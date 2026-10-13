# Roadmap & issue status

Source of truth for scope is the GitHub issues (labels: phase / epic / priority).
This page records where the code stands against them.

Legend: ✅ done on this branch · 🟡 partly done · ⬜ not started

## Phase 0 — walking skeleton

| Issue | Title | Status | Notes |
|---|---|---|---|
| #2 E1-1a | Golden dataset v1 | 🟡 | 30-question set already in `corpus/rag/`; now **validated against the corpus in CI**. Widening is #15. |
| #3 E2-1 | Schema & source registry | 🟡 | Data model (`models.py`), schema, stable ids, content hash, tier, version. `canonical_url`/`license` columns exist but are unpopulated until fetchers (#5/#13) land. Source registry still lives as markdown (`_meta/SOURCE-REGISTER.md`). |
| #4 E1-2 | Retrieval eval harness | ✅ | Recall@k, hit@k, doc-hit@k, MRR@10, per-category, known-gap handling. `lkengine eval`. |
| #5 E2-2a | Docs fetcher (LangGraph subset) | ⬜ | The pipeline ingests the shipped corpus; a fetcher produces the same `(CorpusDocument, [Section])` shape. |
| #6 E2-3 | Structure-aware chunker | ✅ | Heading-bounded, token-capped, fences atomic with lead-in. |
| #7 E2-4 | Embed & index | ✅ | Idempotent by content hash (+ model id), BGE-M3 dense+sparse, Postgres tsvector. HNSW **opt-in** — see ARCHITECTURE §6. |
| #8 E3-1 | Hybrid retrieval API | ✅ | Dense + sparse + FTS, weighted RRF, metadata filters, provenance. |
| #9 E3-2 | Grounded answer composer | ⬜ | Next. Consumes `RetrievalHit`; needs cite-or-abstain + delimited untrusted context. |
| #10 E3-3 | Thin interface | 🟡 | CLI covers ingest/search/eval; the end-to-end `ask` waits on #9. |
| #11 E7-1a | Basic injection defense | ⬜ | Belongs in the composer prompt (#9). |
| #12 E3-4 | Baseline eval report | ⬜ | Harness ready; needs a real BGE-M3 run. |
| #1 E6-0a | Spike: mcpdoc prior art | ⬜ | |

## Later phases

Unchanged: #13–#18, #19, #20–#22 (retrieval depth), #23–#25 (ops), #26–#30
(GitHub sources, gated on #28 injection defenses), #31–#33, #34–#37.

## Suggested next slice

1. Run the real baseline (`--embedder bge`) and record it in `EVALUATION.md` → closes #12.
2. #9 + #11 together: a composer that takes `RetrievalHit`s, wraps them in
   delimited untrusted blocks, cites by `section_id`, and abstains below a
   score/coverage threshold. Add answer-level metrics via #18.
3. #20 reranker behind an eval-gated flag, using the existing `pool` of 40.
