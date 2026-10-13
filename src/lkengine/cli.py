"""Command-line interface: ``uv run lkengine <command>`` (partial ticket E3-3).

    lkengine db init|reset [--ann]    create / drop the schema
    lkengine ingest                   parse, chunk, embed (changed only), index
    lkengine search "query"           hybrid retrieval, prints cited results
    lkengine eval                     Recall@k / MRR against the golden set

Every command takes ``--embedder bge|hash`` (after the command name, e.g.
``lkengine ingest --embedder hash``). ``hash`` is a dependency-free
fake for smoke runs; the index and the queries must use the same embedder
(checked, with a clear error). ``DATABASE_URL`` comes from the environment or
``.env`` (see ``.env.example``).

Retrieval only for now: the grounded answer composer (#9) and the
end-to-end ``ask`` command that wraps it are the next slice.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence

from lkengine.db.connection import get_connection
from lkengine.db.migrate import SchemaMismatchError, apply_schema, create_ann_index, reset_schema
from lkengine.embed import EMBEDDER_NAMES, EmbedderUnavailable, make_embedder
from lkengine.eval.golden import load_golden
from lkengine.eval.harness import DEFAULT_KS, evaluate
from lkengine.ingest.pipeline import EmptyCorpusError, ingest_corpus
from lkengine.paths import CORPUS_DIR, GOLDEN_SET_PATH
from lkengine.retrieval.hybrid import HybridRetriever, SearchFilters


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="lkengine", description=__doc__.split("\n\n")[0])
    # Defined once and inherited by every subcommand (argparse only accepts an
    # option where its parser is active, so a top-level flag would have to
    # precede the command name).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--embedder", choices=EMBEDDER_NAMES,
                        default=os.environ.get("LKENGINE_EMBEDDER", "bge"),
                        help="embedding model (default: bge; env LKENGINE_EMBEDDER)")
    sub = p.add_subparsers(dest="command", required=True)

    db = sub.add_parser("db", parents=[common], help="schema management")
    db.add_argument("action", choices=["init", "reset"])
    db.add_argument("--ann", action="store_true", help="init: also create the opt-in HNSW index")

    ing = sub.add_parser("ingest", parents=[common], help="index the corpus (idempotent)")
    ing.add_argument("--corpus", default=str(CORPUS_DIR))
    ing.add_argument("--batch-size", type=int, default=32)

    s = sub.add_parser("search", parents=[common], help="hybrid retrieval")
    s.add_argument("query")
    s.add_argument("--product", nargs="*", help="LangChain LangGraph both")
    s.add_argument("--series", nargs="*", help="LC LG SH AC")
    s.add_argument("--max-tier", type=int, choices=[1, 2, 3], help="1 = primary sources only")
    s.add_argument("--top-k", type=int, default=6)
    s.add_argument("--pool", type=int, default=40, help="candidates per channel before fusion")
    s.add_argument("--expand", action="store_true", help="also show cross-referenced overviews")
    s.add_argument("--json", action="store_true")

    e = sub.add_parser("eval", parents=[common], help="score retrieval against the golden set")
    e.add_argument("--golden", default=str(GOLDEN_SET_PATH))
    e.add_argument("--ks", type=int, nargs="+", default=list(DEFAULT_KS))
    e.add_argument("--json", action="store_true")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _COMMANDS[args.command](args)
    except (SchemaMismatchError, EmbedderUnavailable, EmptyCorpusError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


def _cmd_db(args) -> int:
    embedder = make_embedder(args.embedder)
    with get_connection() as conn:
        if args.action == "reset":
            reset_schema(conn)
            print("dropped lkengine tables")
        else:
            apply_schema(conn, dense_dim=embedder.dense_dim, sparse_dim=embedder.sparse_dim)
            if args.ann:
                create_ann_index(conn)
            print("schema ready")
    return 0


def _cmd_ingest(args) -> int:
    embedder = make_embedder(args.embedder)
    with get_connection() as conn:
        report = ingest_corpus(conn, embedder, args.corpus, batch_size=args.batch_size)
    print(report.summary())
    return 0


def _cmd_search(args) -> int:
    embedder = make_embedder(args.embedder)
    filters = SearchFilters(product=args.product, series=args.series, max_tier=args.max_tier)
    with get_connection() as conn:
        retriever = HybridRetriever(conn, embedder, pool=args.pool)
        hits = retriever.search(args.query, filters=filters, top_k=args.top_k)
        extra = retriever.expand_xrefs(hits) if args.expand else []

    if args.json:
        dump = lambda h: {**h.__dict__, "last_verified": str(h.last_verified)}
        print(json.dumps({"results": [dump(h) for h in hits],
                          "xref_context": [dump(h) for h in extra]}, indent=2))
        return 0
    for i, h in enumerate(hits, 1):
        tier = f"T{h.source_tier}" if h.source_tier else "T?"
        print(f"\n{i}. [{h.section_id}] {h.heading}")
        print(f"   {h.doc_title} · {h.product} · {tier} · verified {h.last_verified}"
              f" · score {h.score:.4f} · channels {h.channel_ranks}")
        if h.version_scope:
            print(f"   scope: {h.version_scope}")
        text = h.body.split("\n", 1)[1].strip() if "\n" in h.body else h.body
        print(f"   {text[:300].replace(chr(10), ' ')}...")
    if extra:
        print("\n--- cross-referenced context ---")
        for h in extra:
            print(f"   [{h.section_id}] {h.heading}")
    if not hits:
        print("no results")
    return 0


def _cmd_eval(args) -> int:
    embedder = make_embedder(args.embedder)
    questions = load_golden(args.golden)
    depth = max(args.ks)
    with get_connection() as conn:
        retriever = HybridRetriever(conn, embedder)
        # Over-fetch: a long section can occupy several chunk slots, and the
        # harness scores unique *sections*, so `depth` chunks may be < `depth` sections.
        report = evaluate(
            lambda q: [h.section_id for h in retriever.search(q, top_k=depth * 3)],
            questions, ks=args.ks,
        )
    print(report.to_json() if args.json else report.format_text())
    return 0


_COMMANDS = {"db": _cmd_db, "ingest": _cmd_ingest, "search": _cmd_search, "eval": _cmd_eval}

if __name__ == "__main__":
    raise SystemExit(main())
