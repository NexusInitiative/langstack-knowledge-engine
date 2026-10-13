"""Turn parsed documents into embeddable ``Chunk`` objects.

This is the seam between *parsing* (files -> sections) and *indexing*
(chunks -> Postgres). It is a pure function, so the whole front half of the
pipeline is testable with nothing but a temp directory.
"""

from __future__ import annotations

from collections.abc import Iterable

from lkengine.ingest.chunker import DEFAULT_MAX_TOKENS, split_section_body
from lkengine.models import Chunk, CorpusDocument, Section, chunk_id_for, hash_content


def build_chunks(
    parsed: Iterable[tuple[CorpusDocument, list[Section]]],
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> tuple[list[Chunk], list[tuple[str, str]]]:
    """Return ``(chunks, xrefs)``; ``xrefs`` are ``(from_section_id, to_doc_id)``.

    ``content`` (what gets embedded) is the body prefixed with the document
    title. A section like "Reducers" can read ambiguously alone; the title
    gives the encoder document-level context for free. This is the cheap,
    deterministic cousin of LLM-written "contextual chunk prefixes" (spike
    #21 measures whether the expensive version is worth it).
    """
    chunks: list[Chunk] = []
    xrefs: list[tuple[str, str]] = []
    for doc, sections in parsed:
        for section in sections:
            for part, body in enumerate(split_section_body(section.body, max_tokens=max_tokens), 1):
                content = f"# {doc.title}\n\n{body}"
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id_for(section.section_id, part),
                        section_id=section.section_id,
                        part=part,
                        doc=doc,
                        heading=section.heading,
                        body=body,
                        content=content,
                        content_hash=hash_content(content),
                        word_count=len(content.split()),
                        has_code="```" in body,
                        is_retrievable=doc.is_retrievable,
                    )
                )
            xrefs.extend((section.section_id, ref) for ref in section.xref_doc_ids)
    return chunks, xrefs
