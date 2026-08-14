#!/usr/bin/env python3
"""
Ingest the LangChain/LangGraph corpus into Postgres + pgvector using BGE-M3.

    pip install FlagEmbedding psycopg[binary] pyyaml
    python ingest.py --corpus ../ --dsn postgresql://user:pass@localhost/ragdb

BGE-M3 gives you dense AND learned-sparse vectors from a single forward pass,
so hybrid retrieval costs one model, not two. It needs no query instruction
prefix (unlike bge-large-en), so queries and documents are encoded identically.
"""

from __future__ import annotations
import argparse, glob, json, os, re, sys
import yaml
import psycopg
from psycopg.rows import dict_row

SECTION_RE = re.compile(r"^## ((?:LC|LG|SH|AC|META)-\d+\.\d+)")
XREF_RE = re.compile(r"`((?:LC|LG|SH|AC|META)-\d+)`")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)

# META-* documents are corpus housekeeping (manifests, source registers).
# They are the only sections that exceed the reranker's 512-token budget and
# they answer no user question. Store them, but exclude from retrieval.
NON_RETRIEVABLE_SERIES = {"META"}


def parse_corpus(root: str) -> tuple[list[dict], list[tuple[str, str]]]:
    chunks, xrefs = [], []
    for path in sorted(glob.glob(os.path.join(root, "**", "*.md"), recursive=True)):
        raw = open(path, encoding="utf-8").read()
        m = FRONTMATTER_RE.match(raw)
        if not m:
            continue  # README.md has no frontmatter — intentionally skipped
        meta, body = yaml.safe_load(m.group(1)), m.group(2)

        for part in re.split(r"\n(?=## )", body):
            heading = part.split("\n", 1)[0].lstrip("# ").strip()
            sid = SECTION_RE.match("## " + heading)
            if not sid:
                continue  # skips H1 block and the trailing "## Sources" footer
            section_id = sid.group(1)
            section_body = part.strip()

            # Prepend the document title. This is the single highest-leverage
            # tweak in the pipeline: it gives the encoder document-level context
            # for a section that may read ambiguously alone.
            content = f"# {meta['title']}\n\n{section_body}"

            chunks.append({
                "section_id": section_id,
                "doc_id": meta["doc_id"],
                "doc_title": meta["title"],
                "heading": heading,
                "content": content,
                "body": section_body,
                "series": meta["series"],
                "product": meta["product"],
                "source_tier": meta.get("source_tier"),
                "recency_class": meta.get("recency_class", "current"),
                "version_scope": meta.get("version_scope"),
                "last_verified": str(meta["last_verified"]),
                "tags": meta.get("tags") or [],
                "source_path": os.path.relpath(path, root),
                "word_count": len(content.split()),
                "has_code": "```" in section_body,
                "is_retrievable": meta["series"] not in NON_RETRIEVABLE_SERIES,
            })
            for ref in set(XREF_RE.findall(section_body)):
                if ref != meta["doc_id"]:
                    xrefs.append((section_id, ref))
    return chunks, xrefs


def to_sparsevec(weights: dict, dim: int) -> str:
    """FlagEmbedding lexical_weights -> pgvector sparsevec literal '{i:v,...}/dim'."""
    items = sorted((int(k), float(v)) for k, v in weights.items() if float(v) > 0)
    if not items:
        return "{}/%d" % dim
    return "{" + ",".join(f"{i}:{v:.6f}" for i, v in items) + "}/%d" % dim


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="..", help="corpus root directory")
    ap.add_argument("--dsn", required=True, help="postgres DSN")
    ap.add_argument("--model", default="BAAI/bge-m3")
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--fp16", action="store_true", default=True)
    args = ap.parse_args()

    chunks, xrefs = parse_corpus(args.corpus)
    print(f"parsed {len(chunks)} sections, {len(xrefs)} cross-references")
    if not chunks:
        print("no sections found — check --corpus path", file=sys.stderr)
        return 1

    from FlagEmbedding import BGEM3FlagModel
    model = BGEM3FlagModel(args.model, use_fp16=args.fp16)
    vocab_size = model.tokenizer.vocab_size
    print(f"model={args.model} vocab={vocab_size}")
    if vocab_size != 250002:
        print(f"  NOTE: schema declares sparsevec(250002); tokenizer says {vocab_size}. "
              f"ALTER the column to sparsevec({vocab_size}) if these differ.")

    print("encoding (dense + sparse, single pass)...")
    out = model.encode(
        [c["content"] for c in chunks],
        batch_size=args.batch_size,
        max_length=8192,          # bge-m3 supports 8192; our max chunk is ~950
        return_dense=True,
        return_sparse=True,
        return_colbert_vecs=False,
    )
    dense_vecs, lexical = out["dense_vecs"], out["lexical_weights"]

    with psycopg.connect(args.dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE corpus_chunks CASCADE")
            for c, dv, lw in zip(chunks, dense_vecs, lexical):
                cur.execute(
                    """
                    INSERT INTO corpus_chunks (
                        section_id, doc_id, doc_title, heading, content, body,
                        series, product, source_tier, recency_class, version_scope,
                        last_verified, tags, source_path, word_count, has_code,
                        is_retrievable, dense, sparse
                    ) VALUES (
                        %(section_id)s, %(doc_id)s, %(doc_title)s, %(heading)s,
                        %(content)s, %(body)s, %(series)s, %(product)s,
                        %(source_tier)s, %(recency_class)s, %(version_scope)s,
                        %(last_verified)s, %(tags)s, %(source_path)s,
                        %(word_count)s, %(has_code)s, %(is_retrievable)s,
                        %(dense)s::vector, %(sparse)s::sparsevec
                    )
                    """,
                    {**c,
                     "dense": "[" + ",".join(f"{x:.6f}" for x in dv) + "]",
                     "sparse": to_sparsevec(lw, vocab_size)},
                )
            cur.executemany(
                "INSERT INTO corpus_xrefs (from_section_id, to_doc_id) "
                "VALUES (%s, %s) ON CONFLICT DO NOTHING",
                xrefs,
            )
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM corpus_chunks")
            total = cur.fetchone()["n"]
            cur.execute("SELECT count(*) AS n FROM corpus_chunks WHERE is_retrievable")
            searchable = cur.fetchone()["n"]
            cur.execute("SELECT max(word_count) AS w FROM corpus_searchable")
            maxw = cur.fetchone()["w"]

    print(f"\ningested {total} chunks ({searchable} retrievable, "
          f"{total - searchable} META excluded)")
    print(f"longest retrievable chunk: {maxw} words "
          f"(~{int(maxw * 1.4)} tok — reranker budget is 512 incl. query)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
