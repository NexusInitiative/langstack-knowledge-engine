import pytest

from lkengine.embed.hashing import HashingEmbedder
from lkengine.ingest.pipeline import ingest_corpus
from lkengine.retrieval.hybrid import HybridRetriever, SearchFilters

from corpus_fixture import write_corpus


@pytest.fixture
def retriever(conn, tmp_path):
    emb = HashingEmbedder(dense_dim=64)
    ingest_corpus(conn, emb, write_corpus(tmp_path))
    return HybridRetriever(conn, emb, pool=10)


def ids(hits):
    return [h.section_id for h in hits]


def test_exact_identifier_query_ranks_the_defining_section_first(retriever):
    assert ids(retriever.search("InvalidUpdateError"))[0] in {"LG-03.1", "SH-07.1"}


def test_paraphrase_without_the_literal_still_finds_it_via_subtokens(retriever):
    assert "LG-03.1" in ids(retriever.search("concurrent writes need a reducer", top_k=3))


def test_hits_carry_provenance_and_channel_ranks(retriever):
    (top, *_) = retriever.search("checkpointer thread_id")
    assert top.section_id == "LG-04.1"
    assert top.doc_title == "LangGraph Persistence" and top.source_tier == 1
    assert top.last_verified.isoformat() == "2026-08-13"
    assert set(top.channel_ranks) <= {"dense", "sparse", "fts"} and top.channel_ranks
    assert top.score > 0


def test_results_are_sorted_by_descending_score(retriever):
    scores = [h.score for h in retriever.search("reducer checkpointer error", top_k=5)]
    assert scores == sorted(scores, reverse=True)


def test_meta_housekeeping_is_never_retrieved(retriever):
    assert all(h.series != "META" for h in retriever.search("source register checkpointer reducer", top_k=10))


def test_product_filter_excludes_other_products(retriever):
    hits = retriever.search("structured output reducer checkpointer", filters=SearchFilters(product=["LangChain"]), top_k=10)
    assert hits and {h.product for h in hits} == {"LangChain"}


def test_series_and_tier_filters(retriever):
    assert {h.series for h in retriever.search("error reducer", filters=SearchFilters(series=["SH"]), top_k=10)} == {"SH"}
    tiers = {h.source_tier for h in retriever.search("error reducer output", filters=SearchFilters(max_tier=1), top_k=10)}
    assert tiers and tiers <= {1}


def test_no_overlap_query_returns_nothing_from_sparse_or_fts(retriever):
    # dense still ranks everything, but a token-less query must not crash
    assert retriever.search("   ") == []
    assert retriever.search("the of and") is not None  # all stopwords: no vectors, no crash


def test_top_k_limits_results(retriever):
    assert len(retriever.search("graph state thread", top_k=2)) == 2


def test_xref_expansion_pulls_overview_of_cited_document(retriever):
    hits = retriever.search("AsyncPostgresSaver production", top_k=1)
    assert ids(hits) == ["LG-04.1"]
    assert ids(retriever.expand_xrefs(hits)) == ["SH-07.1"]
    assert retriever.expand_xrefs([]) == []


def test_bare_string_filter_is_treated_as_one_value_not_characters(retriever):
    hits = retriever.search("structured output", filters=SearchFilters(product="LangChain"), top_k=5)
    assert hits and {h.product for h in hits} == {"LangChain"}


def test_xref_expansion_is_ordered_by_citing_hit_rank(conn, tmp_path):
    from corpus_fixture import doc
    root = tmp_path
    (root / "a.md").write_text(doc("LG-10", "A", "LG", "both", 1, [("LG-10.1", "x", "alpha `SH-07` `LG-04` `LC-04`.")]))
    (root / "b.md").write_text(doc("SH-07", "B", "SH", "both", 1, [("SH-07.1", "x", "ov b")]))
    (root / "c.md").write_text(doc("LG-04", "C", "LG", "both", 1, [("LG-04.1", "x", "ov c")]))
    (root / "d.md").write_text(doc("LC-04", "D", "LC", "both", 1, [("LC-04.1", "x", "ov d")]))
    emb = HashingEmbedder(dense_dim=64)
    ingest_corpus(conn, emb, root)
    r = HybridRetriever(conn, emb)
    hits = r.search("alpha", top_k=1)
    assert ids(hits) == ["LG-10.1"]
    assert len(r.expand_xrefs(hits, limit=2)) == 2  # limit respected across three citations


def test_dense_query_keeps_the_pure_distance_ordering_so_hnsw_can_be_used(conn, tmp_path):
    from lkengine.db.migrate import create_ann_index
    emb = HashingEmbedder(dense_dim=64)
    ingest_corpus(conn, emb, write_corpus(tmp_path))
    create_ann_index(conn)
    conn.execute("SET enable_seqscan = off")
    plan = "\n".join(r[0] for r in conn.execute(
        "EXPLAIN SELECT chunk_id FROM corpus_chunks "
        "ORDER BY dense <=> %s::vector LIMIT 5", ("[" + ",".join(["0.1"] * 64) + "]",)).fetchall())
    assert "idx_chunks_dense_hnsw" in plan
    from lkengine.retrieval.hybrid import _CHANNEL_SQL
    assert "chunk_id LIMIT" not in _CHANNEL_SQL["dense"].split("ORDER BY")[1]
