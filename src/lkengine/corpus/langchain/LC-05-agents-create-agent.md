---
doc_id: LC-05
title: LangChain — Agents (create_agent)
series: LC
product: LangChain
version_scope: langchain 1.x
last_verified: 2026-08-13
source_tier: 1
tags: [create_agent, agent-loop, checkpointer, store, context_schema, state_schema, migration, AgentExecutor, create_react_agent]
---

# LC-05 — Agents: create_agent

## LC-05.1 — What create_agent is

`create_agent` is LangChain 1.x's standard agent constructor, living at `langchain.agents.create_agent`. It implements the convergent agent pattern LangChain identified as covering most use cases: give a model tools, call it, execute any tool calls, feed results back, and repeat until the model stops requesting tools.

It is built on the LangGraph runtime. This is the principal intersection point between the two products — LangGraph concepts including checkpointers, stores, interrupts, and streaming are exposed directly through `create_agent` parameters, and an agent produced by it can be embedded as a node inside a larger `StateGraph`. **Tier 1** ([agents docs](https://docs.langchain.com/oss/python/langchain/agents)).

## LC-05.2 — Parameters

The documented parameters are:

- **`model`** — a `"provider:model"` string such as `"anthropic:claude-sonnet-4-6"`, or an initialized model instance for dynamic configuration.
- **`tools`** — Python callables, LangChain tools, or tool dicts (see `LC-03`).
- **`system_prompt`** — a string or `SystemMessage` shaping behavior.
- **`middleware`** — a list of middleware controlling execution, context, planning, fault tolerance, guardrails, and steering (see `LC-06`).
- **`response_format`** — a schema for structured output, surfacing at the `'structured_response'` state key (see `LC-04`).
- **`checkpointer`** — persists conversation history across turns, e.g. `InMemorySaver()` (see `LG-04`).
- **`store`** — the long-term, cross-thread persistence layer (see `LG-05`).
- **`context_schema`** — a dataclass defining the shape of per-run configuration.
- **`state_schema`** — a custom `AgentState` subclass adding fields to the agent's state.
- **`name`** — an identifier, used when composing multi-agent systems.

## LC-05.3 — The agent loop and execution surfaces

The core loop repeats until the task completes: the model generates tool calls, tools execute, results are fed back into context, and the model processes those results and decides the next action.

`agent.invoke()` runs synchronously and returns the final state dictionary. For intermediate progress, use `agent.stream_events()` with **`version="v3"`**, which surfaces events as they emit. The v3 version parameter is the currently documented event-stream contract for agents; note that the LangGraph `.stream()` API documents a separate `version="v2"` unified `StreamPart` format for graph-level streaming (see `LG-06`) — these are different surfaces with independently versioned formats, which is a genuine source of confusion when reading mixed-vintage tutorials.

## LC-05.4 — Context and state customization

`context_schema` and `state_schema` serve different purposes and are frequently confused. **`context_schema`** describes *per-run configuration* — values supplied when a run starts, such as a user ID or tenant, that the agent reads but does not evolve. **`state_schema`** extends the agent's *evolving state* by subclassing `AgentState`, adding fields that nodes and tools read and write as the run progresses. Configuration goes in context; accumulating working data goes in state.

## LC-05.5 — Migration from earlier agent APIs

The official v1 migration guide states the current recommendation directly: *"Prior to v1.0, we recommended using `langgraph.prebuilt.create_react_agent` to build agents. Now, we recommend you use `langchain.agents.create_agent`."* That is the authoritative migration path for anyone on `create_react_agent`.

For older constructs, the guide directs users of legacy chains — `LLMChain`, `ConversationChain`, and similar — to install **`langchain-classic`** and update their imports rather than expecting them in `langchain`.

**A specific claim to treat with caution:** several third-party comparison articles state that `AgentExecutor` has an end-of-life date of December 2026. That date could **not** be corroborated in LangChain's official v1 migration guide or the LangChain overview page, neither of which states an explicit `AgentExecutor` sunset. The direction of travel is unambiguous — `AgentExecutor` and the legacy agent types are superseded by `create_agent` — but the specific date is **Tier 3 and unverified**. Do not plan a hard migration deadline around it without confirming against current official documentation. This is discussed further in `SH-02`.

## LC-05.6 — Multi-agent composition

Agents compose in two documented ways. The **supervisor pattern** has a coordinating agent route work to specialists; LangChain publishes both a tutorial and a packaged implementation as `langgraph-supervisor` (see `SH-09`). The **subagent pattern** uses `SubAgentMiddleware` to let an agent spawn and delegate to subagents, and is the model Deep Agents builds on via its `task` tool (see `LC-08`).

Because `create_agent` produces a LangGraph graph, an agent can also simply be added as a node in a parent `StateGraph`. The documentation confirms that when an agent is embedded this way, "every middleware hook continues to run" — middleware is not bypassed by nesting. Subgraph mechanics and their checkpointer caveats are in `LG-08`.

## Sources

- [Agents — official docs](https://docs.langchain.com/oss/python/langchain/agents) — accessed 2026-08-13 (Tier 1)
- [LangChain v1 migration guide](https://docs.langchain.com/oss/python/migrate/langchain-v1) — accessed 2026-08-13 (Tier 1)
- [LangChain overview](https://docs.langchain.com/oss/python/langchain/overview) — accessed 2026-08-13 (Tier 1)
- [Middleware — official docs](https://docs.langchain.com/oss/python/langchain/middleware) — accessed 2026-08-13 (Tier 1)
