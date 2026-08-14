---
doc_id: SH-08
title: GitHub Issues — Solved & Ongoing
series: SH
product: both
version_scope: sampled 2026-08-13
last_verified: 2026-08-13
source_tier: 1
tags: [github-issues, bugs, solved, open, known-limitations, sampling-caveat]
---

# SH-08 — GitHub Issues: Solved & Ongoing

## SH-08.1 — Sampling method and its limits

**Read this before drawing conclusions from anything below.** GitHub's REST search API is scoped away from arbitrary repositories in the compilation environment, and repository issue-list views (`/issues?q=…`) are disallowed by robots. Individual issue pages *are* fetchable, and several were verified that way.

What follows is therefore a **thematically clustered sample with individually verified exemplars** — not an exhaustive census and not ranked by reactions or recency. Do not infer issue counts, relative severity, or "most upvoted" ordering from it, because that ordering could not be computed. The value here is the *pattern* each cluster represents and the verified state of the named exemplars.

Issues verified by direct fetch during compilation are marked **verified open** or **verified closed**. Others are cited as reported.

## SH-08.2 — Verified issues

Four issues were fetched directly and their titles, states, and content confirmed.

**[#3206](https://github.com/langchain-ai/langgraph/issues/3206) — verified CLOSED.** "Subgraph checkpointer=True causes subgraph to be skipped." A parent graph looped over a subgraph that used interrupts and was configured `checkpointer=True`. After the first resume, the subgraph never re-executed its counter node; the parent counter stuck at 1 and the run died with a recursion-limit error. Removing `checkpointer=True` resolved it. Filed January 2025 against LangGraph 0.2.67. Analyzed in `LG-08`.

**[#5790](https://github.com/langchain-ai/langgraph/issues/5790) — verified CLOSED.** "`langgraph dev` Ignores Checkpointer Configuration, Forcing In-Memory Storage." The dev server logged `"Using langgraph_runtime_inmem"` regardless of a configured `AsyncSqliteSaver`, leaving `checkpoint.db` empty and discarding conversation state on every hot reload. Analyzed in `LG-10`.

**[#35320](https://github.com/langchain-ai/langchain/issues/35320) — verified OPEN.** "`with_structured_output()` silently drops previously bound tools and lacks support for OpenAI native tool bindings." Chaining `.bind(tools=[...])` then `.with_structured_output(schema)` discards the tools because the second call creates bindings that overwrite rather than merge. The reporter's summary captures why it is dangerous: "The code appears to work — it returns structured JSON — but the model is hallucinating instead of using the tool." Three fixes are proposed: preserve bindings during merge, add a `tools` parameter to `with_structured_output()`, or raise explicitly instead of failing silently. Analyzed in `LC-04`.

**[#4973](https://github.com/langchain-ai/langgraph/issues/4973) — verified CLOSED as "not planned."** The LangGraph v1 roadmap feedback request, folded into an internal v1 sprint. Analyzed in `SH-02`.

## SH-08.3 — Cluster: streaming

The largest cluster, and the reports do not share a root cause. Subgraph streaming interacting with multiple stream modes ([#5932](https://github.com/langchain-ai/langgraph/issues/5932)); streaming conflicting with additional callbacks ([#6394](https://github.com/langchain-ai/langgraph/issues/6394)); `astream_events` not streaming when a graph is nested in a plain `Runnable` ([#6105](https://github.com/langchain-ai/langgraph/issues/6105)); async tools unable to emit custom events via `get_stream_writer()` ([#6447](https://github.com/langchain-ai/langgraph/issues/6447)); general `astream` misbehavior ([#6034](https://github.com/langchain-ai/langgraph/issues/6034)); frontends losing the event stream mid-run while LangSmith shows it continuing ([#6202](https://github.com/langchain-ai/langgraph/issues/6202)); a request for type-safe streaming and invoke ([#7008](https://github.com/langchain-ai/langgraph/issues/7008)); and, in JS, streaming failures against the OpenAI Responses API ([langgraphjs #1454](https://github.com/langchain-ai/langgraphjs/issues/1454)).

**Interpretation:** treat streaming problems as several independent bugs with distinct triggers. Isolate the exact combination — sync/async, subgraphs on/off, single/multiple modes, custom callbacks present/absent — before assuming a known issue applies. See `LG-06`.

## SH-08.4 — Cluster: checkpointers and persistence

Async checkpointer misuse causing hangs ([#1800](https://github.com/langchain-ai/langgraph/issues/1800)); `get_state_history` hanging with an async saver ([#2992](https://github.com/langchain-ai/langgraph/issues/2992)); async Postgres persistence errors ([#2609](https://github.com/langchain-ai/langgraph/issues/2609)); `setup()` failing against a fresh Postgres database ([#2570](https://github.com/langchain-ai/langgraph/issues/2570)); `undefined table 'checkpoints'` ([#2062](https://github.com/langchain-ai/langgraph/issues/2062)); a version-update regression in `langgraph-checkpoint-postgres` ([#3557](https://github.com/langchain-ai/langgraph/issues/3557)); incomplete Postgres setup documentation ([#4937](https://github.com/langchain-ai/langgraph/issues/4937)); and Postgres/Redis checkpointers failing inside Cloudflare Workers ([langgraphjs #1692](https://github.com/langchain-ai/langgraphjs/issues/1692)).

**Interpretation:** the dominant failure signature is a **silent hang from sync/async mismatch**, and the second is setup/schema friction on fresh databases. Both are as much DX and documentation gaps as code defects. See `LG-04`.

## SH-08.5 — Cluster: structured output and tool calling

Beyond the verified [#35320](https://github.com/langchain-ai/langchain/issues/35320): agents silently failing when a model omits an expected tool call ([#36349](https://github.com/langchain-ai/langchain/issues/36349)); structured output breaking when an assistant response is appended back into context ([#36916](https://github.com/langchain-ai/langchain/issues/36916)); structured output conflicting with system prompts ([#33688](https://github.com/langchain-ai/langchain/issues/33688)); `ChatOpenAI` dropping `reasoning_content` from OpenAI-compatible providers such as vLLM and DeepSeek ([#35059](https://github.com/langchain-ai/langchain/issues/35059)); Gemini falling back to tool-call emulation instead of native structured output in JS ([langchainjs #8585](https://github.com/langchain-ai/langchainjs/issues/8585)); Vertex AI failing to prepare the backing tool call ([langchain-google #953](https://github.com/langchain-ai/langchain-google/issues/953)); and a v1 message converter dropping valid block types for Google models ([langchainjs #10366](https://github.com/langchain-ai/langchainjs/issues/10366)).

**Interpretation:** these are overwhelmingly **provider-specific**, and they concentrate in the separately versioned partner packages. The fix pattern is per-provider rather than general, which means new providers and model releases reliably reintroduce similar problems. See `LC-04`.

## SH-08.6 — Cluster: legacy agents

Bugs in the deprecated agent surface — `AgentExecutor` failing to execute tools ([#31485](https://github.com/langchain-ai/langchain/issues/31485)), a bug in the `OPENAI_FUNCTIONS` agent type ([#12183](https://github.com/langchain-ai/langchain/issues/12183)), and `ImportError` on `AgentExecutor` ([#33621](https://github.com/langchain-ai/langchain/issues/33621)).

**Interpretation:** these largely resolve by **migration rather than patching**. The maintainers' answer to legacy-agent bugs is `create_agent` (see `LC-05`, `SH-02`), so time spent debugging legacy agent internals is usually better spent migrating.

## SH-08.7 — The general resolution pattern

Across clusters, issues resolve through one of two routes. Either the fix is **architectural migration** — move to `create_agent` and the LangGraph-first runtime rather than patch a legacy path — or it is a **provider-adapter fix** in a partner package such as `langchain-openai` or `langchain-google`, released independently of `langchain-core`.

The operational consequence for triage: when you hit a bug in a provider integration, check that package's own issue tracker and release notes. Waiting for a `langchain-core` release will not deliver the fix, because it will not be there.

## Sources

- Verified by direct fetch: [#3206](https://github.com/langchain-ai/langgraph/issues/3206), [#5790](https://github.com/langchain-ai/langgraph/issues/5790), [#35320](https://github.com/langchain-ai/langchain/issues/35320), [#4973](https://github.com/langchain-ai/langgraph/issues/4973) — accessed 2026-08-13 (Tier 1)
- Cited as reported: issues [#5932](https://github.com/langchain-ai/langgraph/issues/5932), [#6394](https://github.com/langchain-ai/langgraph/issues/6394), [#6105](https://github.com/langchain-ai/langgraph/issues/6105), [#6447](https://github.com/langchain-ai/langgraph/issues/6447), [#6034](https://github.com/langchain-ai/langgraph/issues/6034), [#6202](https://github.com/langchain-ai/langgraph/issues/6202), [#7008](https://github.com/langchain-ai/langgraph/issues/7008), [#1800](https://github.com/langchain-ai/langgraph/issues/1800), [#2992](https://github.com/langchain-ai/langgraph/issues/2992), [#2609](https://github.com/langchain-ai/langgraph/issues/2609), [#2570](https://github.com/langchain-ai/langgraph/issues/2570), [#2062](https://github.com/langchain-ai/langgraph/issues/2062), [#3557](https://github.com/langchain-ai/langgraph/issues/3557), [#4937](https://github.com/langchain-ai/langgraph/issues/4937), [#36349](https://github.com/langchain-ai/langchain/issues/36349), [#36916](https://github.com/langchain-ai/langchain/issues/36916), [#33688](https://github.com/langchain-ai/langchain/issues/33688), [#35059](https://github.com/langchain-ai/langchain/issues/35059), [#31485](https://github.com/langchain-ai/langchain/issues/31485), [#12183](https://github.com/langchain-ai/langchain/issues/12183), [#33621](https://github.com/langchain-ai/langchain/issues/33621), [langchainjs #8585](https://github.com/langchain-ai/langchainjs/issues/8585), [langchainjs #10366](https://github.com/langchain-ai/langchainjs/issues/10366), [langchain-google #953](https://github.com/langchain-ai/langchain-google/issues/953), [langgraphjs #1454](https://github.com/langchain-ai/langgraphjs/issues/1454), [langgraphjs #1692](https://github.com/langchain-ai/langgraphjs/issues/1692) — accessed 2026-08-13 (Tier 1 artifacts, sampled)
