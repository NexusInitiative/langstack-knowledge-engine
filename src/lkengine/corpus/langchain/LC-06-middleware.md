---
doc_id: LC-06
title: LangChain — Middleware System
series: LC
product: LangChain
version_scope: langchain 1.x
last_verified: 2026-08-13
source_tier: 1
tags: [middleware, hooks, SummarizationMiddleware, HumanInTheLoopMiddleware, PIIMiddleware, guardrails, retry, fallback, context-editing]
---

# LC-06 — Middleware System

## LC-06.1 — What middleware is and why it replaced subclassing

Middleware is LangChain 1.x's extension mechanism for agents. Rather than subclassing an agent or rewriting its loop, you pass a list of middleware objects to `create_agent`, each of which can observe or intervene at defined points in the agent's execution.

The documentation describes its purposes as "tracking agent behavior with logging, analytics, and debugging" and "transforming prompts, tool selection, and output formatting." Middleware operates inside the compiled LangGraph workflow, and — importantly for composition — hooks continue to run even when the agent is embedded as a node in a larger `StateGraph`. **Tier 1** ([middleware docs](https://docs.langchain.com/oss/python/langchain/middleware)).

## LC-06.2 — Hook points (verified against the API reference)

The `AgentMiddleware` base class supports **six hooks**, confirmed from the middleware API reference:

- **`before_agent`** — lifecycle boundary, before the agent loop starts
- **`before_model`** — pre-LLM processing, before each model invocation
- **`wrap_model_call`** — a wrapping interceptor around the model call
- **`after_model`** — post-LLM handling, after each model response
- **`wrap_tool_call`** — a wrapping interceptor around tool execution
- **`after_agent`** — lifecycle boundary, after the agent loop completes

Each hook has a matching **decorator** for defining middleware inline without subclassing: `@before_agent`, `@before_model`, `@wrap_model_call`, `@after_model`, `@wrap_tool_call`, `@after_agent`. The reference describes these as decorators "used to dynamically create a middleware with the `<hook>` hook."

Two further decorators exist beyond the six hooks: **`@generate_system_prompt`**, "used to dynamically generate system prompts for the model," and **`@configure_hook`**, "to configure hook behavior in middleware methods." A module-level **`set_default_trace_policy`** sets a process-wide default trace policy.

`@wrap_tool_call` is the one also documented in the tools page, where it converts tool exceptions into `ToolMessage` responses (see `LC-03`).

**Remaining verification gap:** composition ordering when multiple middleware wrap the same point is still **not confirmed** — neither the middleware overview nor the API reference index specified it. Treat ordering as significant and verify it empirically for your stack rather than assuming a direction.

**Correction note:** an earlier revision of this corpus listed these hook names as unverified inference. They are now confirmed Tier 1 from [reference.langchain.com](https://reference.langchain.com/python/langchain/agents/middleware/); the earlier inference happened to be correct, but it is now sourced rather than guessed.

## LC-06.3 — Prebuilt middleware catalogue

LangChain ships a substantial library of prebuilt middleware, which is the fastest route to production-grade behavior without custom code. The provider-agnostic set, with exact class names, is:

**Context and cost management.** `SummarizationMiddleware` automatically summarizes conversation history when approaching token limits. `ContextEditingMiddleware` manages context by clearing older tool outputs. Both directly address the cost-compounding pattern documented in `SH-10`, where accumulated tool output dominates token spend in long runs.

**Loop and cost guardrails.** `ModelCallLimitMiddleware` limits the number of model calls "to prevent infinite loops." `ToolCallLimitMiddleware` limits tool call counts — and per `LG-08` it doubles as the documented remedy for parallel invocation conflicts against per-thread subgraphs.

**Fault tolerance.** `ModelFallbackMiddleware` falls back to alternative models when the primary fails. `ModelRetryMiddleware` and `ToolRetryMiddleware` retry failed model and tool calls respectively with exponential backoff. `ToolErrorMiddleware` converts tool exceptions into error messages the model can recover from.

**Safety and governance.** `PIIMiddleware` detects and handles personally identifiable information. `HumanInTheLoopMiddleware` pauses execution for human approval of tool calls, building on the LangGraph interrupt mechanism in `LG-07`.

**Planning and delegation.** `TodoListMiddleware` equips agents with task planning. `SubAgentMiddleware` enables spawning and delegating to subagents.

**Tool management.** `LLMToolSelectorMiddleware` uses an LLM to select relevant tools from a large catalogue — the standard answer to degraded tool selection when a model is given too many tools. `ProviderToolSearchMiddleware` defers tools behind a provider's server-side tool search. `LLMToolEmulator` emulates tool execution using an LLM, which is aimed at testing.

**Capabilities.** `ShellToolMiddleware` exposes a persistent shell session. `FilesystemMiddleware` provides filesystem-backed memory tools, and `FilesystemFileSearchMiddleware` adds Glob and Grep search over files.

**Evaluation.** `RubricMiddleware` applies LLM-as-a-judge grading for self-evaluation and iteration.

Provider-specific middleware for Anthropic, AWS, and OpenAI also exist. **Tier 1** ([built-in middleware docs](https://docs.langchain.com/oss/python/langchain/middleware/built-in)).

## LC-06.4 — Choosing middleware deliberately

The catalogue maps onto the failure modes documented elsewhere in this corpus, and reading it that way is the fastest path to a resilient agent. Runaway loops — the most common cause of `GraphRecursionError` in `SH-07` — are bounded by `ModelCallLimitMiddleware` and `ToolCallLimitMiddleware`. Context growth and its cost consequences are handled by `SummarizationMiddleware` and `ContextEditingMiddleware`. Transient provider failures are absorbed by the retry and fallback middleware. Tool exceptions that would otherwise kill a run are converted by `ToolErrorMiddleware`.

Because these are prebuilt and composable, the practical guidance is to start from this list before writing custom middleware — most production hardening people write by hand already exists here.

## Sources

- [Middleware — official docs](https://docs.langchain.com/oss/python/langchain/middleware) — accessed 2026-08-13 (Tier 1)
- [Prebuilt middleware — official docs](https://docs.langchain.com/oss/python/langchain/middleware/built-in) — accessed 2026-08-13 (Tier 1)
- [Tools — official docs (for @wrap_tool_call)](https://docs.langchain.com/oss/python/langchain/tools) — accessed 2026-08-13 (Tier 1)
