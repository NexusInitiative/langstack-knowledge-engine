"""Index a corpus: parse -> chunk -> embed (only what changed) -> upsert.

The idempotency contract (ticket E2-4): running ingestion twice on an
unchanged corpus embeds **nothing** the second time. A chunk is re-embedded
iff its ``content_hash`` or the ``embedding_model`` differs from what is
stored. Metadata-only edits (a tier or tag change in frontmatter) are applied
without re-embedding.

Assumes a single writer: ingestion reads the index state, embeds (slow), then
writes in one transaction. Two concurrent ingests could interleave; the write
path detects a vanished row and aborts rather than silently skipping it, and a
re-run converges. Fine for a CLI/cron job; revisit if ingestion becomes a service.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import psycopg

from lkengine.db import store
from lkengine.db.migrate import apply_schema
from lkengine.embed.base import Embedder
from lkengine.ingest.build import build_chunks
from lkengine.ingest.chunker import DEFAULT_MAX_TOKENS
from lkengine.ingest.parser import parse_corpus
from lkengine.models import Chunk


class EmptyCorpusError(RuntimeError):
    """Parsing produced no chunks. Refusing to continue: pruning "everything
    that is not in the corpus" against an empty corpus would wipe the index."""


@dataclass(frozen=True)
class IngestReport:
    total_chunks: int
    retrievable_chunks: int
    embedded: int        # chunks we paid to embed this run
    unchanged: int       # retrievable chunks skipped because their hash+model matched
    removed: int         # chunks pruned because the corpus no longer has them

    def summary(self) -> str:
        return (
            f"{self.total_chunks} chunks ({self.retrievable_chunks} retrievable): "
            f"embedded {self.embedded}, unchanged {self.unchanged}, removed {self.removed}"
        )


def ingest_corpus(
    conn: psycopg.Connection,
    embedder: Embedder,
    root: str | Path,
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    batch_size: int = 32,
) -> IngestReport:
    apply_schema(conn, dense_dim=embedder.dense_dim, sparse_dim=embedder.sparse_dim)
    chunks, xrefs = build_chunks(parse_corpus(root), max_tokens=max_tokens)
    if not chunks:
        raise EmptyCorpusError(
            f"no sections found under {root}; check the path (nothing was changed)")

    state = store.load_index_state(conn)
    stale = [c for c in chunks if c.is_retrievable and state.get(c.chunk_id) != (c.content_hash, embedder.model_id)]
    embedded = _embed(embedder, stale, batch_size)

    with conn.transaction():
        for chunk in chunks:
            store.upsert_chunk(
                conn, chunk, embedded.get(chunk.chunk_id),
                model_id=embedder.model_id, sparse_dim=embedder.sparse_dim,
            )
        removed = store.delete_missing(conn, {c.chunk_id for c in chunks})
        store.replace_xrefs(conn, xrefs)

    retrievable = sum(c.is_retrievable for c in chunks)
    return IngestReport(
        total_chunks=len(chunks),
        retrievable_chunks=retrievable,
        embedded=len(embedded),
        unchanged=retrievable - len(embedded),
        removed=removed,
    )


def _embed(embedder: Embedder, chunks: list[Chunk], batch_size: int) -> dict:
    out = {}
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        for chunk, emb in zip(batch, embedder.encode([c.content for c in batch])):
            out[chunk.chunk_id] = emb
    return out
