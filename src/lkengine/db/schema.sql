-- ============================================================================
-- lkengine schema. Applied by lkengine.db.migrate.apply_schema(); idempotent.
-- Placeholders {dense_dim} / {sparse_dim} are filled from the Embedder in use
-- (BGE-M3: 1024 / 250002). Postgres 14+, pgvector 0.7+ (sparsevec needs 0.7).
--
-- Design notes (the "why" lives in docs/ARCHITECTURE.md):
--  * One table is the single source of truth for vectors, lexical index,
--    metadata and provenance - no second store to keep in sync.
--  * chunk_id is the primary key; section_id is the citation anchor and is
--    NOT unique (an oversized section becomes several chunks).
--  * content_hash makes ingestion idempotent: unchanged content is never
--    re-embedded. embedding_model makes a model swap detectable.
--  * Vectors are NULL for non-retrievable (META) rows - we don't spend
--    compute embedding housekeeping text. The CHECK enforces the invariant.
--  * No ANN index by default: at hundreds-to-low-thousands of chunks an exact
--    scan is sub-millisecond and 100% recall. See db.migrate.create_ann_index.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS engine_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS corpus_chunks (
    -- Identity ---------------------------------------------------------------
    chunk_id        TEXT PRIMARY KEY,               -- 'LG-04.3' or 'LG-04.3~2'
    section_id      TEXT NOT NULL,                  -- 'LG-04.3' - citation anchor
    part            INT  NOT NULL DEFAULT 1,
    doc_id          TEXT NOT NULL,                  -- 'LG-04'
    doc_title       TEXT NOT NULL,
    heading         TEXT NOT NULL,

    -- Payload -----------------------------------------------------------------
    content         TEXT NOT NULL,                  -- embedded: '# <doc title>' + body
    body            TEXT NOT NULL,                  -- shown to the user / the LLM
    content_hash    TEXT NOT NULL,                  -- sha256(content)

    -- Filter dimensions & provenance -----------------------------------------
    series          TEXT NOT NULL CHECK (series IN ('LC','LG','SH','AC','META')),
    product         TEXT NOT NULL CHECK (product IN ('LangChain','LangGraph','both')),
    source_tier     SMALLINT CHECK (source_tier IN (1,2,3)),  -- 1 primary .. 3 single-source
    recency_class   TEXT NOT NULL DEFAULT 'current'
                    CHECK (recency_class IN ('current','foundational')),
    version_scope   TEXT,
    last_verified   DATE NOT NULL,
    tags            TEXT[] NOT NULL DEFAULT '{{}}',
    source_path     TEXT NOT NULL,
    canonical_url   TEXT,                           -- filled by Phase 1 fetchers
    license         TEXT,                           -- filled by Phase 1 fetchers

    -- Derived signals ---------------------------------------------------------
    word_count      INT     NOT NULL,
    has_code        BOOLEAN NOT NULL DEFAULT FALSE,
    is_retrievable  BOOLEAN NOT NULL DEFAULT TRUE,

    -- Vectors -----------------------------------------------------------------
    embedding_model TEXT,
    dense           vector({dense_dim}),            -- cosine distance (<=>)
    sparse          sparsevec({sparse_dim}),        -- inner product (<#>)

    -- Postgres-native lexical channel: exact identifiers (InvalidUpdateError)
    fts             tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT retrievable_rows_are_embedded CHECK (
        NOT is_retrievable
        OR (dense IS NOT NULL AND sparse IS NOT NULL AND embedding_model IS NOT NULL)
    )
);

-- Metadata filters run on every query, so these matter (unlike an ANN index).
CREATE INDEX IF NOT EXISTS idx_chunks_section ON corpus_chunks (section_id);
CREATE INDEX IF NOT EXISTS idx_chunks_doc     ON corpus_chunks (doc_id);
CREATE INDEX IF NOT EXISTS idx_chunks_product ON corpus_chunks (product)       WHERE is_retrievable;
CREATE INDEX IF NOT EXISTS idx_chunks_series  ON corpus_chunks (series)        WHERE is_retrievable;
CREATE INDEX IF NOT EXISTS idx_chunks_tier    ON corpus_chunks (source_tier)   WHERE is_retrievable;
CREATE INDEX IF NOT EXISTS idx_chunks_tags    ON corpus_chunks USING GIN (tags);
CREATE INDEX IF NOT EXISTS idx_chunks_fts     ON corpus_chunks USING GIN (fts);

-- Cross-reference graph: the corpus cites `LG-04`-style ids instead of "as
-- described above", so this table is built mechanically at ingest time and
-- used to expand retrieved context along real semantic links.
CREATE TABLE IF NOT EXISTS corpus_xrefs (
    from_section_id TEXT NOT NULL,
    to_doc_id       TEXT NOT NULL,
    PRIMARY KEY (from_section_id, to_doc_id)
);
CREATE INDEX IF NOT EXISTS idx_xrefs_to ON corpus_xrefs (to_doc_id);
