---
doc_id: LG-07
title: LangGraph — Human-in-the-Loop & Interrupts
series: LG
product: LangGraph
version_scope: langgraph 1.x
last_verified: 2026-08-13
source_tier: 1
tags: [interrupt, human-in-the-loop, HITL, Command, resume, breakpoints, idempotency, time-travel, gotchas]
---

# LG-07 — Human-in-the-Loop & Interrupts

## LG-07.1 — How interrupt() works

`interrupt()` pauses graph execution at any point inside a node, persisting state via the checkpointer. It accepts a JSON-serializable payload that surfaces to the caller — typically the question or proposed action a human must review.

Execution resumes by invoking the graph with `Command(resume=value)`, where `value` becomes the return value of the original `interrupt()` call. Resuming **requires the same `thread_id`** used when the interrupt occurred; the documentation states this as a hard requirement.

A checkpointer is mandatory. Interrupts are built on persistence, so a graph compiled without one cannot pause and resume. **Tier 1** ([interrupts docs](https://docs.langchain.com/oss/python/langgraph/interrupts)).

## LG-07.2 — The single most important gotcha: nodes restart from the beginning

The documentation states it plainly: on resume, **"the runtime restarts the entire node from the beginning — it does not resume from the exact line where interrupt was called."**

Everything else in this document follows from that sentence. Any code that ran before the `interrupt()` call **executes again** on resume. If a node charges a credit card, sends an email, or writes a record before pausing for approval, that side effect happens twice.

The remedies are ordered by preference: move non-idempotent side effects into a **separate upstream node** that completes before the interrupting node begins; or place them **after** the `interrupt()` call; or make them genuinely idempotent. Splitting into a separate node is the most robust, because it removes the replay window entirely rather than relying on correct idempotency.

## LG-07.3 — Never wrap interrupt() in try/except

Per the documentation: "If you wrap the interrupt call in a try/except block, you will catch this exception and the interrupt will not be passed back to the graph."

`interrupt()` signals by raising an internal control-flow exception — `GraphInterrupt`, one of the internal exceptions listed in `SH-07` as not intended for user code to catch. A broad `except Exception` anywhere in the call path silently disables the interrupt. This is a particularly nasty failure because the code appears to run fine; it simply never pauses.

## LG-07.4 — Interrupt ordering and loops

Two further constraints follow from node-restart semantics.

**Ordering matters.** The documentation notes that "the order of interrupt calls within the node is important" because resume values are matched to interrupts by index. Conditional interrupts, or interrupts inside non-deterministic loops, break that index correspondence and mismatch resume values to interrupts.

**Loops are worse than they look.** A `while` loop calling `interrupt()` repeatedly causes each resume to replay all previous iterations — "the first resume replays 1 iteration, the second replays 2, and so on." This is quadratic replay, and it is a documented anti-pattern rather than a bug.

The documented alternative for validation loops is to **store the re-prompt state and use a conditional edge to route back into the node**, so each pass is a fresh node execution rather than a deeper loop iteration. This is a concrete case where `add_conditional_edges` is preferred over in-node control flow (see `LG-02`).

## LG-07.5 — The @task caching trap in server deployments

A documented community finding worth flagging: `@task`-decorated functions can re-execute non-deterministic code on resume even when a checkpointer is configured, specifically in LangGraph API Server deployments.

The mechanism is a compile-time versus runtime mismatch. Node-level checkpointing uses the runtime-injected checkpointer that the API Server supplies, but **task-level checkpointing resolves its checkpointer at compile time.** When you compile without a checkpointer — which is the normal pattern for API Server deployment, since the server injects one — `schedule_task` cannot find it and re-runs the wrapped function instead of reusing its cached result.

Reported remedies, in order of robustness: split non-deterministic code into its own node completed before the interrupt; keep all pre-interrupt code idempotent; order interrupts before non-deterministic operations; or use the Functional API's `@entrypoint` with a compile-time checkpointer. The general lesson stated by the author — **test HITL workflows end-to-end in the deployment environment, not only locally** — is reinforced by the separate `langgraph dev` checkpointer issue in `SH-08`. **Tier 2**: single-author account, but the mechanism it describes is consistent with the officially documented node-restart and runtime-injection behavior.

## LG-07.6 — Breakpoints, time travel and agent-level HITL

Beyond `interrupt()`, LangGraph supports **static breakpoints** through `interrupt_before` and `interrupt_after` at compile time, and conditional pausing via `NodeInterrupt`.

**Time travel** builds on `get_state_history` (see `LG-04`): past checkpoints can be replayed, and execution can be forked from any of them to explore an alternative path. This is the debugging capability most often cited as a reason to choose LangGraph over plain chain composition.

At the LangChain agent level, this machinery is packaged as **`HumanInTheLoopMiddleware`**, which pauses for approval of specified tool calls (see `LC-06`), and in Deep Agents as the **`interrupt_on`** parameter (see `LC-08`). Both inherit every caveat in this document — particularly node restart on resume.

## Sources

- [Interrupts — official docs](https://docs.langchain.com/oss/python/langgraph/interrupts) — accessed 2026-08-13 (Tier 1)
- [LangGraph HITL: the task caching gotcha](https://dev.to/rigby_/langgraph-hitl-the-task-caching-gotcha-that-cost-me-3-days-1g0j) — accessed 2026-08-13 (Tier 2)
- [LangGraph cheatsheet: troubleshooting & debugging](https://sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/troubleshooting-debugging/) — accessed 2026-08-13 (Tier 2)
- [Prebuilt middleware — official docs](https://docs.langchain.com/oss/python/langchain/middleware/built-in) — accessed 2026-08-13 (Tier 1)
