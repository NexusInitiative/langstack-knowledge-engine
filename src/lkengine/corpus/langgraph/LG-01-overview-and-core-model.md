---
doc_id: LG-01
title: LangGraph — Overview & Core Model
series: LG
product: LangGraph
version_scope: langgraph 1.x (verified 1.2.11)
last_verified: 2026-08-13
source_tier: 1
tags: [overview, pregel, durable-execution, orchestration, positioning, case-studies]
---

# LG-01 — LangGraph Overview & Core Model

## LG-01.1 — What LangGraph is

LangGraph is a **low-level orchestration framework for constructing and managing stateful, long-running agents**, built by LangChain Inc. Where LangChain supplies the components and a standard agent loop, LangGraph supplies the runtime that makes an agent durable, inspectable, and resumable.

Its README frames five core capabilities: **durable execution** that persists through failures and resumes from the exact stopping point; **human-in-the-loop** oversight allowing inspection and modification of agent state mid-run; **comprehensive memory** combining short-term reasoning state with long-term persistence; **deep debugging** through LangSmith integration; and **production deployment infrastructure** for stateful workflows.

Install with `pip install -U langgraph`. Verified current version 1.2.11 across 276 releases (see `SH-01`). **Tier 1** ([README](https://github.com/langchain-ai/langgraph/blob/main/README.md)).

## LG-01.2 — Design lineage

LangGraph's execution model is explicitly inspired by **Pregel** and **Apache Beam** — Google's bulk-synchronous-parallel graph processing model and the unified batch/stream processing model respectively. This lineage explains behavior that otherwise looks surprising.

Execution proceeds in discrete **supersteps** rather than as free-form function calls. Within a superstep, all eligible nodes run; state updates are then applied together before the next superstep begins. This is why multiple nodes writing to the same state key concurrently require an explicit **reducer** to define how the writes combine — without one, LangGraph raises `InvalidUpdateError` rather than silently picking a winner (see `LG-03` and `SH-07`). It is also why checkpoints land at superstep boundaries, which is what makes clean resume possible.

## LG-01.3 — When LangGraph is the right tool

LangGraph is warranted when an agent needs cycles, retries, multi-turn autonomous decisions, multi-agent coordination, human approval gates, or time-travel debugging. LangChain's sequential composition is sufficient for linear pipelines — RAG, prompt chains, document processing — where steps execute in a predictable order.

The distinguishing capabilities against plain LangChain composition are built-in checkpointing with automatic state snapshots rather than manual memory serialization; native support for cycles rather than workarounds; visual time-travel debugging rather than limited runtime visibility; and hierarchical or parallel multi-agent orchestration rather than basic tool calling. **Tier 2** (consistent across multiple independent comparison sources).

An important nuance for anyone choosing between them: as of the 1.0 line this is **not an either/or decision**, because LangChain's `create_agent` runs on LangGraph. Using LangChain agents means using LangGraph whether or not you write graph code, and LangGraph concepts surface directly through `create_agent` parameters (see `LC-05`).

## LG-01.4 — Two authoring APIs

LangGraph offers two ways to express a workflow, and they are genuinely different programming models rather than syntactic variants.

The **Graph API** centers on `StateGraph` — you declare state, nodes, and edges, then compile. It supports visualization and gives explicit, inspectable structure. Documented in `LG-02` and `LG-03`.

The **Functional API** centers on the `@entrypoint` and `@task` decorators — you write ordinary Python control flow, and LangGraph handles durability around it. It does not support graph visualization because structure is determined at runtime. Documented in `LG-09`.

The choice has real consequences for checkpointing semantics, not just style, which is covered in `LG-09`.

## LG-01.5 — Production adoption

LangChain publishes a case-studies page listing 40+ companies using LangGraph, noting that entries are compiled from public sources. Named adopters span code generation (GitLab, Replit, Uber, Qodo, LinkedIn for text-to-SQL), financial services (J.P. Morgan, BlackRock, Modern Treasury), domain copilots (AppFolio, Klarna, Definely for legal, Komodo Health), customer support (Cisco, Prosper, City of Hope), search and research (Exa, Harmonic, Athena Intelligence, Morningstar), automation (AirTop, C.H. Robinson, 11x), and enterprise software (Infor, Elastic, Vodafone).

Treat this as evidence of production viability at scale, while noting it is a vendor-curated list from public mentions rather than an audited customer roster. **Tier 1 for the list's existence and contents; the page itself discloses its compilation method.**

## Sources

- [langchain-ai/langgraph README](https://github.com/langchain-ai/langgraph/blob/main/README.md) — accessed 2026-08-13 (Tier 1)
- [LangGraph case studies — official docs](https://docs.langchain.com/oss/python/langgraph/case-studies) — accessed 2026-08-13 (Tier 1)
- [LangGraph Graph API — official docs](https://docs.langchain.com/oss/python/langgraph/graph-api) — accessed 2026-08-13 (Tier 1)
- [LangGraph Platform GA announcement](https://www.langchain.com/blog/langgraph-platform-ga) — accessed 2026-08-13 (Tier 1)
