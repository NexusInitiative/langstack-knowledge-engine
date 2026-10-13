"""End-to-end smoke over the *real* shipped corpus and golden set.

Uses the deterministic HashingEmbedder, so the numbers here validate the
plumbing (ingest -> hybrid search -> eval) and guard against regressions - they
are NOT the project's quality baseline. The real BGE-M3 numbers are issue #12.
"""

import pytest

from lkengine.cli import main
from lkengine.embed.hashing import HashingEmbedder
from lkengine.eval.golden import load_golden
from lkengine.eval.harness import evaluate
from lkengine.db.migrate import SchemaMismatchError
from lkengine.ingest.pipeline import ingest_corpus
from lkengine.paths import CORPUS_DIR, GOLDEN_SET_PATH
from lkengine.retrieval.hybrid import HybridRetriever


@pytest.fixture
def indexed(conn):
    emb = HashingEmbedder()
    report = ingest_corpus(conn, emb, CORPUS_DIR)
    return conn, emb, report


def test_real_corpus_ingests_and_reingest_is_a_noop(indexed):
    conn, emb, report = indexed
    assert report.retrievable_chunks > 150 and report.embedded == report.retrievable_chunks
    again = ingest_corpus(conn, emb, CORPUS_DIR)
    assert again.embedded == 0 and again.removed == 0


def test_golden_set_scores_above_smoke_floor(indexed):
    conn, emb, _ = indexed
    retriever = HybridRetriever(conn, emb)
    report = evaluate(
        lambda q: [h.section_id for h in retriever.search(q, top_k=10)],
        load_golden(GOLDEN_SET_PATH),
    )
    agg = report.aggregate()
    assert agg["n"] == 27
    # Floor chosen well under the observed value so this only trips on a real regression.
    assert agg["hit@10"] >= FLOOR_HIT_10, report.format_text()
    assert report.unscored and len(report.unscored) == 3


FLOOR_HIT_10 = 0.7  # observed 0.85 with the fake embedder


def test_query_with_wrong_embedder_geometry_fails_fast(indexed):
    conn, _, _ = indexed
    with pytest.raises(SchemaMismatchError, match="embedder"):
        HybridRetriever(conn, HashingEmbedder(dense_dim=32))


def test_search_before_ingest_explains_what_to_do(conn):
    # Pin the search path to the empty private schema so tables a developer
    # created in `public` by running the CLI cannot leak into this test.
    conn.execute(f"SET search_path TO {conn.execute('SELECT current_schema()').fetchone()[0]}")
    with pytest.raises(SchemaMismatchError, match="ingest"):
        HybridRetriever(conn, HashingEmbedder())
