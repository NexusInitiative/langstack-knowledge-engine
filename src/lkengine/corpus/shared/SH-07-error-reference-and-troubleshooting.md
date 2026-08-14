---
doc_id: SH-07
title: Error Reference & Troubleshooting
series: SH
product: both
version_scope: langgraph 1.x
last_verified: 2026-08-13
source_tier: 2
tags: [errors, troubleshooting, GraphRecursionError, InvalidUpdateError, EmptyChannelError, debugging, ErrorCode, serialization]
---

# SH-07 — Error Reference & Troubleshooting

## SH-07.1 — LangGraph exception reference

Five user-facing exceptions are documented, each with a characteristic cause and fix.

**`GraphRecursionError`** — the graph exceeded its maximum recursion depth, typically from an unterminated loop. The correct response is to fix the termination condition; raising `recursion_limit` should be a last resort, because it converts a logic bug into a slower, more expensive logic bug. A specific diagnostic from `LG-08`: if the graph contains a per-thread subgraph, check that subgraph's checkpointer mode, since a subgraph that silently stops advancing presents as a parent-side infinite loop.

**`InvalidUpdateError`** — an update targeted an incompatible channel type, a non-existent channel, or, most commonly, two concurrent nodes wrote the same state key with no reducer. The fix is a reducer via `Annotated` (see `LG-03`).

**`EmptyChannelError`** — a channel was read before anything wrote to it. Initialize with a default or check `is_available()` first.

**`EmptyInputError`** — the graph was invoked with `None` or an empty dict where input is required.

**`TaskNotFound`** — in distributed execution, a referenced task ID does not exist or was already processed. Verify existence and make operations idempotent.

Four further exceptions — **`GraphInterrupt`**, **`GraphBubbleUp`**, **`ParentCommand`**, and **`NodeInterrupt`** — are internal control-flow signals **not intended to be caught by user code.** This is the mechanism behind the try/except prohibition in `LG-07`: a broad `except Exception` swallows `GraphInterrupt` and silently disables human-in-the-loop.

A standardized `ErrorCode` enum carries values including `GRAPH_RECURSION_LIMIT`, `INVALID_CONCURRENT_GRAPH_UPDATE`, `INVALID_GRAPH_NODE_RETURN_VALUE`, `MULTIPLE_SUBGRAPHS`, and `INVALID_CHAT_HISTORY`, with `create_error_message()` formatting errors alongside documentation links. **Tier 2** — sourced from a third-party mirror of the 1.0.0 error documentation; the `ErrorCode` values are consistent with names referenced in official docs, but the table was not read from the `langchain-ai/langgraph` source tree directly.

## SH-07.2 — Silent failures: the ones that cost the most time

Several documented failure modes produce **no exception at all**, which makes them disproportionately expensive. Collecting them in one place is the most useful thing this document does.

**Program hangs instead of erroring** when an async checkpointer is used with synchronous `invoke` or `get_state`, or with `get_state_history` ([#1800](https://github.com/langchain-ai/langgraph/issues/1800), [#2992](https://github.com/langchain-ai/langgraph/issues/2992)). A hang is the signature of sync/async mismatch in persistence.

**Interrupts silently stop working** when `interrupt()` is wrapped in try/except — the code runs, it just never pauses (`LG-07`).

**Side effects run twice** on resume, because nodes restart from the beginning rather than resuming mid-function (`LG-07`).

**Tools silently vanish** when `.bind(tools=[...])` is followed by `.with_structured_output(schema)`; you get valid JSON while the model hallucinates instead of calling the tool ([#35320](https://github.com/langchain-ai/langchain/issues/35320), verified open).

**Tasks silently re-execute** on resume in API Server deployments because task checkpointing resolves at compile time while the server injects at runtime (`LG-09`).

**Local persistence silently differs from production** — `langgraph dev` was documented forcing in-memory storage regardless of configuration ([#5790](https://github.com/langchain-ai/langgraph/issues/5790), verified closed, but test the class of problem).

## SH-07.3 — Common non-silent errors

**Type errors** mean state does not match the declared schema — verify with type hints and inspect node inputs and outputs.

**API key errors** require checking environment variables, key validity, and provider permissions.

**Serialization errors** occur when state is not JSON-serializable, which checkpointing requires. Prefer Pydantic `BaseModel` over arbitrary Python objects (see `LG-02`).

**Database timeout errors** in long-running workflows point to raw connections rather than a `ConnectionPool` (see `LG-04`).

**`thread_id` database errors** may be length-related; keep values under 255 characters.

## SH-07.4 — Debugging toolkit

Four techniques, roughly in order of reach.

**Breakpoints** — `interrupt_before` and `interrupt_after` at compile time for static pauses, `NodeInterrupt` for conditional pausing.

**Time travel** — replay past executions from `get_state_history` and fork from any checkpoint to explore alternative paths (see `LG-04`).

**LangSmith tracing** — visual traces showing node timings, state transitions, and error locations, linking failures to specific nodes and state (see `SH-05`).

**Structured logging and stream modes** — the `debug` stream mode combines `checkpoints` and `tasks` with extra metadata, and `updates` shows exactly what each node wrote (see `LG-06`).

For stack traces, follow the call chain to identify the failing node and distinguish node-level errors from graph-execution errors — the two have different fixes.

## SH-07.5 — A diagnostic decision path

A compact triage order. If the program **hangs**, suspect sync/async checkpointer mismatch first. If you get **`InvalidUpdateError`**, add a reducer to the contended key. If you get **`GraphRecursionError`**, check termination conditions, then subgraph checkpointer modes. If **side effects duplicate**, examine code placement relative to `interrupt()`. If **structured output looks right but behavior is wrong**, check for tool bindings dropped by `with_structured_output`. If **persistence works locally but not deployed**, or vice versa, investigate compile-time versus runtime checkpointer resolution. If **streaming misbehaves**, isolate the exact combination of sync/async, subgraphs, mode count, and callbacks before searching issues (see `LG-06`).

## Sources

- [LangGraph errors reference](https://tessl.io/registry/tessl/pypi-langgraph/1.0.0/files/docs/errors.md) — accessed 2026-08-13 (Tier 2)
- [LangGraph cheatsheet: troubleshooting & debugging](https://sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/troubleshooting-debugging/) — accessed 2026-08-13 (Tier 2)
- [Interrupts — official docs](https://docs.langchain.com/oss/python/langgraph/interrupts) — accessed 2026-08-13 (Tier 1)
- [Persistence — official docs](https://docs.langchain.com/oss/python/langgraph/persistence) — accessed 2026-08-13 (Tier 1)
- [Understanding Checkpointers, Databases, API Memory and TTL](https://support.langchain.com/articles/6253531756-understanding-checkpointers-databases-api-memory-and-ttl) — accessed 2026-08-13 (Tier 1)
- GitHub issues [#1800](https://github.com/langchain-ai/langgraph/issues/1800), [#2992](https://github.com/langchain-ai/langgraph/issues/2992), [#35320](https://github.com/langchain-ai/langchain/issues/35320), [#5790](https://github.com/langchain-ai/langgraph/issues/5790) — accessed 2026-08-13 (Tier 1)
