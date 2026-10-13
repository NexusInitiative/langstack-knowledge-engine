"""Persistence for chunks: read current state, upsert, prune.

Kept separate from the pipeline so the SQL is in one reviewable place.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable

import psycopg

from lkengine.db.vectors import dense_literal, sparse_literal
from lkengine.embed.base import Embedding
from lkengine.models import Chunk

# chunk_id -> (content_hash, embedding_model or None)
IndexState = dict[str, tuple[str, str | None]]

# Columns that describe a chunk but are not vectors. Shared by the INSERT path
# and the metadata-only UPDATE path so the two can never drift apart.
_META_COLS = (
    "section_id", "part", "doc_id", "doc_title", "heading", "content", "body",
    "content_hash", "series", "product", "source_tier", "recency_class",
    "version_scope", "last_verified", "tags", "source_path", "canonical_url",
    "license", "word_count", "has_code", "is_retrievable",
)
_VECTOR_COLS = ("embedding_model", "dense", "sparse")
_PLACEHOLDER = {"dense": "%(dense)s::vector", "sparse": "%(sparse)s::sparsevec"}


def _ph(col: str) -> str:
    return _PLACEHOLDER.get(col, f"%({col})s")


# New or re-embedded row (or a non-retrievable row, whose vectors are NULL).
_UPSERT = (
    f"INSERT INTO corpus_chunks (chunk_id, {', '.join(_META_COLS + _VECTOR_COLS)}) "
    f"VALUES (%(chunk_id)s, {', '.join(_ph(c) for c in _META_COLS + _VECTOR_COLS)}) "
    "ON CONFLICT (chunk_id) DO UPDATE SET "
    + ", ".join(f"{c} = EXCLUDED.{c}" for c in _META_COLS + _VECTOR_COLS)
    + ", updated_at = now()"
)

# Unchanged retrievable row: refresh metadata, leave the stored vectors alone.
# This cannot be an upsert with NULL vectors: Postgres validates CHECK
# constraints on the *proposed* tuple before ON CONFLICT resolves, so a
# NULL-vector insert would trip `retrievable_rows_are_embedded`.
_REFRESH = (
    "UPDATE corpus_chunks SET "
    + ", ".join(f"{c} = {_ph(c)}" for c in _META_COLS)
    + ", updated_at = now() WHERE chunk_id = %(chunk_id)s"
)


def load_index_state(conn: psycopg.Connection) -> IndexState:
    rows = conn.execute("SELECT chunk_id, content_hash, embedding_model FROM corpus_chunks")
    return {cid: (h, m) for cid, h, m in rows.fetchall()}


def upsert_chunk(
    conn: psycopg.Connection,
    chunk: Chunk,
    embedding: Embedding | None,
    *,
    model_id: str | None,
    sparse_dim: int,
) -> None:
    """Write one chunk.

    * with an ``embedding`` (new / changed content): upsert row and vectors;
    * ``embedding=None`` on a retrievable chunk: the stored vectors are still
      valid, so only metadata is refreshed (the row must already exist);
    * ``embedding=None`` on a non-retrievable chunk: upsert with NULL vectors.
    """
    d = chunk.doc
    refresh_only = embedding is None and chunk.is_retrievable
    cur = conn.execute(
        _REFRESH if refresh_only else _UPSERT,
        {
            "chunk_id": chunk.chunk_id, "section_id": chunk.section_id, "part": chunk.part,
            "doc_id": d.doc_id, "doc_title": d.title, "heading": chunk.heading,
            "content": chunk.content, "body": chunk.body, "content_hash": chunk.content_hash,
            "series": d.series, "product": d.product, "source_tier": d.source_tier,
            "recency_class": d.recency_class, "version_scope": d.version_scope,
            "last_verified": d.last_verified, "tags": list(d.tags),
            "source_path": d.source_path, "canonical_url": d.canonical_url,
            "license": d.license, "word_count": chunk.word_count, "has_code": chunk.has_code,
            "is_retrievable": chunk.is_retrievable,
            "embedding_model": model_id if embedding else None,
            "dense": dense_literal(embedding.dense) if embedding else None,
            "sparse": sparse_literal(embedding.sparse, sparse_dim) if embedding else None,
        },
    )
    if refresh_only and cur.rowcount != 1:
        raise RuntimeError(
            f"chunk {chunk.chunk_id} vanished during ingest (concurrent writer?); re-run ingest")


def delete_missing(conn: psycopg.Connection, keep_ids: Collection[str]) -> int:
    """Hard-delete chunks no longer produced by the corpus; returns the count.

    Simple pruning so a removed section cannot linger in retrieval. Soft
    tombstones and per-source incremental sync are issue #23.
    """
    cur = conn.execute(
        "DELETE FROM corpus_chunks WHERE NOT (chunk_id = ANY(%s))", (list(keep_ids),)
    )
    return cur.rowcount


def replace_xrefs(conn: psycopg.Connection, xrefs: Iterable[tuple[str, str]]) -> None:
    conn.execute("DELETE FROM corpus_xrefs")
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO corpus_xrefs (from_section_id, to_doc_id) VALUES (%s, %s) "
            "ON CONFLICT DO NOTHING",
            list(xrefs),
        )
