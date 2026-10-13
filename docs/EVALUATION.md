# Evaluation

Principle from the README: *every design decision is measured, not assumed.*
The harness exists so a change to chunking, embeddings, fusion weights or (later)
a reranker is accepted or rejected by numbers.

## Run it

```bash
uv sync --dev --extra bge          # real embedder (torch, ~2 GB model on first run)
docker compose up -d
uv run lkengine db init
uv run lkengine ingest
uv run lkengine eval               # table; add --json for a machine-readable report
```

`--embedder hash` runs everything with the deterministic fake — fine for checking
plumbing, **meaningless as a quality number**.

## The golden set

`src/lkengine/corpus/rag/eval_questions.jsonl` — 30 hand-written questions:

```json
{"id": "q03", "query": "Does interrupt() resume from where it paused?",
 "expect_sections": ["LG-07.2"], "expect_docs": ["LG-07"],
 "category": "semantics", "note": "no — node restarts from the beginning"}
```

- **27 scored** questions have at least one `expect_sections` label.
- **3 known-gap** questions (`q27`–`q29`) have *empty* `expect_sections`: the
  corpus deliberately cannot answer them (no code samples, no integrations, no
  Stack Overflow). Correct behaviour is to abstain, which is an *answer*-level
  property, so they are excluded from retrieval metrics and listed separately in
  the report for manual review (and later for the judge, #18).
- Labels are validated against the live corpus in the unit tests
  (`test_shipped_golden_set_is_valid_against_the_shipped_corpus`): editing a
  section id without updating the set fails CI instead of silently deflating recall.

Still to do (#15): widen to 50–75 questions across all 9 categories (temporal and
adversarial are thin).

## Metrics

All computed over **sections** (chunk parts are collapsed, rank order preserved).

| Metric | Definition | Read it as |
|---|---|---|
| `recall@k` | fraction of the labelled sections found in top *k* | "did we retrieve everything the answer needs?" Strict for multi-section questions. |
| `hit@k` | 1 if any labelled section is in top *k* | lenient; many labels are alternates |
| `doc_hit@k` | 1 if any section from an expected *document* is in top *k* | right area, wrong paragraph |
| `mrr@10` | mean of 1/rank of the first correct section within 10 | does the right thing come *first*? matters because only a few chunks reach the LLM |

Per-category breakdown is printed because aggregate numbers hide the interesting
failure: e.g. exact-API questions should be near-perfect (lexical channels), while
debugging and multi-hop ("symptom → cause") questions are where dense retrieval,
reranking and parent-child expansion (#20, #22) have to earn their keep.

## Using the harness for experiments

`evaluate(retrieve, questions)` takes any `retrieve(query) -> [section_id, ...]`.
To compare variants, wrap each in a lambda:

```python
evaluate(lambda q: [h.section_id for h in dense_only.search(q, top_k=10)], qs)
evaluate(lambda q: [h.section_id for h in hybrid.search(q, top_k=10)], qs)
```

Because the harness never sees the database, the same function can score a
competitor (e.g. the hosted LangChain docs MCP server, spike #19).

## What the tests assert about eval

- Metric maths (`tests/unit/test_eval.py`): recall/hit/RR edge cases, per-category
  aggregation, known-gap exclusion, part-collapsing, doc-level credit.
- End-to-end smoke (`tests/integration/test_e2e_eval.py`): the real corpus + golden
  set through ingest → hybrid search → eval with the fake embedder must clear a
  deliberately loose floor (hit@10 ≥ 0.7; observed 0.85). This guards the pipeline
  against regressions; it is **not** the project's baseline.

## Reference numbers (fake embedder — plumbing check only)

Lexical `HashingEmbedder`, 27 scored questions: recall@5 = 0.67, hit@10 = 0.85,
mrr@10 = 0.71. The real BGE-M3 baseline is ticket #12 and must be run with
`--embedder bge`; record it here when it exists.

## Caveats

- 27 questions is small: a single question moves recall by ~3.7 points. Treat
  differences under ~5 points as noise until the set grows.
- Labels were written against this corpus's section structure; changing the
  chunker never invalidates them (they are section-level), but restructuring the
  corpus does.
