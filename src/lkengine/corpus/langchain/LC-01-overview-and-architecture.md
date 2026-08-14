---
doc_id: LC-01
title: LangChain — Overview & Architecture
series: LC
product: LangChain
version_scope: langchain 1.x (verified 1.3.15)
last_verified: 2026-08-13
source_tier: 1
tags: [overview, architecture, packages, positioning, deep-agents, langgraph-relationship]
---

# LC-01 — LangChain Overview & Architecture

## LC-01.1 — What LangChain is

LangChain describes itself in its repository README as **"the agent engineering platform"** — a framework for building agents and LLM-powered applications by composing interoperable components and third-party services. The README frames its value around six developer needs: real-time data augmentation through a broad integration catalog, model interoperability so providers can be swapped, rapid prototyping via modular architecture, production-grade monitoring and deployment, an active open-source community, and flexible abstraction layers that let a team choose how much framework they want.

Installation is `pip install langchain` or `uv add langchain`. The project is MIT licensed and carries roughly 137k GitHub stars and 22.7k forks on the Python repository. **Tier 1** ([README](https://github.com/langchain-ai/langchain/blob/master/README.md)).

## LC-01.2 — The three-tier positioning: LangChain, LangGraph, Deep Agents

LangChain's own documentation positions three products as ascending levels of abstraction, and knowing which one a question is really about prevents most architectural confusion.

**LangGraph** is the lowest level — a graph runtime for stateful, durable, long-running agents. You reach for it when you need explicit control over control flow, state, and persistence. It is documented in the `LG-*` series of this corpus.

**LangChain** sits in the middle. Since 1.0 its center of gravity is `create_agent`, a standard agent loop with a middleware system for customization (see `LC-05` and `LC-06`). Critically, `create_agent` is **implemented on top of the LangGraph runtime** — this is the main intersection between the two products, and it means LangGraph concepts like checkpointers, stores, and interrupts surface directly in LangChain agent APIs.

**Deep Agents** is the highest level — a batteries-included harness with a filesystem, subagents, planning, and memory already wired up. The LangChain README explicitly directs beginners toward Deep Agents rather than assembling primitives by hand. It is documented in `LC-08`. **Tier 1** ([LangChain overview](https://docs.langchain.com/oss/python/langchain/overview)).

## LC-01.3 — Package architecture

LangChain is deliberately split so integrations release independently of core abstractions. `langchain-core` carries the base abstractions — messages, content blocks, runnables, base chat model and tool interfaces. `langchain` is the user-facing package holding agents and middleware. `langchain-classic` is the compatibility home for pre-1.0 constructs such as `LLMChain` and `ConversationChain`. Provider integrations live in separately versioned packages like `langchain-openai` and `langchain-anthropic`. `langchain-community` holds broader community integrations, and `langchain-text-splitters` is factored out for retrieval work.

The operational consequence: when something breaks in provider-specific tool calling or structured output, the bug and its fix almost always live in a provider package on its own release cadence, not in `langchain-core`. Full verified version matrix in `SH-01`.

## LC-01.4 — The v1 architectural shift

LangChain 1.0 represented a deliberate narrowing. The alpha announcement articulated the thesis directly: most use cases converge on a single pattern — "give an LLM access to tools, call it with input, execute any tool calls, and repeat until completion" — while genuinely custom workflows belong in LangGraph rather than in bespoke LangChain chain abstractions.

Three changes followed from that thesis. LangChain gained `create_agent` as the standard implementation of that loop. LangGraph gained a built-in agent runtime supplying durable execution, short-term memory, human-in-the-loop, and streaming. `langchain-core` gained structured content blocks via a `.content_blocks` property reflecting how modern LLM APIs actually return content (see `LC-02`). Backward compatibility was preserved by moving legacy constructs into `langchain-classic` rather than breaking them in place. **Tier 1** ([1.0 alpha announcement](https://www.langchain.com/blog/langchain-langchain-1-0-alpha-releases)).

## LC-01.5 — Documentation surfaces

LangChain consolidated its documentation into a unified site, replacing the older per-version `python.langchain.com/v0.X/...` structure. Narrative documentation lives at [docs.langchain.com](https://docs.langchain.com/), API reference at [reference.langchain.com](https://reference.langchain.com/), and the docs source is open at [langchain-ai/docs](https://github.com/langchain-ai/docs). Old versioned URLs now issue 302 redirects into the unified site rather than 404ing — confirmed by direct fetch during compilation.

A machine-readable index of the entire documentation set is published at `https://docs.langchain.com/llms.txt`, following the `llms.txt` convention. It enumerates the Build, OSS (Deep Agents, LangChain, LangGraph, Integrations), LangSmith, and Studio sections with `.md` URLs for each page — which makes it the correct entry point for anyone programmatically ingesting LangChain docs into a corpus or RAG index. LangChain also ships an open-source MCP server for serving exactly this kind of index; see `SH-03`.

## Sources

- [langchain-ai/langchain README](https://github.com/langchain-ai/langchain/blob/master/README.md) — accessed 2026-08-13 (Tier 1)
- [LangChain overview — official docs](https://docs.langchain.com/oss/python/langchain/overview) — accessed 2026-08-13 (Tier 1)
- [LangChain & LangGraph 1.0 alpha releases](https://www.langchain.com/blog/langchain-langchain-1-0-alpha-releases) — accessed 2026-08-13 (Tier 1)
- [LangChain v1 migration guide](https://docs.langchain.com/oss/python/migrate/langchain-v1) — accessed 2026-08-13 (Tier 1)
- [docs.langchain.com/llms.txt](https://docs.langchain.com/llms.txt) — accessed 2026-08-13 (Tier 1)
