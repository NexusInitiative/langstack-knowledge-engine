# RAG Deployment — pgvector + BGE-M3

Reference implementation for serving this corpus. Four files:

| File | Purpose |
|---|---|
| `schema.sql` | pgvector DDL — chunks, cross-reference graph, filter indexes |
| `ingest.py` | Parse → BGE-M3 dense+sparse → Postgres |
| `search.py` | Hybrid retrieval (dense + sparse + FTS) → RRF → cross-encoder rerank |
| `eval_questions.jsonl` | 30-question golden set, every section ID validated against the corpus |

```bash
pip install FlagEmbedding "psycopg[binary]" pyyaml
psql "$DSN" -f schema.sql
python ingest.py --corpus .. --dsn "$DSN"
python search.py --dsn "$DSN" "why does my graph hang?"
```

---

## The two models are different models

This is the most common point of confusion, so it is worth stating plainly:

| | `BAAI/bge-m3` | `BAAI/bge-reranker-v2-m3` |
|---|---|---|
| Type | Bi-encoder (embedding) | Cross-encoder (reranker) |
| Output | Vectors | A relevance score |
| Max length | **8192 tokens** | **512 tokens** (query + passage combined) |
| Runs over | The whole corpus, once, offline | ~20–40 candidates, per query |
| Params | — | 0.6B (base model is BGE-M3) |

BGE-M3 **cannot** rerank — it has no mechanism for scoring a pair jointly. The reranker **cannot** embed — it never produces a vector. You need both, at different stages. Retrieve wide with the bi-encoder, rerank narrow with the cross-encoder.

BGE-M3 requires **no instruction prefix** on queries (unlike `bge-large-en`), so queries and documents are encoded identically. Do not prepend "Represent this sentence for searching…".

---

## Why BGE-M3 is an unusually good fit here

BGE-M3 emits **dense, learned-sparse, and ColBERT multi-vector** representations from a single forward pass. The sparse channel is the reason it fits this corpus specifically.

This corpus is dense with exact identifiers that dense retrieval handles badly: `InvalidUpdateError`, `with_structured_output`, `CVE-2026-34070`, `wrap_model_call`, `langgraph.json`, `AsyncPostgresSaver`. A user searching for a literal exception name needs lexical matching. BGE-M3's sparse output gives you that **without running a second model or a separate BM25 index** — one encode call, two retrieval channels.

`search.py` uses three channels — dense, BGE-M3 sparse, and Postgres `tsvector` — fused with Reciprocal Rank Fusion (k=60). The third is weighted at 0.5 since it overlaps the sparse channel; it costs nothing and catches literal strings the learned sparse model down-weights.

**ColBERT vectors are deliberately not used.** At 220 chunks, MaxSim scoring would add storage and complexity for a gain the reranker already delivers more cheaply.

---

## Why there is no HNSW index

**220 chunks. Use exact search.**

A sequential scan over 220 × 1024-dim vectors is sub-millisecond. An ANN index here is strictly worse: build cost, memory, approximate recall (you lose correct answers), and `ef_search` tuning — to speed up something already free.

ANN starts paying off around 100k+ vectors. `schema.sql` includes the `CREATE INDEX` statements commented out for when this corpus gets merged into something larger. pgvector v0.8.5 HNSW limits, for when you get there: `vector` ≤ 2000d, `halfvec` ≤ 4000d, `sparsevec` ≤ 1000 non-zero elements. BGE-M3's 1024 dims fit `vector` fine.

**Metadata indexes do matter** and are enabled — filters run on every query.

---

## Chunk-level findings that shaped this design

Measured against the actual corpus:

- **220 chunks, zero duplicate IDs**, median 124 words, p90 226, p99 343, max 659.
- **Only 3 sections (1.4%) exceed the reranker's 512-token budget** — `META-00.1`, `META-02.8`, `META-01.4`. All three are META housekeeping (manifest tables, source registers).
- Therefore: **`ingest.py` marks all META sections `is_retrievable = FALSE`.** This removes every reranker-truncation case in one move, and drops ~20 chunks that answer no user question. Provenance stays queryable by `doc_id` when you need it.
- **No chunk comes close to BGE-M3's 8192-token encode window** (largest is ~11%). Nothing is truncated at embed time.

---

## Recommended query configuration

**Retrieve 40, rerank to 6.** Pool of 40 gives the cross-encoder enough to work with; final k=6 because answers here often need 2–3 sections plus a cross-reference.

**Filter before ranking.** Pass `--product LangGraph both` for LangGraph questions. LangChain and LangGraph answers are genuinely different and unfiltered retrieval mixes them.

**Consider `--series LC LG SH` for how-to questions** to exclude academic material, and `--max-tier 1` when you want primary sources only.

**Cross-reference expansion is enabled.** The corpus uses explicit `` `LG-04` `` references rather than "as described above" precisely so this is mechanical — `search.py` pulls section `.1` of referenced documents not already in the result set.

---

## Evaluate before you trust it

`eval_questions.jsonl` has 30 questions with expected section IDs, all validated against the corpus. Categories: debugging, semantics, security, api-reference, migration, cost, conceptual, citation, guidance.

**Five questions are deliberately adversarial** and are the most informative in the set:

- **q09** ("Is AgentExecutor removed in December 2026?") — the corpus carries this as an explicitly unverified Tier 3 claim. A correct system flags the uncertainty. A system that asserts the date has failed.
- **q30** ("What is the current version of langgraph?") — must caveat that it is a dated snapshot and point to PyPI.
- **q27, q28, q29** — probe the three known gaps (code examples, integrations, Stack Overflow-style symptom queries). Correct behavior is a graceful decline, not fabrication.

Suggested metrics: recall@6 and MRR against `expect_sections`, plus a manual pass on the five adversarial items. Run it once with `--no-rerank` and once with reranking to measure what the cross-encoder is actually buying you — on a corpus this small it may be less than you expect, and that is worth knowing before you pay for it on every query.

---

## System prompt guidance

Tell the answering model to: cite by `section_id`; surface `source_tier` when an answer rests on Tier 2 or 3; show `version_scope` and `last_verified` on version-sensitive answers; and never present a version number from this corpus as a live fact — direct users to PyPI instead.
