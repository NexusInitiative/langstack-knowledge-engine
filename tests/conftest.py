"""Shared fixtures.

Integration tests need Postgres with pgvector >= 0.7 (``docker compose up -d``
or the CI service). They look for ``TEST_DATABASE_URL`` then ``DATABASE_URL``
and are *skipped* - not failed - when no database is reachable, so
``uv run pytest`` is always green on a laptop with nothing running.

Each test gets its own throwaway Postgres schema, so tests are isolated and
never touch real data.
"""

from __future__ import annotations

import os
import uuid

import psycopg
import pytest
from dotenv import load_dotenv

load_dotenv()


def pytest_collection_modifyitems(items):
    for item in items:
        if "integration" in item.nodeid.split("/"):
            item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session")
def database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("no TEST_DATABASE_URL / DATABASE_URL set")
    try:
        with psycopg.connect(url, connect_timeout=3, autocommit=True) as c:
            c.execute("CREATE EXTENSION IF NOT EXISTS vector")
    except psycopg.Error as e:
        pytest.skip(f"Postgres with pgvector not reachable: {e}")
    return url


@pytest.fixture
def conn(database_url):
    """Autocommit connection pinned to a private schema, dropped afterwards."""
    schema = f"t_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(database_url, autocommit=True) as c:
        c.execute(f"CREATE SCHEMA {schema}")
        c.execute(f"SET search_path TO {schema}, public")
        try:
            yield c
        finally:
            c.execute(f"DROP SCHEMA {schema} CASCADE")
