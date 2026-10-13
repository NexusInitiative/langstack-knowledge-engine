import psycopg
import pytest

from lkengine.db.migrate import SchemaMismatchError, apply_schema, reset_schema, create_ann_index


def test_apply_is_idempotent(conn):
    apply_schema(conn, dense_dim=8, sparse_dim=100)
    apply_schema(conn, dense_dim=8, sparse_dim=100)
    assert conn.execute("SELECT count(*) FROM corpus_chunks").fetchone() == (0,)


def test_dimension_mismatch_is_refused_with_actionable_message(conn):
    apply_schema(conn, dense_dim=8, sparse_dim=100)
    with pytest.raises(SchemaMismatchError, match="db reset"):
        apply_schema(conn, dense_dim=16, sparse_dim=100)


def test_reset_then_reinit_with_new_dimensions(conn):
    apply_schema(conn, dense_dim=8, sparse_dim=100)
    reset_schema(conn)
    apply_schema(conn, dense_dim=16, sparse_dim=100)


def test_retrievable_row_without_vectors_violates_constraint(conn):
    apply_schema(conn, dense_dim=8, sparse_dim=100)
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            "INSERT INTO corpus_chunks (chunk_id, section_id, doc_id, doc_title, heading, content,"
            " body, content_hash, series, product, last_verified, source_path, word_count)"
            " VALUES ('a','a','d','t','h','c','b','x','LG','both','2026-01-01','p',1)"
        )


def test_ann_index_is_opt_in_and_idempotent(conn):
    apply_schema(conn, dense_dim=8, sparse_dim=100)
    names = lambda: {r[0] for r in conn.execute(
        "SELECT indexname FROM pg_indexes WHERE schemaname = current_schema()").fetchall()}
    assert "idx_chunks_dense_hnsw" not in names()
    create_ann_index(conn)
    create_ann_index(conn)
    assert "idx_chunks_dense_hnsw" in names()
