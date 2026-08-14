---
doc_id: LG-06
title: LangGraph — Streaming
series: LG
product: LangGraph
version_scope: langgraph 1.x; StreamPart format version="v2"
last_verified: 2026-08-13
source_tier: 1
tags: [streaming, stream_mode, values, updates, messages, custom, debug, checkpoints, tasks, get_stream_writer, subgraphs, StreamPart]
---

# LG-06 — Streaming

## LG-06.1 — Seven stream modes

LangGraph exposes execution through `stream()` and `astream()` with a `stream_mode` parameter taking seven documented values:

- **`values`** — the full state after each step.
- **`updates`** — state updates after each step; multiple updates within the same step are streamed separately.
- **`messages`** — 2-tuples of `(LLM token, metadata)` from model calls. This is the mode for token-by-token UI output.
- **`custom`** — arbitrary data emitted from inside nodes and tools via `get_stream_writer()`.
- **`checkpoints`** — checkpoint events. **Requires a checkpointer.**
- **`tasks`** — task start and finish events including results and errors. **Requires a checkpointer.**
- **`debug`** — everything; combines `checkpoints` and `tasks` with extra metadata.

The distinction between `values` and `updates` is the one most often gotten wrong: `values` re-sends the entire state on every step, while `updates` sends only the delta. For large state, `updates` is dramatically cheaper to transport. **Tier 1** ([streaming docs](https://docs.langchain.com/oss/python/langgraph/streaming)).

## LG-06.2 — Multiple modes and the v2 StreamPart format

Multiple modes can be requested simultaneously by passing a list to `stream_mode`. With **`version="v2"`**, every emitted chunk follows a unified **`StreamPart`** shape with `type`, `ns`, and `data` fields, and consumers filter on `chunk["type"]`.

The documentation is explicit that v2 exists to fix a real problem: v1 produced variable output structures — raw data, 2-tuples, or 3-tuples depending on which modes and options were active. Any tutorial that parses stream output by positional unpacking is written against v1 semantics.

Note the version-parameter collision described in `LC-05`: LangChain's `agent.stream_events()` documents `version="v3"`, while LangGraph's `.stream()` documents `version="v2"`. These are **different APIs with independently versioned formats** — not a typo in either place, and a real trap when mixing documentation sources.

## LG-06.3 — Custom streaming with get_stream_writer

`get_stream_writer()` obtains a writer inside a node or tool for emitting arbitrary data into the `custom` stream. Two things make it more useful than it first appears.

First, it works with **any** LLM, including ones with no LangChain integration — you can stream tokens from a raw provider SDK by writing them yourself. Second, it is the mechanism for progress reporting from long-running tools, which otherwise appear frozen to the user until they return. Tools reach the writer through `ToolRuntime` (see `LC-03`).

A known limitation: async tools have been reported not to support `custom` event streaming via `get_stream_writer()` on some paths ([#6447](https://github.com/langchain-ai/langgraph/issues/6447)). Verify this against your version before designing a UI around async tool progress.

## LG-06.4 — Streaming from subgraphs

Setting **`subgraphs=True`** on `.stream()` includes output from nested graphs. In the v2 format, the **`ns`** field carries the namespace path identifying which subgraph a chunk came from.

The documentation also describes a `stream.subgraphs` projection for observing nested executions and discovering each run's path and values **without parsing namespace strings** — which is the preferable route, since string-parsing namespaces is brittle.

## LG-06.5 — Known issues in streaming

Streaming is the most issue-dense area of LangGraph, and the reports do not share one root cause. Distinct reported problems include: subgraph streaming interacting badly with multiple stream modes when `subgraphs=True` ([#5932](https://github.com/langchain-ai/langgraph/issues/5932)); streaming conflicting with additional callbacks ([#6394](https://github.com/langchain-ai/langgraph/issues/6394)); `astream_events` not streaming when a LangGraph graph is nested inside a plain `Runnable` ([#6105](https://github.com/langchain-ai/langgraph/issues/6105)); async tools not supporting custom events ([#6447](https://github.com/langchain-ai/langgraph/issues/6447)); general `astream` misbehavior ([#6034](https://github.com/langchain-ai/langgraph/issues/6034)); frontends ceasing to receive events mid-stream while LangSmith shows the run continuing ([#6202](https://github.com/langchain-ai/langgraph/issues/6202)); and, in JS, streaming failures against the OpenAI Responses API ([langgraphjs #1454](https://github.com/langchain-ai/langgraphjs/issues/1454)).

The practical implication: treat "streaming is flaky" as **several independent bugs with different triggers**, not one fixable root cause. When diagnosing, isolate the specific combination — sync versus async, subgraphs on or off, single versus multiple modes, custom callbacks present or absent — because that combination is usually what determines whether you hit a known issue. Issue-sampling caveats are documented in `SH-08`.

## Sources

- [Streaming — official docs](https://docs.langchain.com/oss/python/langgraph/streaming) — accessed 2026-08-13 (Tier 1)
- [stream API reference](https://reference.langchain.com/python/langgraph/stream) — accessed 2026-08-13 (Tier 1)
- GitHub issues [#5932](https://github.com/langchain-ai/langgraph/issues/5932), [#6394](https://github.com/langchain-ai/langgraph/issues/6394), [#6105](https://github.com/langchain-ai/langgraph/issues/6105), [#6447](https://github.com/langchain-ai/langgraph/issues/6447), [#6034](https://github.com/langchain-ai/langgraph/issues/6034), [#6202](https://github.com/langchain-ai/langgraph/issues/6202), [langgraphjs #1454](https://github.com/langchain-ai/langgraphjs/issues/1454) — accessed 2026-08-13 (Tier 1)
