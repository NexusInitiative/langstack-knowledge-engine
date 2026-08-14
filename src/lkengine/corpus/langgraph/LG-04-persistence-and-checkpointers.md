---
doc_id: LG-04
title: LangGraph — Persistence & Checkpointers
series: LG
product: LangGraph
version_scope: langgraph 1.x, langgraph-checkpoint 4.x
last_verified: 2026-08-13
source_tier: 1
tags: [checkpointer, persistence, thread_id, InMemorySaver, SqliteSaver, PostgresSaver, get_state, TTL, connection-pool]
---

# LG-04 — Persistence & Checkpointers

## LG-04.1 — What a checkpointer does

A checkpointer persists a thread's graph state as **checkpoints**, written at the end of each superstep. This is what provides short-term, thread-scoped memory and what makes durable execution, resume-after-failure, human-in-the-loop, and time travel possible.

The single most important operational fact, stated in LangChain's support documentation: **checkpoints are written to the configured database, not held in pod memory.** After a run completes, application state is cleaned up from memory. Consequently, high pod memory in a deployment indicates large objects or a leak in your node code — not checkpoint accumulation. This corrects a common misdiagnosis. **Tier 1** ([checkpointers support article](https://support.langchain.com/articles/6253531756-understanding-checkpointers-databases-api-memory-and-ttl)).

## LG-04.2 — Checkpointer implementations

Four backends are documented, each in its own package (versions per `SH-01`):

- **`InMemorySaver`** — RAM-backed, for development and tests.
- **`SqliteSaver`** — local file-based storage for development.
- **`PostgresSaver`** / **`AsyncPostgresSaver`** — PostgreSQL, the production default.
- Additional backends exist for **MongoDB** and **Redis**.

The documentation is explicit about the in-memory caveat: "`MemorySaver` and `InMemorySaver` store checkpoints in RAM. When the process restarts, all checkpoints are lost." Database-backed savers require calling **`setup()`** once to create their schema.

**Security note:** several checkpoint backends carried CVEs — SQL injection in the SQLite saver, namespace boundary crossing in the Postgres and SQLite stores, NoSQL injection in the JS MongoDB saver, and pickle-fallback RCE in `langgraph-checkpoint` itself. Minimum safe versions are in `SH-06`. Do not deploy a checkpoint backend without checking that register.

## LG-04.3 — Threads and thread_id

A **thread** is the unit of conversational scope. Checkpoints are grouped by a `thread_id` passed in the graph config:

```python
config = {"configurable": {"thread_id": "user-123-session-7"}}
graph.invoke(input, config)
```

Same `thread_id` continues a conversation; a new one starts fresh. The documentation gives a concrete constraint: **keep `thread_id` values under 255 characters** to avoid database errors.

A `thread_id` is **not a security boundary on its own.** CVE-2026-48121 demonstrated NoSQL operator injection through `config.configurable` identifier fields reaching other tenants' checkpoints, and CVE-2026-71433 showed namespace prefix matching crossing tenant boundaries. Multi-tenant deployments must enforce authorization above the checkpointer. See `SH-06`.

## LG-04.4 — Inspecting and modifying state

Three methods form the state-inspection API. **`graph.get_state(config)`** returns the current `StateSnapshot` for a thread. **`graph.get_state_history(config)`** returns the sequence of past checkpoints — the basis for time travel. **`graph.update_state(...)`** writes state directly, which is how a human edit is applied before resuming.

Thread deletion is available as **`checkpointer.delete_thread(thread_id)`**.

Two documented hazards attach to this API, both async-related. Using an async checkpointer with a synchronous `invoke` or `get_state` causes the program to **hang** rather than error ([#1800](https://github.com/langchain-ai/langgraph/issues/1800)), and `get_state_history` with an async `BaseCheckpointSaver` has been reported to hang similarly ([#2992](https://github.com/langchain-ai/langgraph/issues/2992)). Silent hangs are the characteristic failure signature of sync/async mismatch here — keep the two consistent across a graph.

## LG-04.5 — Database growth, TTL and durability

Checkpoints accumulate. Per the support documentation, "Database usage grows when many runs are executed" and grows faster when "checkpoints include large application state." Without intervention, "database tables grow indefinitely (unless you manually delete resources)."

Three documented controls exist. **TTL** automatically expires old checkpoints and is configurable in `langgraph.json` (see `LG-10`). The **`"exit"` durability mode** skips intermediate checkpoints, persisting only at completion. And the **external storage pattern** keeps large files in S3 or similar with only a reference in state.

The tradeoff is explicit: `"exit"` reduces write volume and storage but sacrifices mid-run resumability, since there are no intermediate checkpoints to resume from. Choose it for short deterministic runs, not for long human-in-the-loop workflows.

## LG-04.6 — Connection management for long-running work

For long-running workflows, the documented guidance is to use a **`ConnectionPool`** rather than a raw database connection, to avoid timeout errors when a run outlives a single connection's lifetime. This is a frequent source of production Postgres failures that looks like a LangGraph bug but is a connection-lifecycle problem.

Related reported issues in this area include async Postgres persistence errors ([#2609](https://github.com/langchain-ai/langgraph/issues/2609)), `setup()` failing against a fresh database ([#2570](https://github.com/langchain-ai/langgraph/issues/2570)), an `undefined table 'checkpoints'` condition ([#2062](https://github.com/langchain-ai/langgraph/issues/2062)), incomplete Postgres setup documentation ([#4937](https://github.com/langchain-ai/langgraph/issues/4937)), and Postgres/Redis checkpointers failing inside constrained runtimes such as Cloudflare Workers ([langgraphjs #1692](https://github.com/langchain-ai/langgraphjs/issues/1692)).

## Sources

- [Persistence — official docs](https://docs.langchain.com/oss/python/langgraph/persistence) — accessed 2026-08-13 (Tier 1)
- [Add memory — official docs](https://docs.langchain.com/oss/python/langgraph/add-memory) — accessed 2026-08-13 (Tier 1)
- [Understanding Checkpointers, Databases, API Memory and TTL](https://support.langchain.com/articles/6253531756-understanding-checkpointers-databases-api-memory-and-ttl) — accessed 2026-08-13 (Tier 1)
- GitHub issues [#1800](https://github.com/langchain-ai/langgraph/issues/1800), [#2992](https://github.com/langchain-ai/langgraph/issues/2992), [#2609](https://github.com/langchain-ai/langgraph/issues/2609), [#2570](https://github.com/langchain-ai/langgraph/issues/2570), [#2062](https://github.com/langchain-ai/langgraph/issues/2062), [#4937](https://github.com/langchain-ai/langgraph/issues/4937), [langgraphjs #1692](https://github.com/langchain-ai/langgraphjs/issues/1692) — accessed 2026-08-13 (Tier 1)
