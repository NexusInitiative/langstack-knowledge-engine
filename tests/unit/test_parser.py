"""Corpus parsing: frontmatter, fence-aware section splitting, cross-references."""

from datetime import date
from pathlib import Path

import pytest

from lkengine.ingest.parser import parse_document, parse_corpus, CorpusParseError

DOC = """---
doc_id: LG-99
title: Test Document
series: LG
product: LangGraph
version_scope: langgraph 1.x
last_verified: 2026-08-13
source_tier: 1
tags: [alpha, beta]
---

# LG-99 — Test Document

Intro prose that belongs to no section.

## LG-99.1 — First section

Body of the first section. See `LG-04` and `SH-07` for more, and `LG-99` itself.

## LG-99.2 — Section with a fenced block

Lead-in:

```python
## this looks like a heading but lives inside a fence
x = 1
```

Trailing prose.

## Sources

- not a section
"""


def write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_parses_frontmatter_into_typed_document(tmp_path):
    doc, _ = parse_document(write(tmp_path, "d.md", DOC), root=tmp_path)
    assert doc.doc_id == "LG-99"
    assert doc.title == "Test Document"
    assert doc.series == "LG"
    assert doc.product == "LangGraph"
    assert doc.source_tier == 1
    assert doc.version_scope == "langgraph 1.x"
    assert doc.last_verified == date(2026, 8, 13)
    assert doc.tags == ("alpha", "beta")
    assert doc.source_path == "d.md"


def test_splits_on_section_headings_and_drops_preamble_and_sources(tmp_path):
    _, sections = parse_document(write(tmp_path, "d.md", DOC), root=tmp_path)
    assert [s.section_id for s in sections] == ["LG-99.1", "LG-99.2"]
    assert sections[0].heading == "LG-99.1 — First section"
    assert "Intro prose" not in sections[0].body
    assert "not a section" not in sections[1].body


def test_heading_lookalikes_inside_code_fences_do_not_split(tmp_path):
    _, sections = parse_document(write(tmp_path, "d.md", DOC), root=tmp_path)
    assert len(sections) == 2
    assert "## this looks like a heading" in sections[1].body


def test_extracts_cross_references_excluding_self(tmp_path):
    _, sections = parse_document(write(tmp_path, "d.md", DOC), root=tmp_path)
    assert sections[0].xref_doc_ids == ("LG-04", "SH-07")  # sorted, no LG-99


def test_file_without_frontmatter_is_skipped(tmp_path):
    assert parse_document(write(tmp_path, "README.md", "# just a readme\n"), root=tmp_path) is None


def test_missing_required_frontmatter_key_raises(tmp_path):
    bad = DOC.replace("doc_id: LG-99\n", "")
    with pytest.raises(CorpusParseError, match="doc_id"):
        parse_document(write(tmp_path, "d.md", bad), root=tmp_path)


def test_parse_corpus_walks_recursively_and_orders_deterministically(tmp_path):
    (tmp_path / "sub").mkdir()
    write(tmp_path / "sub", "b.md", DOC.replace("LG-99", "LG-98"))
    write(tmp_path, "a.md", DOC)
    write(tmp_path, "README.md", "# no frontmatter\n")
    docs = parse_corpus(tmp_path)
    assert [d.doc_id for d, _ in docs] == ["LG-99", "LG-98"]  # sorted by path: a.md < sub/b.md
