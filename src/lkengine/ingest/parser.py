"""Parse corpus markdown files into ``CorpusDocument`` + ``Section`` objects.

File format (see ``corpus/_meta/INDEX.md``)::

    ---
    doc_id: LG-04
    title: ...
    series: LG
    ...
    ---
    # LG-04 - H1 title            <- preamble, not a section
    ## LG-04.1 - First section    <- a citable section
    ...
    ## Sources                    <- footer, not a section

The one subtlety: a ``## ...`` line inside a fenced code block (a shell or
Python comment, say) is *not* a heading. A naive ``re.split(r"\\n(?=## )")``
would cut the section there, so splitting walks the lines and tracks fence
state.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

import yaml

from lkengine.models import CorpusDocument, Section

SECTION_HEADING_RE = re.compile(r"^## ((?:LC|LG|SH|AC|META)-\d+\.\d+)\b")
XREF_RE = re.compile(r"`((?:LC|LG|SH|AC|META)-\d+)`")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.S)
FENCE_RE = re.compile(r"^\s*(```|~~~)")

_REQUIRED = ("doc_id", "title", "series", "product", "last_verified")


class CorpusParseError(ValueError):
    """A corpus file has frontmatter but it is malformed or incomplete."""


def parse_corpus(root: str | Path) -> list[tuple[CorpusDocument, list[Section]]]:
    """Parse every ``*.md`` under ``root``, in path order (deterministic)."""
    root = Path(root)
    parsed = []
    for path in sorted(root.rglob("*.md")):
        result = parse_document(path, root=root)
        if result is not None:
            parsed.append(result)
    return parsed


def parse_document(
    path: str | Path, *, root: str | Path
) -> tuple[CorpusDocument, list[Section]] | None:
    """Parse one file. Returns ``None`` for files without frontmatter
    (READMEs are intentionally not part of the corpus)."""
    path, root = Path(path), Path(root)
    raw = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(raw)
    if not m:
        return None

    meta = yaml.safe_load(m.group(1)) or {}
    missing = [k for k in _REQUIRED if k not in meta]
    if missing:
        raise CorpusParseError(f"{path}: missing frontmatter key(s): {', '.join(missing)}")

    doc = CorpusDocument(
        doc_id=meta["doc_id"],
        title=meta["title"],
        series=meta["series"],
        product=meta["product"],
        last_verified=_as_date(meta["last_verified"], path),
        source_path=path.relative_to(root).as_posix(),
        source_tier=meta.get("source_tier"),
        recency_class=meta.get("recency_class", "current"),
        version_scope=meta.get("version_scope"),
        tags=tuple(meta.get("tags") or ()),
        canonical_url=meta.get("canonical_url"),
        license=meta.get("license"),
    )
    return doc, split_sections(m.group(2), doc_id=doc.doc_id)


def split_sections(markdown: str, *, doc_id: str) -> list[Section]:
    """Split a document body into sections; fence-aware (see module docstring)."""
    blocks: list[list[str]] = []
    in_fence = False
    current: list[str] | None = None

    for line in markdown.split("\n"):
        if FENCE_RE.match(line):
            in_fence = not in_fence
        starts_section = not in_fence and SECTION_HEADING_RE.match(line)
        starts_other_h2 = not in_fence and line.startswith("## ") and not starts_section
        if starts_section:
            current = [line]
            blocks.append(current)
        elif starts_other_h2:
            current = None  # e.g. '## Sources' footer: stop collecting
        elif current is not None:
            current.append(line)

    sections = []
    for lines in blocks:
        body = "\n".join(lines).strip()
        heading_line = lines[0]
        section_id = SECTION_HEADING_RE.match(heading_line).group(1)
        refs = sorted({r for r in XREF_RE.findall(body) if r != doc_id})
        sections.append(
            Section(
                section_id=section_id,
                heading=heading_line.removeprefix("## ").strip(),
                body=body,
                xref_doc_ids=tuple(refs),
            )
        )
    return sections


def _as_date(value, path: Path) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as e:
        raise CorpusParseError(f"{path}: last_verified is not an ISO date: {value!r}") from e
