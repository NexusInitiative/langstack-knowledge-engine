---
doc_id: LG-02
title: LangGraph — Graph API (StateGraph, nodes, edges)
series: LG
product: LangGraph
version_scope: langgraph 1.x
last_verified: 2026-08-13
source_tier: 1
tags: [StateGraph, add_node, add_edge, add_conditional_edges, START, END, compile, input_schema, output_schema, parallel]
---

# LG-02 — Graph API: StateGraph, Nodes & Edges

## LG-02.1 — StateGraph is the entry point

`StateGraph` is described in the documentation as "the main graph class to use." It is parameterized by a user-defined State object, and the construction sequence is always the same: define state, add nodes, add edges, then call `.compile()`.

The documentation is emphatic on the last step: **"You MUST compile your graph before you can use it."** `.compile()` validates structure and accepts runtime arguments including checkpointers and breakpoints. An uncompiled builder is not runnable. **Tier 1** ([Graph API docs](https://docs.langchain.com/oss/python/langgraph/graph-api)).

## LG-02.2 — Defining state

State may be declared as a `TypedDict`, a `dataclass`, or a Pydantic `BaseModel`. The schema defines the input and output structure shared by all nodes and edges.

Separate `input_schema` and `output_schema` may be specified to constrain what the graph accepts and returns while keeping richer internal state private. This is the clean way to avoid leaking working state to callers — internal scratch fields stay out of the public contract.

Pydantic `BaseModel` is worth preferring when state must survive checkpointing, because checkpointed state must be JSON-serializable and Pydantic models give you validated, serializable structures rather than arbitrary Python objects. Serialization failures at checkpoint time are a documented error class (see `SH-07`).

## LG-02.3 — Nodes

Nodes are functions accepting `state`, plus optional `config` and `runtime` parameters. They are registered with `builder.add_node(name, function)`.

The `runtime` parameter is how a node reaches the `Store` for long-term memory (`LG-05`) and the stream writer for custom streaming (`LG-06`). The `config` parameter carries the `configurable` dictionary including `thread_id`.

A node returns a partial state update — a dict of the keys it wants to change — not the whole state. How that update merges is governed by reducers (`LG-03`).

## LG-02.4 — Edges and control flow

Three edge constructs govern routing.

**`add_edge(from_node, to_node)`** creates an unconditional transition.

**`add_conditional_edges(node, routing_function)`** routes dynamically. The routing function inspects state and returns either node names directly or keys into an optional mapping dictionary.

**`START` and `END`** are the sentinel constants marking graph entry and termination. An edge from `START` designates the entry point; an edge to `END` terminates that branch.

Critically: **multiple outgoing edges from one node execute their destinations in parallel.** This is the fan-out mechanism, and it is also the origin of the most common LangGraph error — parallel nodes writing the same state key without a reducer raises `InvalidUpdateError`. If you add a second outgoing edge and start seeing that error, this is why.

## LG-02.5 — Conditional edges versus Command

There are two ways to express dynamic routing, and choosing between them is a recurring design question. `add_conditional_edges` keeps routing logic in a separate function, which preserves a statically inspectable graph structure and better visualization. Returning a `Command` from inside a node combines the state update and the routing decision in one place, which is more concise when the routing depends on work the node just did. `Command` is documented in `LG-03`.

The documented guidance for human-in-the-loop validation loops specifically favors conditional edges over in-node looping, because repeated `interrupt()` calls inside a loop replay prior iterations on each resume (see `LG-07`).

## LG-02.6 — Compilation options

`.compile()` accepts the runtime configuration that turns a graph definition into a durable, debuggable application. The most consequential arguments are `checkpointer` for persistence (`LG-04`), `store` for long-term memory (`LG-05`), and `interrupt_before`/`interrupt_after` for static breakpoints (`LG-07`).

A deployment caveat worth knowing before you write compile-time code: when running under the LangGraph API Server, the checkpointer is **injected at runtime** rather than supplied at compile time. Code that resolves a checkpointer during compilation can therefore behave differently in a server deployment than it does locally — the mechanism behind the `@task` caching surprise documented in `LG-09`.

## Sources

- [Graph API — official docs](https://docs.langchain.com/oss/python/langgraph/graph-api) — accessed 2026-08-13 (Tier 1)
- [Persistence — official docs](https://docs.langchain.com/oss/python/langgraph/persistence) — accessed 2026-08-13 (Tier 1)
- [Interrupts — official docs](https://docs.langchain.com/oss/python/langgraph/interrupts) — accessed 2026-08-13 (Tier 1)
