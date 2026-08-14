---
doc_id: SH-05
title: Observability & Evaluation (LangSmith)
series: SH
product: both
version_scope: langsmith 0.10.18
last_verified: 2026-08-13
source_tier: 1
tags: [langsmith, tracing, observability, evaluation, datasets, evaluators, llm-as-judge, experiments, monitoring]
---

# SH-05 — Observability & Evaluation

## SH-05.1 — What LangSmith covers

LangSmith is LangChain's commercial platform for observability, evaluation, and deployment, offering "full visibility into your LLM application: from individual traces to production-wide performance metrics."

Its documented capabilities span tracing setup via environment variables, framework integrations, or SDK; trace investigation including filtering, exporting, sharing, and comparing; performance monitoring through dashboards and alerts; automation via rules, webhooks, and online evaluations; feedback collection through annotation and user feedback; and issue detection through the LangSmith Engine for diagnosing recurring problems.

It integrates beyond LangChain — OpenAI, Anthropic, CrewAI, Vercel AI SDK, and Pydantic AI are documented. The Python client is `langsmith`, verified 0.10.18 across **520 releases**, the highest release count in the ecosystem (see `SH-01`). **Tier 1** ([observability docs](https://docs.langchain.com/langsmith/observability)).

## SH-05.2 — Why observability is structurally important here

LangSmith is a paid product, and it is reasonable to be skeptical of a vendor recommending its own tooling. Two independent findings in this corpus nonetheless make observability more load-bearing for LangChain than for a typical library.

First, **debugging opacity is the most consistently corroborated criticism** of the framework across independent sources (see `SH-10`) — orchestration hides the execution path, and practitioners report substantial time lost tracing behavior through abstraction layers. Tracing addresses that directly.

Second, **cost behavior is non-obvious**. The measured 66-session study in `SH-10` found input tokens exceeding output roughly 1.9:1 and per-step cost at step 200 running about 100× step 1, because each step re-bills accumulated context. That pattern is invisible without per-run token accounting.

Notably, even critics of LangChain in the sources reviewed tend to single out LangSmith as the component that delivers value. LangChain's framework-native alternative for token accounting specifically — `UsageMetadataCallbackHandler` and `get_usage_metadata_callback` — is documented in `LC-02` and requires no paid tooling.

## SH-05.3 — Evaluation: offline and online

LangSmith frames evaluation in two modes. **Offline evaluation** — "test before you ship" — runs against curated datasets during development to benchmark performance and catch regressions. **Online evaluation** — "monitor in production" — evaluates real user interactions in real time to detect issues on live traffic.

## SH-05.4 — Evaluation components

Three concepts compose the evaluation model.

**Datasets and examples** are curated test cases pairing inputs with reference outputs. They can be assembled manually, harvested from production traces, or generated synthetically. Harvesting from traces is the highest-leverage route, because it grounds the test set in real usage.

**Evaluators** score performance, with four documented approaches: human review, code-based rules, LLM-as-judge, and pairwise comparison. Code-based rules should be preferred wherever the property is mechanically checkable — schema validity, latency, presence of a required field — because they are cheaper and deterministic. Reserve LLM-as-judge for genuinely subjective qualities.

**Experiments** are the results of running an application against a dataset, with configurable repetitions, concurrency, and caching. Repetitions matter for non-deterministic systems: a single pass tells you little about variance.

The documented offline workflow is create dataset → define evaluators → run experiment → analyze comparatively, supporting benchmarking, unit testing, regression detection, and backtesting. The online workflow deploys the application, configures production evaluators with sampling controls, monitors in real time, and **feeds failing traces back into datasets** — closing the loop between production failures and the regression suite.

**Verification limitation:** the evaluation overview page as retrieved did not specify the exact `evaluate()` function signature or the pytest/vitest integration details. Those names are commonly referenced but are **not confirmed here**; check `reference.langchain.com` and the LangSmith SDK docs before use.

## SH-05.5 — Rubric-based self-evaluation inside agents

Distinct from LangSmith, LangChain ships **`RubricMiddleware`**, which applies LLM-as-a-judge grading for agent self-evaluation and iteration at runtime (see `LC-06`). This is in-loop quality control rather than offline measurement — the agent grades and revises its own work during a run.

The two are complementary and should not be substituted for one another: `RubricMiddleware` improves an individual run; LangSmith evaluation tells you whether your system got better or worse across many runs after a change.

## SH-05.6 — Deployment observability

LangGraph deployments surface within LangSmith as a first-class product area, with the LangSmith changelog covering tracing improvements, engine capabilities, deployment updates, sandbox enhancements, administration, and LLM Gateway functionality. The `deploy` CLI command targets **LangSmith Deployments** directly (see `LG-10`), which is the intended path from local graph to observed production service.

## Sources

- [LangSmith observability — official docs](https://docs.langchain.com/langsmith/observability) — accessed 2026-08-13 (Tier 1)
- [LangSmith evaluation — official docs](https://docs.langchain.com/langsmith/evaluation) — accessed 2026-08-13 (Tier 1)
- [LangSmith changelog](https://docs.langchain.com/langsmith/changelog) — accessed 2026-08-13 (Tier 1)
- [Prebuilt middleware — official docs](https://docs.langchain.com/oss/python/langchain/middleware/built-in) — accessed 2026-08-13 (Tier 1)
- [PyPI: langsmith](https://pypi.org/pypi/langsmith/json) — queried 2026-08-13 (Tier 1)
