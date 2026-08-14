---
doc_id: SH-04
title: Language Support — Official vs Community
series: SH
product: both
version_scope: 2026-08
last_verified: 2026-08-13
source_tier: 1
tags: [python, javascript, typescript, java, go, langchain4j, langchaingo, parity, ports]
---

# SH-04 — Language Support

## SH-04.1 — Officially maintained: Python and JavaScript/TypeScript only

LangChain Inc maintains two language ecosystems. **Python** is primary: `langchain`, `langgraph`, `langchain-core`, and the partner integration packages, with a floor of Python 3.10 (see `SH-01`). **JavaScript/TypeScript** is second and near-parity: `langchainjs` and `langgraphjs`, plus matching `@langchain/*` npm packages.

Everything else is a third-party reimplementation. This distinction is load-bearing for anyone evaluating LangChain for a JVM or Go service.

## SH-04.2 — Python/JS divergences that matter

The two official ecosystems are close but not identical, and three documented differences catch people out.

**Peer dependency.** Since v0.3, `@langchain/core` is a **peer dependency** in JS and must be installed explicitly. Python has no equivalent requirement.

**Async callbacks.** Also since v0.3, JS callbacks execute **asynchronously by default** and must be explicitly awaited — the documentation specifically flags serverless contexts, where a function can terminate before un-awaited callbacks flush, silently losing traces or side effects.

**Stream format versions.** The version parameters on streaming APIs differ across surfaces (`version="v2"` for LangGraph `.stream()`, `version="v3"` for LangChain `agent.stream_events()`, per `LG-06` and `LC-05`). When following a tutorial, confirm both the language and the API surface it targets.

Feature arrival is generally Python-first. Several verified issues in `SH-08` are JS-specific — Gemini structured output falling back to tool-call emulation ([langchainjs #8585](https://github.com/langchain-ai/langchainjs/issues/8585)), streaming failures against the OpenAI Responses API ([langgraphjs #1454](https://github.com/langchain-ai/langgraphjs/issues/1454)), and checkpointers breaking in Cloudflare Workers ([langgraphjs #1692](https://github.com/langchain-ai/langgraphjs/issues/1692)).

## SH-04.3 — Java: langchain4j (community)

[`langchain4j`](https://github.com/langchain4j/langchain4j) is an independent, idiomatic Java library for building LLM applications on the JVM. It offers a unified API over LLM providers and vector stores, supports tool calling **including MCP**, and covers agents and RAG. It integrates with Quarkus and Spring Boot.

It is **not maintained by LangChain Inc.** It has its own maintainers, release cadence, API design, and issue tracker. It is a parallel project inspired by LangChain, not a port of it — its API does not mirror the Python package, and version numbers correspond to nothing in the Python ecosystem.

For JVM teams it is generally the better choice than trying to bridge to Python, precisely because it is idiomatic Java rather than a translation. Just do not expect documentation, tutorials, or `SH-08` issues from the Python project to transfer.

## SH-04.4 — Go: langchaingo (community)

[`langchaingo`](https://pkg.go.dev/github.com/tmc/langchaingo) (`tmc/langchaingo`) is the most active Go implementation, described as "LangChain for Go." A smaller alternative, `Struki84/GoLangChain`, also exists. Neither is official.

The same caveats as Java apply: independent maintainership, independent versioning, no guaranteed feature parity, and no coverage by LangChain's official documentation or security advisories. On that last point specifically — the CVE register in `SH-06` covers the Python and npm packages; community ports have their own security posture that must be assessed separately.

## SH-04.5 — A cross-language integration nuance

Google Cloud publishes LangChain database integrations with connectors for **Go, Java, and JavaScript** in addition to Python. This is sometimes cited as evidence that LangChain supports those languages.

It does not show that. It shows that **Google** ships integration libraries targeting multiple language ecosystems, including the community ports. It is Tier 1 evidence about Google's product and only Tier 2 evidence — weak evidence — about LangChain's own language support.

## SH-04.6 — Practical guidance

Choose **Python** for the fullest, earliest, best-documented surface, and when using Deep Agents (`LC-08`), which is Python-only among the official packages. Choose **JavaScript/TypeScript** when your stack requires it, budgeting for occasional feature lag and the divergences in `SH-04.2`. Choose **`langchain4j` or `langchaingo`** when staying in-language outweighs ecosystem depth — but verify every claim against those projects' own repositories, because nothing in the `LC-*` or `LG-*` series of this corpus is guaranteed to apply to them.

## Sources

- [langchain-ai/langchainjs](https://github.com/langchain-ai/langchainjs) — accessed 2026-08-13 (Tier 1)
- [Announcing LangChain v0.3 (JS breaking changes)](https://www.langchain.com/blog/announcing-langchain-v0-3) — accessed 2026-08-13 (Tier 1)
- [langchain4j/langchain4j](https://github.com/langchain4j/langchain4j) — accessed 2026-08-13 (Tier 1 for the project itself)
- [tmc/langchaingo](https://pkg.go.dev/github.com/tmc/langchaingo) — accessed 2026-08-13 (Tier 1 for the project itself)
- [Google Cloud: LangChain integrations support Go, Java, JavaScript](https://cloud.google.com/blog/products/databases/google-cloud-database-and-langchain-integrations-support-go-java-and-javascript/) — accessed 2026-08-13 (Tier 1 for Google's product)
- [LangChain.js for Beginners — Microsoft](https://developer.microsoft.com/blog/langchainjs-for-beginners/) — accessed 2026-08-13 (Tier 2)
