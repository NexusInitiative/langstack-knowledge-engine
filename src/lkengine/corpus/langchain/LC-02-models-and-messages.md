---
doc_id: LC-02
title: LangChain — Chat Models & Messages
series: LC
product: LangChain
version_scope: langchain 1.x / langchain-core 1.x
last_verified: 2026-08-13
source_tier: 1
tags: [chat-models, init_chat_model, messages, content-blocks, multimodal, streaming, rate-limiting, caching, token-usage]
---

# LC-02 — Chat Models & Messages

## LC-02.1 — Initializing models with init_chat_model

`init_chat_model` is the provider-agnostic constructor for chat models, imported from `langchain.chat_models`. It accepts a model identifier — either a bare name or a `"provider:model"` string such as `"openai:gpt-5.5"` — plus common parameters, and resolves the correct provider integration.

```python
from langchain.chat_models import init_chat_model
model = init_chat_model("claude-sonnet-4-6", temperature=0.7, max_tokens=1000)
```

Documented providers include OpenAI, Anthropic, Azure, Google Gemini, AWS Bedrock, HuggingFace, and OpenRouter. Standard parameters are `model`, `temperature` (0 being deterministic), `max_tokens`, `timeout` in seconds, and `max_retries` which defaults to **6**. **Tier 1** ([models docs](https://docs.langchain.com/oss/python/langchain/models)).

## LC-02.2 — Invocation methods

Four invocation surfaces exist. `invoke()` makes a single synchronous call returning a complete `AIMessage`. `stream()` yields `AIMessageChunk` objects as they arrive, each exposing `.text`. `batch()` and `batch_as_completed()` process multiple inputs in parallel, with concurrency governed by `max_concurrency`; the `as_completed` variant yields results in completion order rather than input order.

```python
response = model.invoke("Why do parrots talk?")
for chunk in model.stream("Your prompt"):
    print(chunk.text, end="|")
```

## LC-02.3 — Message types

LangChain defines four primary message classes. **`SystemMessage`** carries the initial instructions priming model behavior — context, tone, guidelines. **`HumanMessage`** represents user input and supports text, images, audio, files, and multimodal content, with optional `name` and `id` metadata. **`AIMessage`** holds model output and exposes `tool_calls`, `usage_metadata`, and `response_metadata`. **`ToolMessage`** returns tool execution results and requires `content`, `tool_call_id`, and `name`; it optionally carries an `artifact` field for supplementary data that is deliberately *not* sent back to the model — useful when a tool produces both a model-facing summary and a bulky payload your application needs.

## LC-02.4 — Content blocks: the .content_blocks property

Messages expose a `content_blocks` property that, per the documentation, "lazily parse[s] the `content` attribute into a standard, type-safe representation." This was introduced in the 1.0 line to normalize the divergent shapes modern provider APIs return, while leaving the raw `content` attribute intact for backward compatibility.

The standard block taxonomy covers several families. Core blocks are `TextContentBlock` and `ReasoningContentBlock`. Multimodal blocks are `ImageContentBlock`, `AudioContentBlock`, `VideoContentBlock`, `FileContentBlock` for generic files such as PDFs, and `PlainTextContentBlock` for document text like `.txt` and `.md` — each accepting URL, base64, or `file_id` sourcing. Tool-related blocks are `ToolCall`, `ToolCallChunk` for streaming fragments, and `InvalidToolCall` for malformed calls. Server-side execution is represented by `ServerToolCall`, `ServerToolCallChunk`, and `ServerToolResult`. Finally, `NonStandardContentBlock` is the documented escape hatch for provider-unique features that do not map onto the standard taxonomy.

The practical significance is that `InvalidToolCall` and `ReasoningContentBlock` exist as first-class citizens — meaning malformed tool calls and reasoning traces are things the framework expects to happen and gives you a typed way to inspect, rather than failure modes you discover by string-parsing. **Tier 1** ([messages docs](https://docs.langchain.com/oss/python/langchain/messages)).

## LC-02.5 — Rate limiting

LangChain ships an in-process rate limiter, `InMemoryRateLimiter`, imported from `langchain.rate_limiters` and passed to the model constructor:

```python
from langchain.rate_limiters import InMemoryRateLimiter
limiter = InMemoryRateLimiter(requests_per_second=0.1)
model = init_chat_model("gpt-5.5", rate_limiter=limiter)
```

Because it is in-memory, it governs a single process. It does not coordinate across replicas, so a horizontally scaled deployment needs an external limiter to enforce a true global budget.

## LC-02.6 — Prompt caching, model profiles, reasoning, and configurable models

**Prompt caching** is supported either implicitly by the provider or explicitly through provider-specific fields such as OpenAI's `prompt_cache_key`.

**Model profiles** are exposed via `model.profile`, a dictionary describing capabilities including `max_input_tokens`, `tool_calling`, and `reasoning_output`. This is the programmatic way to branch on capability instead of hardcoding assumptions per model name.

**Reasoning** models accept a `reasoning_effort` parameter with documented values `"low"` and `"high"`, and reasoning output surfaces as `ReasoningContentBlock`.

**Configurable models** allow deferring model choice to runtime through `configurable_fields`:

```python
model = init_chat_model(temperature=0, configurable_fields=("model", "temperature"))
model.invoke("prompt", config={"configurable": {"model": "claude-sonnet-4-6"}})
```

## LC-02.7 — Token usage tracking

Token accounting is available through `UsageMetadataCallbackHandler` or the `get_usage_metadata_callback` context manager, both of which aggregate token counts across multiple model calls. This is the framework-native answer to the cost-visibility problem documented in `SH-10`, where a measured study found that in long agent runs the accumulated context — not generation — dominates spend. Aggregating usage at the callback layer is how you detect that pattern before the invoice does.

## Sources

- [Chat models — official docs](https://docs.langchain.com/oss/python/langchain/models) — accessed 2026-08-13 (Tier 1)
- [Messages — official docs](https://docs.langchain.com/oss/python/langchain/messages) — accessed 2026-08-13 (Tier 1)
- [init_chat_model API reference](https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model) — accessed 2026-08-13 (Tier 1)
