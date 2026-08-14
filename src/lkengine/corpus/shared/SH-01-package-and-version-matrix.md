---
doc_id: SH-01
title: Package & Version Matrix (verified from PyPI)
series: SH
product: both
version_scope: as-published 2026-08-13
last_verified: 2026-08-13
source_tier: 1
tags: [packages, versions, pypi, python-version, ecosystem, dependencies]
---

# SH-01 — Package & Version Matrix

## SH-01.1 — Why this document is registry-sourced

Every figure in this document was read directly from the **PyPI JSON API** (`https://pypi.org/pypi/<package>/json`) on **2026-08-13**, not from documentation prose or third-party articles. This matters because the LangChain ecosystem releases extremely frequently — `langchain` alone has 509 published releases and `langsmith` has 520 — so any version number quoted in an article is stale within weeks. Treat the table in `SH-01.2` as a dated snapshot and re-query the registry before pinning anything in a real build. **Tier 1.**

## SH-01.2 — Verified version and Python-floor matrix

Snapshot taken 2026-08-13 from the PyPI JSON API, then **re-queried the same day as an accuracy check** — all values held, and upload timestamps were captured on the second pass. `requires_python` is the package's own declared floor, which is the authoritative answer to "what Python do I need."

**Upload recency (second pass):** `langchain` 1.3.15 and `langchain-core` 1.5.4 both uploaded 2026-08-11; `langgraph` 1.2.11 uploaded 2026-08-11; `langsmith` 0.10.18 uploaded 2026-08-11; `langgraph-checkpoint` 4.2.0 and `langgraph-checkpoint-postgres` 3.1.2 uploaded 2026-08-07; `langchain-mcp-adapters` 0.3.2 and `deepagents` 0.7.5 uploaded 2026-08-06; `langgraph-checkpoint-sqlite` 3.1.1 uploaded 2026-07-30. Every core package had shipped a release within the **two weeks** preceding compilation, which is the release cadence in `SH-01.1` made concrete.

| Package | Version | Releases | requires_python |
|---|---|---|---|
| `langchain` | 1.3.15 | 509 | — |
| `langchain-core` | 1.5.4 | 298 | — |
| `langchain-classic` | 1.0.8 | 10 | >=3.10, <4.0 |
| `langchain-community` | 0.4.2 | 99 | >=3.10, <4.0 |
| `langchain-text-splitters` | 1.1.2 | 27 | >=3.10, <4.0 |
| `langchain-openai` | 1.4.3 | 136 | >=3.10, <4.0 |
| `langchain-anthropic` | 1.5.5 | 93 | >=3.10, <4.0 |
| `langchain-mcp-adapters` | 0.3.2 | 32 | — |
| `langgraph` | 1.2.11 | 276 | — |
| `langgraph-prebuilt` | 1.1.0 | 44 | >=3.10 |
| `langgraph-checkpoint` | 4.2.0 | 60 | — |
| `langgraph-checkpoint-postgres` | 3.1.2 | 50 | >=3.10 |
| `langgraph-checkpoint-sqlite` | 3.1.1 | 24 | >=3.10 |
| `langgraph-checkpoint-mongodb` | 0.4.0 | 14 | >=3.10 |
| `langgraph-checkpoint-redis` | 0.5.1 | 28 | >=3.10, <3.15 |
| `langgraph-cli` | 0.4.31 | 140 | >=3.10 |
| `langgraph-sdk` | 0.4.2 | 100 | >=3.10 |
| `langgraph-supervisor` | 0.0.31 | 30 | >=3.10 |
| `deepagents` | 0.7.5 | 117 | >=3.11, <4.0 |
| `langsmith` | 0.10.18 | 520 | >=3.10 |

## SH-01.3 — The practical Python support answer

The current floor across the LangChain and LangGraph core packages is **Python 3.10**. `deepagents` is stricter at **Python 3.11**. `langgraph-checkpoint-redis` is the only package observed with an *upper* bound, declaring `<3.15`. LangGraph has separately been announced as compatible with Python 3.13 ([changelog](https://changelog.langchain.com/announcements/langgraph-is-now-compatible-with-python-3-13), Tier 1), and the LangGraph CLI accepts `python_version` values of `3.11`, `3.12`, or `3.13` in `langgraph.json`, defaulting to 3.11 (see `LG-10`).

Historical note: Python 3.8 support was dropped at LangChain v0.3 in September 2024, when Python 3.8 itself reached end of life. That is the origin of the widely-repeated "LangChain dropped 3.8" claim, but quoting it today understates the floor by two minor versions. **Tier 1.**

## SH-01.4 — Package topology and what belongs where

The ecosystem is deliberately split so that integrations can release independently of the core abstractions. Understanding the split is the fastest way to diagnose "where do I file this bug."

`langchain-core` holds the base abstractions — messages, content blocks, runnables, base chat-model and tool interfaces. It is the dependency almost everything else shares, which is also why security issues in it have the widest blast radius (see `SH-06`).

`langchain` is the main user-facing package, now centered on `create_agent` and the middleware system. `langchain-classic` is the compatibility home for pre-1.0 constructs — the official v1 migration guide directs users of legacy chains such as `LLMChain` and `ConversationChain` to install `langchain-classic` and update imports. Its low release count (10) reflects that it is a stability shim, not an actively evolving surface.

Provider integrations live in their own packages — `langchain-openai`, `langchain-anthropic`, and many others — each versioned independently. A bug in provider-specific tool calling or structured output is usually a bug in one of these, not in `langchain-core`, and will be fixed and released on that package's own cadence.

`langgraph` is the runtime. `langgraph-prebuilt` supplies prebuilt components, `langgraph-checkpoint` the persistence interfaces, and `langgraph-checkpoint-{postgres,sqlite,mongodb,redis}` the concrete backends. `langgraph-cli` and `langgraph-sdk` cover local development and client access respectively. `deepagents` sits on top of the whole stack as a batteries-included harness (see `LC-08`).

## SH-01.5 — Observed registry/repository discrepancy

At fetch time on 2026-08-13, the GitHub releases page for `langchain-ai/langgraph` displayed `langgraph==1.2.4` (dated 02 Jun) as its newest tag, while the PyPI JSON API reported `1.2.11` as the current published version the same day. PyPI is authoritative for what `pip install` resolves. The most likely explanation is a cached or paginated view of the releases page. This is recorded rather than silently reconciled; if you are automating version checks, prefer the registry API over scraping release pages. **Tier 1 (both artifacts), discrepancy unresolved.**

## Sources

- [PyPI JSON API](https://pypi.org/) — queried per-package 2026-08-13 (Tier 1)
- [LangGraph is now compatible with Python 3.13 — LangChain changelog](https://changelog.langchain.com/announcements/langgraph-is-now-compatible-with-python-3-13) — accessed 2026-08-13 (Tier 1)
- [LangChain v1 migration guide](https://docs.langchain.com/oss/python/migrate/langchain-v1) — accessed 2026-08-13 (Tier 1)
- [Announcing LangChain v0.3](https://www.langchain.com/blog/announcing-langchain-v0-3) — accessed 2026-08-13 (Tier 1)
- [langchain-ai/langgraph releases](https://github.com/langchain-ai/langgraph/releases) — accessed 2026-08-13 (Tier 1)
