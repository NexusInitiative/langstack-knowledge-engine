#!/usr/bin/env python3
"""
Hybrid retrieval over the corpus: BGE-M3 dense + sparse, fused with RRF,
then reranked with bge-reranker-v2-m3.

    pip install FlagEmbedding psycopg[binary]
    python search.py --dsn postgresql://... "why does my graph hang?"

IMPORTANT — two different models:
  BAAI/bge-m3             bi-encoder, produces vectors, 8192 tok  -> retrieval
  BAAI/bge-reranker-v2-m3 cross-encoder, produces a score, 512 tok -> reranking
The reranker does not embed anything. It reads (query, passage) together and
emits a relevance score directly, which is why it is more accurate and far
too slow to run over the whole corpus. Retrieve wide, rerank narrow.
"""

from __future__ import annotations
import argparse, json
import psycopg
from psycopg.rows import dict_row

RRF_K = 60  # standard Reciprocal Rank Fusion constant


def to_sparsevec(weights: dict, dim: int) -> str:
    items = sorted((int(k), float(v)) for k, v in weights.items() if float(v) > 0)
    return ("{" + ",".join(f"{i}:{v:.6f}" for i, v in items) + "}/%d" % dim
            if items else "{}/%d" % dim)


HYBRID_SQL = """
WITH filtered AS (
    SELECT * FROM corpus_chunks
    WHERE is_retrievable
      AND (%(product)s IS NULL OR product = ANY(%(product)s))
      AND (%(series)s  IS NULL OR series  = ANY(%(series)s))
      AND (%(max_tier)s IS NULL OR source_tier <= %(max_tier)s)
),
dense_r AS (
    SELECT section_id,
           ROW_NUMBER() OVER (ORDER BY dense <=> %(qdense)s::vector) AS rank
    FROM filtered
    ORDER BY dense <=> %(qdense)s::vector
    LIMIT %(pool)s
),
sparse_r AS (
    SELECT section_id,
           ROW_NUMBER() OVER (ORDER BY sparse <#> %(qsparse)s::sparsevec) AS rank
    FROM filtered
    ORDER BY sparse <#> %(qsparse)s::sparsevec
    LIMIT %(pool)s
),
fts_r AS (
    SELECT section_id,
           ROW_NUMBER() OVER (
               ORDER BY ts_rank_cd(fts, websearch_to_tsquery('english', %(q)s)) DESC
           ) AS rank
    FROM filtered
    WHERE fts @@ websearch_to_tsquery('english', %(q)s)
    LIMIT %(pool)s
),
fused AS (
    SELECT section_id, SUM(w) AS rrf FROM (
        SELECT section_id, 1.0 / (%(k)s + rank) * 1.0 FROM dense_r
        UNION ALL
        SELECT section_id, 1.0 / (%(k)s + rank) * 1.0 FROM sparse_r
        UNION ALL
        SELECT section_id, 1.0 / (%(k)s + rank) * 0.5 FROM fts_r
    ) s(section_id, w)
    GROUP BY section_id
)
SELECT c.section_id, c.doc_id, c.doc_title, c.heading, c.body, c.content,
       c.product, c.series, c.source_tier, c.recency_class,
       c.version_scope, c.last_verified, c.tags, c.word_count, c.has_code,
       f.rrf
FROM fused f JOIN corpus_chunks c USING (section_id)
ORDER BY f.rrf DESC
LIMIT %(pool)s;
"""


def retrieve(conn, q, qdense, qsparse, *, product=None, series=None,
             max_tier=None, pool=40):
    with conn.cursor() as cur:
        cur.execute(HYBRID_SQL, {
            "q": q, "qdense": qdense, "qsparse": qsparse,
            "product": product, "series": series, "max_tier": max_tier,
            "pool": pool, "k": RRF_K,
        })
        return cur.fetchall()


def expand_xrefs(conn, rows, limit=3):
    """Pull section .1 of documents the top hits explicitly reference.

    The corpus uses explicit `LG-04` IDs rather than 'as described above',
    which makes this expansion mechanical and high-precision.
    """
    if not rows:
        return []
    top = [r["section_id"] for r in rows[:3]]
    have = {r["doc_id"] for r in rows}
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT c.* FROM corpus_xrefs x
            JOIN corpus_chunks c ON c.doc_id = x.to_doc_id
                                AND c.section_id LIKE x.to_doc_id || '.1'
            WHERE x.from_section_id = ANY(%s)
              AND c.is_retrievable
              AND NOT (c.doc_id = ANY(%s))
            LIMIT %s
            """,
            (top, list(have), limit),
        )
        return cur.fetchall()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--dsn", required=True)
    ap.add_argument("--product", nargs="*", help="LangChain LangGraph both")
    ap.add_argument("--series", nargs="*", help="LC LG SH AC")
    ap.add_argument("--max-tier", type=int, help="1 = primary sources only")
    ap.add_argument("--pool", type=int, default=40, help="candidates before rerank")
    ap.add_argument("--top-k", type=int, default=6, help="results after rerank")
    ap.add_argument("--no-rerank", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    from FlagEmbedding import BGEM3FlagModel
    embedder = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)
    vocab = embedder.tokenizer.vocab_size

    # No instruction prefix: bge-m3 encodes queries and documents identically.
    enc = embedder.encode([args.query], return_dense=True, return_sparse=True)
    qdense = "[" + ",".join(f"{x:.6f}" for x in enc["dense_vecs"][0]) + "]"
    qsparse = to_sparsevec(enc["lexical_weights"][0], vocab)

    with psycopg.connect(args.dsn, row_factory=dict_row) as conn:
        rows = retrieve(conn, args.query, qdense, qsparse,
                        product=args.product, series=args.series,
                        max_tier=args.max_tier, pool=args.pool)

        if not args.no_rerank and rows:
            from FlagEmbedding import FlagReranker
            reranker = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=True)
            # normalize=True applies a sigmoid -> scores in [0,1]
            scores = reranker.compute_score(
                [[args.query, r["content"]] for r in rows],
                normalize=True,
            )
            if isinstance(scores, float):
                scores = [scores]
            for r, s in zip(rows, scores):
                r["score"] = float(s)
            rows.sort(key=lambda r: r["score"], reverse=True)
        else:
            for r in rows:
                r["score"] = float(r["rrf"])

        rows = rows[: args.top_k]
        extra = expand_xrefs(conn, rows)

    if args.json:
        print(json.dumps({"results": rows, "xref_context": extra},
                         default=str, indent=2))
        return 0

    for i, r in enumerate(rows, 1):
        tier = f"T{r['source_tier']}" if r["source_tier"] else "T?"
        print(f"\n{i}. [{r['section_id']}] {r['heading']}")
        print(f"   {r['doc_title']}  ·  {r['product']}  ·  {tier}"
              f"  ·  verified {r['last_verified']}  ·  score {r['score']:.4f}")
        if r["version_scope"]:
            print(f"   scope: {r['version_scope']}")
        body = r["body"].split("\n", 1)[1].strip() if "\n" in r["body"] else r["body"]
        print(f"   {body[:300].replace(chr(10), ' ')}...")

    if extra:
        print("\n--- cross-referenced context ---")
        for r in extra:
            print(f"   [{r['section_id']}] {r['heading']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
