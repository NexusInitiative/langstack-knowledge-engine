from lkengine.embed.hashing import HashingEmbedder
from lkengine.ingest.pipeline import ingest_corpus

from corpus_fixture import write_corpus


def run(conn, root, embedder=None):
    return ingest_corpus(conn, embedder or HashingEmbedder(dense_dim=32), root)


def test_first_run_embeds_retrievable_chunks_and_skips_meta(conn, tmp_path):
    root = write_corpus(tmp_path)
    rep = run(conn, root)
    assert (rep.total_chunks, rep.retrievable_chunks, rep.embedded) == (6, 5, 5)
    meta = conn.execute("SELECT dense IS NULL, is_retrievable FROM corpus_chunks WHERE series='META'").fetchone()
    assert meta == (True, False)
    assert conn.execute("SELECT count(*) FROM corpus_chunks WHERE is_retrievable AND dense IS NULL").fetchone() == (0,)


def test_second_run_on_unchanged_corpus_embeds_nothing(conn, tmp_path):
    root = write_corpus(tmp_path)
    run(conn, root)
    rep = run(conn, root)
    assert rep.embedded == 0 and rep.unchanged == 5 and rep.removed == 0


def test_only_the_changed_chunk_is_reembedded(conn, tmp_path):
    root = write_corpus(tmp_path)
    run(conn, root)
    p = root / "lg/LG-03.md"
    p.write_text(p.read_text().replace("reducer.", "reducer and more words."))
    rep = run(conn, root)
    assert rep.embedded == 1


def test_metadata_only_change_updates_row_without_reembedding(conn, tmp_path):
    root = write_corpus(tmp_path)
    run(conn, root)
    before = conn.execute("SELECT dense::text FROM corpus_chunks WHERE chunk_id='LG-03.1'").fetchone()[0]
    p = root / "lg/LG-03.md"
    p.write_text(p.read_text().replace("source_tier: 1", "source_tier: 2"))
    rep = run(conn, root)
    assert rep.embedded == 0
    tier, after = conn.execute("SELECT source_tier, dense::text FROM corpus_chunks WHERE chunk_id='LG-03.1'").fetchone()
    assert tier == 2 and after == before


def test_changing_embedding_model_reembeds_everything(conn, tmp_path):
    root = write_corpus(tmp_path)
    run(conn, root)

    class V2(HashingEmbedder):
        model_id = "hashing-bow-v2"

    rep = run(conn, root, V2(dense_dim=32))
    assert rep.embedded == 5
    models = {r[0] for r in conn.execute("SELECT embedding_model FROM corpus_chunks WHERE is_retrievable").fetchall()}
    assert models == {"hashing-bow-v2"}


def test_chunks_for_deleted_sections_are_pruned(conn, tmp_path):
    root = write_corpus(tmp_path)
    run(conn, root)
    (root / "lc/LC-04.md").unlink()
    rep = run(conn, root)
    assert rep.removed == 1
    assert conn.execute("SELECT count(*) FROM corpus_chunks WHERE doc_id='LC-04'").fetchone() == (0,)


def test_cross_references_are_recorded(conn, tmp_path):
    run(conn, write_corpus(tmp_path))
    assert conn.execute("SELECT from_section_id, to_doc_id FROM corpus_xrefs").fetchall() == [("LG-04.1", "SH-07")]


def test_empty_or_wrong_corpus_refuses_to_wipe_the_index(conn, tmp_path):
    import pytest
    from lkengine.ingest.pipeline import EmptyCorpusError

    run(conn, write_corpus(tmp_path / "good"))
    (tmp_path / "empty").mkdir()
    with pytest.raises(EmptyCorpusError):
        run(conn, tmp_path / "empty")
    assert conn.execute("SELECT count(*) FROM corpus_chunks").fetchone() == (6,)
