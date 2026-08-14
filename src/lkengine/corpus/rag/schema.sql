-- ============================================================================
-- LangChain/LangGraph Corpus — pgvector schema
-- Target: pgvector v0.8.5+ on PostgreSQL 14+
-- Embedding model: BAAI/bge-m3 (1024-dim dense + learned sparse)
-- ============================================================================
--
-- DESIGN NOTE — READ THIS BEFORE ADDING AN INDEX:
--
-- This corpus is 220 chunks. At that scale you should use EXACT SEARCH.
-- A sequential scan over 220 x 1024-dim vectors is sub-millisecond.
--
-- An HNSW index here would be strictly worse: it costs build time, consumes
-- memory, introduces approximate recall (you lose correct answers), and needs
-- ef_search tuning — to accelerate a scan that is already effectively free.
--
-- ANN indexes start earning their keep in the ~100k+ vector range. The
-- CREATE INDEX statements are included at the bottom, commented out, for when
-- you merge this corpus into a much larger one. Until then, leave them off.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- optional: fuzzy identifier matching

-- ---------------------------------------------------------------------------
-- Main chunk table
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS corpus_chunks CASCADE;

CREATE TABLE corpus_chunks (
    -- Identity -------------------------------------------------------------
    section_id      TEXT PRIMARY KEY,          -- 'LG-04.3' — stable citation anchor
    doc_id          TEXT NOT NULL,             -- 'LG-04'
    doc_title       TEXT NOT NULL,
    heading         TEXT NOT NULL,             -- full '## LG-04.3 — Threads and thread_id'

    -- Retrieval payload ----------------------------------------------------
    content         TEXT NOT NULL,             -- doc title + section body (what gets embedded)
    body            TEXT NOT NULL,             -- section body alone (what you show the user)

    -- Filter dimensions ----------------------------------------------------
    series          TEXT NOT NULL CHECK (series IN ('LC','LG','SH','AC','META')),
    product         TEXT NOT NULL CHECK (product IN ('LangChain','LangGraph','both')),
    source_tier     SMALLINT,                  -- 1 = primary, 2 = corroborated, 3 = single-source
    recency_class   TEXT NOT NULL DEFAULT 'current'
                    CHECK (recency_class IN ('current','foundational')),
    version_scope   TEXT,
    last_verified   DATE NOT NULL,
    tags            TEXT[] NOT NULL DEFAULT '{}',
    source_path     TEXT NOT NULL,

    -- Derived signals ------------------------------------------------------
    word_count      INT NOT NULL,
    has_code        BOOLEAN NOT NULL DEFAULT FALSE,
    is_retrievable  BOOLEAN NOT NULL DEFAULT TRUE,  -- FALSE for META housekeeping

    -- Vectors --------------------------------------------------------------
    -- bge-m3 dense: 1024 dims. Cosine distance (<=>) — normalize at encode time.
    dense           vector(1024),

    -- bge-m3 learned sparse (lexical weights over the XLM-RoBERTa vocab).
    -- Dimension is set from the tokenizer at ingest time (~250k).
    -- pgvector sparsevec stores up to 16,000 non-zero elements; our chunks
    -- produce roughly 100-250 non-zero, so there is ample headroom.
    sparse          sparsevec(250002),

    -- Postgres native lexical channel — a zero-dependency fallback/complement
    -- to bge-m3 sparse. Excellent for exact identifiers like InvalidUpdateError.
    fts             tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Metadata indexes — these DO matter. Filters run on every query.
-- ---------------------------------------------------------------------------
CREATE INDEX idx_chunks_product     ON corpus_chunks (product)       WHERE is_retrievable;
CREATE INDEX idx_chunks_series      ON corpus_chunks (series)        WHERE is_retrievable;
CREATE INDEX idx_chunks_tier        ON corpus_chunks (source_tier)   WHERE is_retrievable;
CREATE INDEX idx_chunks_recency     ON corpus_chunks (recency_class) WHERE is_retrievable;
CREATE INDEX idx_chunks_doc         ON corpus_chunks (doc_id);
CREATE INDEX idx_chunks_tags        ON corpus_chunks USING GIN (tags);
CREATE INDEX idx_chunks_fts         ON corpus_chunks USING GIN (fts);
CREATE INDEX idx_chunks_heading_trgm ON corpus_chunks USING GIN (heading gin_trgm_ops);

-- ---------------------------------------------------------------------------
-- Cross-reference graph.
-- The corpus uses explicit `LG-04`-style references instead of "as described
-- above", specifically so this table can be built mechanically. Use it to
-- expand retrieved context along real semantic links.
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS corpus_xrefs CASCADE;

CREATE TABLE corpus_xrefs (
    from_section_id TEXT NOT NULL REFERENCES corpus_chunks(section_id) ON DELETE CASCADE,
    to_doc_id       TEXT NOT NULL,
    PRIMARY KEY (from_section_id, to_doc_id)
);
CREATE INDEX idx_xrefs_to ON corpus_xrefs (to_doc_id);

-- ---------------------------------------------------------------------------
-- Convenience view: the retrievable slice
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW corpus_searchable AS
SELECT * FROM corpus_chunks WHERE is_retrievable;

-- ---------------------------------------------------------------------------
-- Sanity checks to run after ingest
-- ---------------------------------------------------------------------------
-- SELECT count(*) FROM corpus_chunks;                                  -- expect 220
-- SELECT count(*) FROM corpus_chunks WHERE is_retrievable;             -- expect ~200
-- SELECT product, count(*) FROM corpus_chunks GROUP BY product;
-- SELECT series,  count(*) FROM corpus_chunks GROUP BY series;
-- SELECT count(*) FROM corpus_chunks WHERE dense IS NULL;              -- expect 0
-- SELECT count(*) FROM corpus_chunks WHERE sparse IS NULL;             -- expect 0
-- SELECT max(word_count) FROM corpus_chunks WHERE is_retrievable;      -- expect <= ~343

-- ============================================================================
-- ANN INDEXES — DO NOT ENABLE AT 220 CHUNKS. See design note at top.
-- Enable only if this corpus is merged into a much larger collection (100k+).
-- pgvector v0.8.5 index limits: HNSW supports vector<=2000d, halfvec<=4000d,
-- sparsevec<=1000 non-zero elements.
-- ============================================================================
-- CREATE INDEX idx_chunks_dense_hnsw ON corpus_chunks
--     USING hnsw (dense vector_cosine_ops) WITH (m = 16, ef_construction = 64);
-- CREATE INDEX idx_chunks_sparse_hnsw ON corpus_chunks
--     USING hnsw (sparse sparsevec_ip_ops);
-- SET hnsw.ef_search = 100;   -- raise for recall, lower for latency
