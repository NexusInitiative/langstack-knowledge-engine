---
doc_id: AC-02
title: RAG Research Lineage — From Lewis 2020 to Self-Corrective RAG
series: AC
product: both
version_scope: foundational — not currency-sensitive
last_verified: 2026-08-13
source_tier: 1
recency_class: foundational
tags: [academic, rag, self-rag, crag, adaptive-rag, papers, retrieval, citations]
---

# AC-02 — RAG Research Lineage

## AC-02.1 — The originating paper

**Lewis, P., et al. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks."** arXiv:2005.11401, NeurIPS 2020.

This is the paper that named RAG and established the pattern LangChain's retrieval stack implements: combine a parametric model with a non-parametric retrieval index so that knowledge can be updated without retraining. Every component in `LC-07` — loaders, splitters, embeddings, vector stores, retrievers — exists to serve this architecture.

The paper predates the corpus recency window by design; see `AC-01.1` for the dual-recency policy. Citing a 2026 blog post instead of Lewis et al. for the definition of RAG would be a downgrade in accuracy, not an upgrade.

## AC-02.2 — Self-RAG: reflection tokens for retrieval quality

**"Self-RAG: Learning to Retrieve, Generate and Critique through Self-Reflection."** arXiv:2310.11511. **Cited directly by LangChain** in its agentic-RAG documentation.

Self-RAG introduces reflection tokens governing RAG stages — `Retrieve`, `ISREL` (is relevant), `ISSUP` (is supported), `ISUSE` (is useful) — allowing the system to evaluate its own retrieval and generation quality inline.

**LangGraph's implementation**, per LangChain's own description: retrieved documents are graded for relevance; if all are irrelevant, the query is reformulated and retrieval re-runs. A generation from relevant documents is then graded twice — once against the source material for grounding, once for usefulness. Failures trigger query rewrites and further retrieval loops.

Structurally this is a graph with conditional edges and cycles, which is precisely why it is a LangGraph tutorial rather than a LangChain chain. A linear chain cannot express "grade, and if it fails, go back."

## AC-02.3 — CRAG: corrective retrieval with a fallback source

**"Corrective Retrieval Augmented Generation."** arXiv:2401.15884. **Cited directly by LangChain.**

CRAG proposes a lightweight retrieval evaluator, supplementary web retrieval when vector-store results are ambiguous, and knowledge refinement by partitioning documents into strips and grading them.

**LangGraph's implementation** assesses retrieved-document quality with confidence scoring; if any document is judged irrelevant, retrieval is supplemented with web search (Tavily in LangChain's example) plus query rewriting. Notably, LangChain's implementation uses **Pydantic models to enforce consistent binary decision logic at conditional edges** — a concrete instance of the structured-output-as-control-flow pattern, tying `LC-04` directly to `LG-02`.

## AC-02.4 — Adaptive RAG: routing by query complexity

**Adaptive RAG** routes queries to different retrieval strategies based on assessed complexity — trivial queries answered directly, moderate ones with single-shot retrieval, complex ones with multi-step iterative retrieval. LangGraph publishes both a hosted-model and a local-model tutorial for it.

**Verification note:** unlike Self-RAG and CRAG, an explicit arXiv identifier for Adaptive RAG was **not confirmed** from a LangChain-authored source during compilation. The pattern and its LangGraph tutorials are verified; the specific paper citation is not. Treat the pattern as documented and the academic attribution as unconfirmed pending your own check.

## AC-02.5 — Why the lineage matters for the three RAG architectures

`LC-07` documents three architectures — 2-Step, Agentic, and Hybrid RAG. This paper lineage explains where they came from and what each costs.

**2-Step RAG** is Lewis et al. in its plainest form: retrieve once, generate once. Bounded cost, predictable latency.

**Agentic and Hybrid RAG** are Self-RAG and CRAG productized: they add grading, re-retrieval, query rewriting, and fallback sources. Each of those is an extra model call, and the loops are unbounded in principle. The quality improvement is real and so is the cost — which is the concrete mechanism behind the cost-compounding finding in `SH-10` when applied to retrieval workloads.

The practical guidance: adopt self-corrective RAG when retrieval quality is the binding constraint, and bound it explicitly with `ModelCallLimitMiddleware` (see `LC-06`) so a pathological query cannot loop indefinitely.

## AC-02.6 — Retrieval evaluation connects to LangSmith

Self-RAG and CRAG both formalize *grading retrieval* as a first-class step. That is the same activity LangSmith's evaluation framework supports offline (see `SH-05`): datasets of query/expected-document pairs, code-based or LLM-as-judge evaluators, and experiments comparing retrieval configurations.

The connection worth drawing: the graders these papers put *inside* the runtime loop and the evaluators LangSmith puts *outside* in a test harness are measuring the same property. Building the offline version first gives you a way to know whether the inline version is helping.

## Sources

- [RAG — arXiv:2005.11401](https://arxiv.org/abs/2005.11401) — accessed 2026-08-13 (Tier 1, foundational)
- [Self-RAG — arXiv:2310.11511](https://arxiv.org/abs/2310.11511) — accessed 2026-08-13 (Tier 1, foundational; cited by LangChain)
- [CRAG — arXiv:2401.15884](https://arxiv.org/abs/2401.15884) — accessed 2026-08-13 (Tier 1, foundational; cited by LangChain)
- [LangChain: Self-Reflective RAG with LangGraph](https://www.langchain.com/blog/agentic-rag-with-langgraph) — accessed 2026-08-13 (Tier 1)
- [Retrieval — official docs](https://docs.langchain.com/oss/python/langchain/retrieval) — accessed 2026-08-13 (Tier 1)
