"""Schema management: idempotent apply, dimension guard, optional ANN index."""

from __future__ import annotations

import psycopg

from lkengine.paths import SCHEMA_PATH


class SchemaMismatchError(RuntimeError):
    """The database was initialised for a different embedding geometry."""


def apply_schema(conn: psycopg.Connection, *, dense_dim: int, sparse_dim: int) -> None:
    """Create tables/indexes if missing. Safe to run repeatedly.

    Vector dimensions are baked into the column types, so switching embedding
    models with a different geometry needs a rebuild. Rather than let Postgres
    fail confusingly mid-ingest, the first apply records the dimensions in
    ``engine_meta`` and later applies refuse to proceed on a mismatch.
    """
    sql = SCHEMA_PATH.read_text(encoding="utf-8").format(
        dense_dim=int(dense_dim), sparse_dim=int(sparse_dim)
    )
    with conn.transaction():
        conn.execute(sql)
        recorded = dict(conn.execute("SELECT key, value FROM engine_meta").fetchall())
        wanted = {"dense_dim": str(dense_dim), "sparse_dim": str(sparse_dim)}
        for key, value in wanted.items():
            if key not in recorded:
                conn.execute("INSERT INTO engine_meta VALUES (%s, %s)", (key, value))
            elif recorded[key] != value:
                raise SchemaMismatchError(
                    f"database was initialised with {key}={recorded[key]} but the "
                    f"embedder needs {value}; run `lkengine db reset` to rebuild"
                )


def reset_schema(conn: psycopg.Connection) -> None:
    """Drop everything this project owns. Destructive; used by `db reset` and tests."""
    with conn.transaction():
        conn.execute("DROP TABLE IF EXISTS corpus_xrefs, corpus_chunks, engine_meta CASCADE")


def create_ann_index(conn: psycopg.Connection) -> None:
    """Opt-in HNSW index on the dense column (ticket #7 asks for it).

    Off by default because at corpus scale it is strictly worse than an exact
    scan (build cost, memory, *approximate* recall). Turn it on when the
    corpus reaches ~100k chunks (Phase 1 full docs may get there). Caveat:
    pgvector applies HNSW *before* the metadata filter, so a selective
    ``WHERE product = ...`` can return fewer than ``pool`` rows; raise
    ``hnsw.ef_search`` or use ``hnsw.iterative_scan`` (pgvector 0.8) if so.
    The sparse column is not indexed: HNSW on sparsevec caps at 1000 non-zeros.
    """
    with conn.transaction():
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chunks_dense_hnsw ON corpus_chunks "
            "USING hnsw (dense vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
        )


def assert_compatible(conn: psycopg.Connection, *, dense_dim: int, sparse_dim: int) -> None:
    """Fail fast when querying with an embedder whose geometry differs from the index.

    Without this, pgvector raises a cryptic "different vector dimensions" deep
    inside a search. Also catches "forgot to ingest" (no schema yet).
    """
    try:
        recorded = dict(conn.execute("SELECT key, value FROM engine_meta").fetchall())
    except psycopg.errors.UndefinedTable as e:
        raise SchemaMismatchError("database is not initialised; run `lkengine ingest` first") from e
    for key, want in (("dense_dim", dense_dim), ("sparse_dim", sparse_dim)):
        if recorded.get(key) != str(want):
            raise SchemaMismatchError(
                f"index was built with {key}={recorded.get(key)} but this embedder needs {want}; "
                "use the embedder the index was built with, or re-ingest after `lkengine db reset`"
            )
