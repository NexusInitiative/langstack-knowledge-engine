"""Core data model (issue E2-1: schema & source registry).

Three layers, each answering a different question:

* ``CorpusDocument`` - *where did this come from?*  One per source file.
  Carries the provenance the corpus frontmatter already records (authority
  tier, version scope, last-verified date) plus the two fields the Phase 1
  fetchers will fill in (``canonical_url``, ``license``).
* ``Section`` - *what is the citable unit?*  A ``## LG-04.3 - ...`` block.
  ``section_id`` is the stable citation anchor the golden set and the answer
  composer cite by.
* ``Chunk`` - *what do we embed and retrieve?*  Usually 1:1 with a section;
  a section that exceeds the token cap becomes several chunks that share the
  same ``section_id`` (so eval and citations still resolve to the section).

Everything here is a frozen dataclass: ingestion is a pure function from files
to these objects, which is what makes it unit-testable without a database.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date

# Series that are corpus housekeeping (manifests, source registers). They are
# stored for provenance but never retrieved: they answer no user question and
# are the only sections that blow the reranker's 512-token budget.
NON_RETRIEVABLE_SERIES = frozenset({"META"})


@dataclass(frozen=True)
class CorpusDocument:
    doc_id: str                      # 'LG-04'
    title: str
    series: str                      # LC | LG | SH | AC | META
    product: str                     # LangChain | LangGraph | both
    last_verified: date
    source_path: str                 # relative to the corpus root
    source_tier: int | None = None   # 1 primary, 2 corroborated, 3 single-source
    recency_class: str = "current"   # current | foundational
    version_scope: str | None = None
    tags: tuple[str, ...] = ()
    canonical_url: str | None = None  # populated by Phase 1 fetchers (#5, #13)
    license: str | None = None        # populated by Phase 1 fetchers (#5, #13)

    @property
    def is_retrievable(self) -> bool:
        return self.series not in NON_RETRIEVABLE_SERIES


@dataclass(frozen=True)
class Section:
    section_id: str                  # 'LG-04.3'
    heading: str                     # 'LG-04.3 - Threads and thread_id'
    body: str                        # heading line + prose, as written
    xref_doc_ids: tuple[str, ...] = ()  # `LG-04`-style references, sorted, no self


@dataclass(frozen=True)
class Chunk:
    chunk_id: str                    # section_id for part 1, 'section_id~N' after
    section_id: str
    part: int                        # 1-based
    doc: CorpusDocument
    heading: str
    body: str                        # what we show the user
    content: str                     # what we embed: '# <doc title>\n\n<body>'
    content_hash: str                # sha256(content) - the idempotency key
    word_count: int
    has_code: bool
    is_retrievable: bool


def chunk_id_for(section_id: str, part: int) -> str:
    """Stable chunk identity.

    Part 1 keeps the bare section id, so the common case (an unsplit section)
    has the same id as its citation anchor, and a section that later grows
    past the cap keeps its original id for its first part.
    """
    return section_id if part == 1 else f"{section_id}~{part}"


def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
