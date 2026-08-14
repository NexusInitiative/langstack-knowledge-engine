---
doc_id: LG-08
title: LangGraph — Subgraphs
series: LG
product: LangGraph
version_scope: langgraph 1.x
last_verified: 2026-08-13
source_tier: 1
tags: [subgraphs, checkpointer-modes, shared-state, namespace-isolation, multi-agent, parallel-conflicts]
---

# LG-08 — Subgraphs

## LG-08.1 — What a subgraph is

A subgraph is a compiled graph used as a node inside another graph. It is LangGraph's modularity mechanism — the way to build reusable workflow components and to compose multi-agent systems, since an agent produced by `create_agent` is itself a graph that can be nested (see `LC-05`).

**Tier 1** ([subgraphs docs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)).

## LG-08.2 — Two communication patterns

How a subgraph is attached depends on whether it shares state keys with its parent.

**Shared state schema — direct attachment.** When parent and subgraph share state keys, pass the compiled subgraph straight to `add_node()`. It reads from and writes to the parent's channels automatically, with no adapter code.

**Different state schemas — wrapper function.** When they share no keys, invoke the subgraph inside a node function that transforms state in both directions: parent state into subgraph input, then subgraph output back into parent state updates.

The wrapper pattern is preferable for genuine encapsulation even when a shared schema would work, because it keeps the subgraph's internal state private and makes the interface explicit.

## LG-08.3 — The three checkpointer modes

Subgraphs take a `checkpointer` argument with three meaningfully different behaviors. This is the highest-value detail in this document, because the modes are easy to confuse and the failure modes differ sharply.

**`None` (default) — per-invocation.** Each call starts fresh and inherits the parent's checkpointer, which supports interrupts and durable execution *within* a single call. This is the documented recommendation for most use cases.

**`True` — per-thread.** State accumulates across calls on the same thread, so a subagent retains multi-turn memory of its own.

**`False` — stateless.** No checkpointing overhead; the subgraph behaves like a plain function with no pause/resume capability.

A prerequisite spans all three: **the parent graph must be compiled with a checkpointer** for subgraph persistence features to work at all.

## LG-08.4 — Documented caveats

Four caveats attach to subgraph usage, and the first two have caused real production bugs.

**Per-thread subgraphs conflict under parallel invocation.** Multiple simultaneous calls to the same per-thread subgraph cause checkpoint conflicts. The documented remedy is `ToolCallLimitMiddleware` to prevent parallel invocation (see `LC-06`).

**Multiple per-thread subagents need namespace isolation.** When calling several different per-thread subagents, wrap each in its own `StateGraph` with a unique node name so their checkpoints stay stable and separate.

**State inspection requires statefulness.** Stateless subgraphs (`checkpointer=False`) save no checkpoints, so state inspection and time travel do not apply to them.

**Streaming requires explicit opt-in.** Subgraph output appears in a stream only with `subgraphs=True`, and the `stream.subgraphs` projection is the recommended way to observe nested runs without parsing namespace strings (see `LG-06`).

## LG-08.5 — A verified historical bug worth knowing

Issue [#3206](https://github.com/langchain-ai/langgraph/issues/3206) — verified **closed** — documented a concrete failure at the intersection of subgraphs, checkpointers, and interrupts, and it illustrates why the mode semantics in `LG-08.3` matter.

A parent graph looped and invoked a subgraph until a counter reached a limit; the subgraph used interrupts for human feedback and was configured with `checkpointer=True`. After the first interrupt resumed, the subgraph never re-executed its counter node. The parent counter stuck at 1, the parent node re-executed repeatedly, and the run eventually died with a recursion-limit error. Removing `checkpointer=True` from the subgraph resolved it. Reported January 2025 against LangGraph 0.2.67.

The diagnostic pattern generalizes: **a `GraphRecursionError` in a parent graph containing a per-thread subgraph is a signal to examine the subgraph's checkpointer mode**, because a subgraph that silently stops advancing looks like a parent-side infinite loop.

## LG-08.6 — Subgraphs in multi-agent design

Subgraphs are the substrate for LangGraph multi-agent patterns. The **supervisor pattern** — a coordinator routing work to specialist agents — has both an official tutorial and a packaged implementation in `langgraph-supervisor` (see `SH-09`). The **subagent pattern** is exposed at the LangChain layer as `SubAgentMiddleware` and in Deep Agents as the built-in `task` tool (see `LC-08`).

When composing agents this way, the per-thread parallel-invocation conflict in `LG-08.4` is the constraint most likely to bite, since fan-out to several specialists at once is exactly the design multi-agent systems invite.

## Sources

- [Use subgraphs — official docs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs) — accessed 2026-08-13 (Tier 1)
- [Issue #3206 — subgraph checkpointer=True causes subgraph to be skipped](https://github.com/langchain-ai/langgraph/issues/3206) — verified closed, accessed 2026-08-13 (Tier 1)
- [Prebuilt middleware — official docs](https://docs.langchain.com/oss/python/langchain/middleware/built-in) — accessed 2026-08-13 (Tier 1)
- [langgraph-supervisor-py](https://github.com/langchain-ai/langgraph-supervisor-py) — accessed 2026-08-13 (Tier 1)
