# Development guide

## Setup

```bash
uv sync --dev                  # light: psycopg, pyyaml, pytest. No torch.
uv sync --dev --extra bge      # + FlagEmbedding (torch) for the real embedder
cp .env.example .env
docker compose up -d           # Postgres 16 + pgvector 0.8
```

pgvector **≥ 0.7** is required (`sparsevec`). The compose image is 0.8.x.

## Tests

```bash
uv run pytest                  # everything; integration tests skip if no DB
uv run pytest tests/unit       # pure logic, no database, ~0.2 s
uv run pytest -m integration   # needs DATABASE_URL (or TEST_DATABASE_URL)
```

| Layer | Needs | Covers |
|---|---|---|
| `tests/unit` | nothing | parser, chunker, build, vector literals, fake embedder, RRF, metrics, golden validation, CLI parsing |
| `tests/integration` | Postgres + pgvector | schema/migrations, idempotent ingest, change detection, pruning, hybrid search, filters, xref expansion, end-to-end eval on the real corpus |

Integration tests each get a throwaway Postgres schema (see `tests/conftest.py`),
so they are isolated and never touch your real index. Prefer a separate `TEST_DATABASE_URL` anyway. If nothing is reachable they
**skip**, they do not fail — CI is the place they must run (`.github/workflows/ci.yml`
starts a pgvector service).

## Working style used on this codebase

1. **Pure core, thin shell.** Logic that can be a function of values is one (and is
   unit-tested); I/O lives in a few small modules.
2. **Test the behaviour you'd be embarrassed to break**, not the implementation:
   idempotent ingest, filters applied inside every channel, fences never split.
3. **Prefer a real database to a mock** for anything touching SQL. This paid off
   immediately: Postgres validates `CHECK` constraints on the proposed row *before*
   `ON CONFLICT` resolves, which a mocked connection would never have revealed (see
   the comment above `_REFRESH` in `db/store.py`).
4. **Document the why next to the code**: module docstrings state the design intent
   and the alternative that was rejected; `docs/ARCHITECTURE.md` collects the decisions.
5. **Measure before optimising**: the eval harness, not intuition, decides.

## Common tasks

| I want to… | Do |
|---|---|
| index the corpus | `uv run lkengine ingest` (safe to repeat; only changed chunks are embedded) |
| change embedding model / dims | `lkengine db reset && lkengine ingest --embedder X` |
| inspect a query | `lkengine search "…" --product LangGraph both --expand` (shows per-channel ranks) |
| score a change | `lkengine eval` before and after; compare per-category |
| enable HNSW | `lkengine db init --ann` (only worthwhile at ~100k chunks) |

## Conventions

- Python ≥ 3.12, type hints throughout, `from __future__ import annotations`.
- Commit messages: imperative subject < 72 chars.
- Don't edit `src/lkengine/corpus/rag/*.py` — they are the corpus bundle's frozen
  reference implementation, superseded by the package (kept for provenance).
