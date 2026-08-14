---
doc_id: LG-09
title: LangGraph — Functional API & Durable Execution
series: LG
product: LangGraph
version_scope: langgraph 1.x
last_verified: 2026-08-13
source_tier: 1
tags: [functional-api, entrypoint, task, durable-execution, determinism, replay, checkpointing, Pregel]
---

# LG-09 — Functional API & Durable Execution

## LG-09.1 — The Functional API in one paragraph

The Functional API lets you write a durable workflow as ordinary Python — normal `if` statements and `for` loops — instead of declaring a graph. Two decorators do the work. **`@entrypoint`** marks the workflow entry point, managing execution flow, long-running tasks, and interrupts; the decorated function takes a single positional argument and returns a `Pregel` instance. **`@task`** wraps a discrete unit of work such as an API call, executing it asynchronously and returning a future-like object resolved with `.result()` or `await`.

**Tier 1** ([Functional API docs](https://docs.langchain.com/oss/python/langgraph/functional-api)).

## LG-09.2 — How it differs from the Graph API

The two APIs differ on four axes that matter in practice.

**Control flow.** The Functional API uses standard Python constructs; the Graph API requires explicit structural declaration through nodes and edges.

**State management.** Functional state is function-scoped with no explicit reducers; the Graph API requires a State schema and reducer definitions (see `LG-03`).

**Checkpointing granularity.** This is the substantive difference: the Functional API **saves task results into an existing checkpoint**, whereas the Graph API **creates a new checkpoint after each superstep.**

**Visualization.** The Graph API supports graph visualization for debugging. The Functional API does not, because its structure is determined at runtime rather than declared.

Choose the Functional API when you want "minimal changes to your existing code" and standard language primitives for branching — the documentation specifically recommends it for human-in-the-loop interactions, parallel I/O, and straightforward sequential logic. Choose the Graph API when structure, visualization, and explicit state modeling are worth the ceremony.

## LG-09.3 — Determinism is a hard requirement

Durable execution works by replay. On resume with a checkpointer, execution **replays from the entrypoint start** while restoring the outputs of already-completed tasks rather than recomputing them.

This makes determinism a correctness requirement, not a style preference. The documented rules are: encapsulate side effects and non-deterministic operations inside `@task` functions; ensure all inputs and outputs are JSON-serializable; and place randomness and API calls in tasks so replay is deterministic.

Code that generates a random value or reads live data **outside** a task will produce a different value on replay, silently diverging the resumed run from the original. This is the same hazard as the node-restart behavior in `LG-07`, expressed in a different API.

`entrypoint.final[return_type, save_type]` decouples what is saved into the checkpoint from what is returned to the caller, which is useful when the value you want to persist differs from the value you want to hand back.

## LG-09.4 — The compile-time versus runtime checkpointer trap

The most consequential reported issue with `@task` concerns deployment. Task-level checkpointing resolves its checkpointer **at compile time**, while the LangGraph API Server injects a checkpointer **at runtime**.

The result: a graph compiled without a checkpointer — the normal pattern for API Server deployment — leaves `schedule_task` unable to find one, so tasks re-execute instead of returning cached results. Non-deterministic work inside those tasks then produces different values on resume, breaking workflow consistency in a way that does not reproduce locally.

Reported remedies: split non-deterministic code into a separate node completed before any interrupt; keep pre-interrupt code idempotent; order interrupts before non-deterministic operations; use `@entrypoint` with a compile-time checkpointer; or build a custom deployment with full checkpointer control. **Tier 2** — a single-author account, but consistent with the officially documented replay semantics above. Cross-referenced in `LG-07`.

## LG-09.5 — Durability modes (verified)

LangGraph exposes a `durability` setting controlling how often state is persisted. The type is confirmed from the API reference as **`langgraph.types.Durability = Literal['sync', 'async', 'exit']`** — exactly three values.

Ordered from least to most durable, per LangChain's own framing:

- **`"exit"`** — fastest; checkpoints **only at the end** of the run. Independently confirmed in LangChain's support documentation as the remedy for excessive checkpoint database growth (see `LG-04`).
- **`"async"`** — checkpoints written asynchronously, so execution proceeds without blocking on the persistence write.
- **`"sync"`** — checkpoints written synchronously before execution continues; most durable, highest write cost.

The tradeoff is a barrier-latency-versus-loss-window choice. `"exit"` gives fewer writes and less storage but no intermediate checkpoint to resume from, so a mid-run failure restarts from the beginning — which also means **`"exit"` is wrong for long human-in-the-loop workflows**, since interrupts depend on intermediate checkpoints existing (`LG-07`). `"sync"` gives the smallest loss window at the highest cost. `"async"` is the middle position.

`AC-03.3` frames these as policies about what happens at the bulk-synchronous barrier, which is the clearest way to reason about why exactly three modes exist.

**Correction note:** an earlier revision of this corpus confirmed only `"exit"` and flagged `"async"` and `"sync"` as unverified. All three are now confirmed Tier 1 from [`langgraph.types.Durability`](https://reference.langchain.com/python/langgraph/types/Durability). The narrative dedicated durable-execution docs page remained partially unretrievable, so the per-mode descriptions above combine the Tier 1 type definition with LangChain's public least-to-most-durable ordering (Tier 2).

## LG-09.6 — Choosing between the APIs

A practical decision rule. Use the **Graph API** when the workflow has genuine branching structure worth seeing, when multiple nodes write shared state and reducers express real merge semantics, or when visualization and time-travel debugging matter. Use the **Functional API** when the logic is naturally sequential Python, when you are adding durability to existing code rather than designing a new topology, or when the graph would be a straight line with extra ceremony.

Both compile to the same Pregel runtime, so the choice is about expressiveness and checkpoint granularity, not capability.

## Sources

- [Functional API — official docs](https://docs.langchain.com/oss/python/langgraph/functional-api) — accessed 2026-08-13 (Tier 1)
- [Persistence — official docs](https://docs.langchain.com/oss/python/langgraph/persistence) — accessed 2026-08-13 (Tier 1)
- [Understanding Checkpointers, Databases, API Memory and TTL](https://support.langchain.com/articles/6253531756-understanding-checkpointers-databases-api-memory-and-ttl) — accessed 2026-08-13 (Tier 1)
- [langgraph.types.Durability API reference](https://reference.langchain.com/python/langgraph/types/Durability) — accessed 2026-08-13 (Tier 1)
- [langgraph-sdk Durability schema](https://reference.langchain.com/python/langgraph-sdk/schema/Durability) — accessed 2026-08-13 (Tier 1)
- [LangGraph HITL: the task caching gotcha](https://dev.to/rigby_/langgraph-hitl-the-task-caching-gotcha-that-cost-me-3-days-1g0j) — accessed 2026-08-13 (Tier 2)
