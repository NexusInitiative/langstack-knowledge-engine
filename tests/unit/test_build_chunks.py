"""Section -> Chunk assembly, including the real corpus as a regression fixture."""

from lkengine.ingest.build import build_chunks
from lkengine.ingest.parser import parse_corpus
from lkengine.models import hash_content
from lkengine.paths import CORPUS_DIR


def test_content_is_doc_title_plus_body_and_hash_matches(tmp_path):
    (tmp_path / "d.md").write_text(
        "---\ndoc_id: LG-99\ntitle: T\nseries: LG\nproduct: LangGraph\n"
        "last_verified: 2026-08-13\n---\n\n## LG-99.1 — One\n\nBody `LG-04`.\n"
    )
    chunks, xrefs = build_chunks(parse_corpus(tmp_path))
    (c,) = chunks
    assert c.chunk_id == "LG-99.1" and c.part == 1
    assert c.content == "# T\n\n" + c.body
    assert c.content_hash == hash_content(c.content)
    assert c.is_retrievable and not c.has_code
    assert xrefs == [("LG-99.1", "LG-04")]


def test_meta_series_is_stored_but_not_retrievable(tmp_path):
    (tmp_path / "m.md").write_text(
        "---\ndoc_id: META-99\ntitle: M\nseries: META\nproduct: both\n"
        "last_verified: 2026-08-13\n---\n\n## META-99.1 — x\n\nbody\n"
    )
    (c,), _ = build_chunks(parse_corpus(tmp_path))
    assert not c.is_retrievable


def test_real_corpus_invariants():
    chunks, _ = build_chunks(parse_corpus(CORPUS_DIR))
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)), "chunk ids must be unique"
    sections = {c.section_id for c in chunks}
    assert len(sections) >= 200  # corpus README documents 220
    retrievable = [c for c in chunks if c.is_retrievable]
    assert 0 < len(retrievable) < len(chunks)
    assert all(c.doc.series != "META" for c in retrievable)
    # reproducible: same input -> same hashes
    again, _ = build_chunks(parse_corpus(CORPUS_DIR))
    assert [c.content_hash for c in chunks] == [c.content_hash for c in again]
