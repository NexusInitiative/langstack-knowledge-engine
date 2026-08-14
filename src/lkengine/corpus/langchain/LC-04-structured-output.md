---
doc_id: LC-04
title: LangChain — Structured Output
series: LC
product: LangChain
version_scope: langchain 1.x; strict= requires langchain >=1.2
last_verified: 2026-08-13
source_tier: 1
tags: [structured-output, response_format, ProviderStrategy, ToolStrategy, pydantic, json-schema, validation, retries]
---

# LC-04 — Structured Output

## LC-04.1 — Two distinct mechanisms

LangChain exposes structured output through two different surfaces, and conflating them causes confusion.

At the **model level**, `with_structured_output(schema)` wraps a chat model so that `invoke()` returns a parsed object instead of an `AIMessage`. It accepts Pydantic models, TypedDicts, or JSON Schema.

At the **agent level**, `create_agent` accepts a `response_format` parameter, and the validated result appears in the agent's final state under the **`'structured_response'`** key. This is the mechanism to use inside an agent loop, and it is strategy-aware in ways the model-level wrapper is not. **Tier 1** ([structured output docs](https://docs.langchain.com/oss/python/langchain/structured-output)).

## LC-04.2 — ProviderStrategy versus ToolStrategy

The agent-level mechanism resolves to one of two strategies.

**`ProviderStrategy`** uses the model provider's native structured-output API — supported for OpenAI, Anthropic Claude, xAI Grok, and Gemini. It is the most reliable path because validation happens provider-side. LangChain selects it automatically when the provider supports it.

**`ToolStrategy`** falls back to tool calling to elicit the structure, and therefore works with any model that supports tool calls at all. It is the compatibility path.

The distinction has practical consequences for debugging: a schema that validates cleanly under `ProviderStrategy` on one provider may behave differently under `ToolStrategy` on another, because the second is emulating a capability rather than invoking it natively.

## LC-04.3 — Supported schema formats and their return types

Both strategies accept four schema formats, and **the format you pass determines what you get back**:

- **Pydantic models** → returns a validated Pydantic instance.
- **Dataclasses** → returns a dictionary.
- **TypedDict** → returns a dictionary.
- **JSON Schema** → returns a dictionary; requires top-level `title` and `description` keys.

A documented gotcha: a raw JSON Schema dictionary passed directly to `response_format` **will not auto-detect a strategy** — it requires explicit strategy wrapping. If you want a validated Python object rather than a dict, use a Pydantic model.

## LC-04.4 — Strategy parameters

`ProviderStrategy` takes `schema` (required) and an optional `strict` boolean requesting stricter provider-side adherence. The documentation notes `strict` **requires langchain ≥ 1.2** — one of the few precisely version-gated features in the current API, worth checking against your pinned version.

`ToolStrategy` takes `schema` (required, and notably supporting **Union types** so the model can select among several possible output shapes), `tool_message_content` to customize what appears in conversation history for the structured-output call, and `handle_errors`.

## LC-04.5 — Error handling and retries

`handle_errors` on `ToolStrategy` is unusually flexible: it accepts `True`/`False`, a custom string, exception types, or a callable. This governs behavior when structured output validation fails — including schema mismatches and the case where the model emits multiple structured-output calls when one was expected. The framework can retry automatically with customizable feedback messages injected back to the model, or filter which exceptions are handled versus raised.

Configuring this deliberately is worthwhile, because the default silent-retry behavior can mask a schema that the model consistently struggles with, converting a design problem into an inflated token bill.

## LC-04.6 — Known failure modes

Structured output is one of the most issue-dense areas of LangChain, and the pattern across reports is that failures are **provider-specific and often silent**. Verified and reported cases include: `with_structured_output()` silently dropping previously bound tools on the OpenAI integration, with no supported way to combine schema validation with native provider tools such as `web_search` in one call ([#35320](https://github.com/langchain-ai/langchain/issues/35320), **confirmed open**); agents silently failing when a model declines to make an expected tool call ([#36349](https://github.com/langchain-ai/langchain/issues/36349)); structured output breaking when an assistant response is appended back into context ([#36916](https://github.com/langchain-ai/langchain/issues/36916)); conflicts between structured output and system prompts ([#33688](https://github.com/langchain-ai/langchain/issues/33688)); Gemini falling back to tool-calling emulation instead of native structured output in the JS SDK ([langchainjs #8585](https://github.com/langchain-ai/langchainjs/issues/8585)); and Vertex AI failing to prepare the tool call backing structured output ([langchain-google #953](https://github.com/langchain-ai/langchain-google/issues/953)).

The operational rule that follows: **test structured output against the exact model and provider you will ship on.** Success on one provider does not transfer, and several of these failures are silent — you get plausible JSON with no error, which is the most expensive kind of bug to find late.

## Sources

- [Structured output — official docs](https://docs.langchain.com/oss/python/langchain/structured-output) — accessed 2026-08-13 (Tier 1)
- [with_structured_output API reference](https://reference.langchain.com/python/langchain-core/language_models/chat_models/BaseChatModel/with_structured_output) — accessed 2026-08-13 (Tier 1)
- GitHub issues [#35320](https://github.com/langchain-ai/langchain/issues/35320) (verified open), [#36349](https://github.com/langchain-ai/langchain/issues/36349), [#36916](https://github.com/langchain-ai/langchain/issues/36916), [#33688](https://github.com/langchain-ai/langchain/issues/33688), [langchainjs #8585](https://github.com/langchain-ai/langchainjs/issues/8585), [langchain-google #953](https://github.com/langchain-ai/langchain-google/issues/953) — accessed 2026-08-13 (Tier 1)
