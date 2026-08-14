---
doc_id: SH-02
title: Versioning Policy, Release History & Migration
series: SH
product: both
version_scope: LangChain 1.x / LangGraph 1.x, LTS policy
last_verified: 2026-08-13
source_tier: 1
tags: [versioning, semver, lts, migration, breaking-changes, langchain-classic, AgentExecutor, deprecation]
---

# SH-02 — Versioning Policy, Release History & Migration

## SH-02.1 — Official versioning policy

LangChain follows standard **semantic versioning** — MAJOR.MINOR.PATCH — where major releases carry breaking changes, minor releases add backward-compatible features, and patch releases address bugs and security. Breaking changes ship with detailed migration guides and, where possible, automated migration tooling.

The documentation defines five **API stability levels** used throughout: stable (production-ready), beta (feature-complete but subject to feedback), alpha (experimental), deprecated, and internal (underscore-prefixed). Treating an underscore-prefixed symbol as public API is unsupported regardless of whether it currently works. **Tier 1** ([versioning docs](https://docs.langchain.com/oss/python/versioning)).

## SH-02.2 — LTS and support windows

LangChain 1.0 and LangGraph 1.0 are designated **long-term support** releases. The documented commitments are: 1.0 stays in active development until 2.0 ships, then enters maintenance mode for a **minimum of 12 months**; the latest major version receives full active support; the previous major version receives security updates and critical fixes for 12 months; older versions receive community support only.

The legacy lines — **LangChain 0.3 and LangGraph 0.4 — remain in maintenance through December 2026.** This is the date that actually governs migration planning, and it is documented officially, unlike the `AgentExecutor` claim in `SH-02.5`.

## SH-02.3 — Release timeline

**LangChain 0.1 (January 2024)** was announced as the first stable version, ending an extended 0.x period during which frequent breaking changes drew sustained criticism (see `SH-10`).

**LangChain 0.3 (September 2024)** completed the internal **Pydantic 1 → 2 migration**, letting user code use Pydantic 2 without compatibility bridges. It dropped Python 3.8, which had reached end of life. On the JavaScript side it made `@langchain/core` a peer dependency requiring explicit installation, made callbacks asynchronous by default — meaning they must be explicitly awaited in serverless contexts — and removed deprecated document loader and Google PaLM entrypoints.

**LangGraph v1 roadmap (June 2025).** Maintainers opened [issue #4973](https://github.com/langchain-ai/langgraph/issues/4973) soliciting community input on what was confusing, boilerplate-heavy, or missing in the low-level `StateGraph` API. It was closed as "not planned" but folded into an internal v1 sprint, with a commitment that "we don't plan to make any major breaking changes that make upgrading from v0 to v1 difficult." The issue is useful evidence that `StateGraph` ergonomics were a maintainer-acknowledged concern, not merely user error.

**LangChain / LangGraph 1.0 alpha (2025)** introduced `create_agent`, the LangGraph built-in agent runtime, and `.content_blocks` on `langchain-core`. **LangGraph 1.0 GA (~October 2025)** was announced with no breaking changes from the prior line (Tier 2 — corroborated by secondary reporting; a dedicated primary changelog entry was not retrievable during compilation).

## SH-02.4 — Migrating to v1

The official migration guide gives one explicit agent recommendation: *"Prior to v1.0, we recommended using `langgraph.prebuilt.create_react_agent` to build agents. Now, we recommend you use `langchain.agents.create_agent`."*

For legacy chains, the guide directs users of `LLMChain`, `ConversationChain`, and similar constructs to **install `langchain-classic` and update imports**. `langchain-classic` (verified 1.0.8, only 10 releases) is a stability shim, not an evolving surface — treat it as a bridge with a finite life, not a destination.

## SH-02.5 — The AgentExecutor EOL claim: unverified

Several third-party comparison articles state that `AgentExecutor` has an end-of-life date of **December 2026**. During compilation this date could **not** be corroborated in either the official v1 migration guide or the LangChain overview page; neither states an explicit `AgentExecutor` sunset date.

What *is* supported: `AgentExecutor` and the legacy agent types are superseded by `create_agent`, and legacy constructs have moved to `langchain-classic`. What is **Tier 3 and unverified**: the specific December 2026 date.

The plausible origin of the confusion is the officially documented December 2026 maintenance-window end for the **0.3 / 0.4 legacy lines** (see `SH-02.2`) — a real date attached to a different subject. Do not set a hard internal migration deadline on the `AgentExecutor` figure without confirming it against current official documentation.

## SH-02.6 — Practical migration guidance

Four steps, ordered by risk. **First, patch for security** — the CVE register in `SH-06` sets minimum versions that in several cases exceed what a conservative pin would give you, and this is the only genuinely urgent item. **Second, move agents to `create_agent`**, which is the documented path and unlocks the middleware system in `LC-06`. **Third, migrate off legacy chains** into `langchain-classic` imports or, preferably, rewrite them as agents or LangGraph graphs. **Fourth, plan around December 2026** for the 0.3/0.4 lines, since that date is officially documented.

Given the release cadence in `SH-01` — 509 releases of `langchain`, 276 of `langgraph` — pin versions explicitly and read release notes rather than tracking latest.

## Sources

- [Versioning — official docs](https://docs.langchain.com/oss/python/versioning) — accessed 2026-08-13 (Tier 1)
- [LangChain v1 migration guide](https://docs.langchain.com/oss/python/migrate/langchain-v1) — accessed 2026-08-13 (Tier 1)
- [Announcing LangChain v0.3](https://www.langchain.com/blog/announcing-langchain-v0-3) — accessed 2026-08-13 (Tier 1)
- [LangChain & LangGraph 1.0 alpha releases](https://www.langchain.com/blog/langchain-langchain-1-0-alpha-releases) — accessed 2026-08-13 (Tier 1)
- [Issue #4973 — LangGraph v1 roadmap](https://github.com/langchain-ai/langgraph/issues/4973) — accessed 2026-08-13 (Tier 1)
- [LangChain overview](https://docs.langchain.com/oss/python/langchain/overview) — accessed 2026-08-13 (Tier 1)
