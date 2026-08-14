---
doc_id: LC-03
title: LangChain — Tools & Tool Calling
series: LC
product: LangChain
version_scope: langchain 1.x
last_verified: 2026-08-13
source_tier: 1
tags: [tools, tool-decorator, ToolNode, ToolRuntime, args_schema, tool-errors, return_direct, Command]
---

# LC-03 — Tools & Tool Calling

## LC-03.1 — Defining tools with the @tool decorator

The `@tool` decorator is the primary way to define a tool in LangChain. Per the official documentation, "The simplest way to create a tool is with the `@tool` decorator. By default, the function's docstring becomes the tool's description that helps the model understand when to use it."

Two consequences follow that are easy to get wrong. First, the docstring is not documentation for humans — it is the description the model reads to decide whether to call the tool, so it should be written for that audience. Second, **type hints are mandatory**: the documentation states plainly that "Type hints are **required** as they define the tool's input schema." An untyped parameter cannot be turned into a schema the model can target. **Tier 1** ([tools docs](https://docs.langchain.com/oss/python/langchain/tools)).

## LC-03.2 — Binding tools to a model

Tools are attached to a model with `bind_tools`, which returns a new model instance that advertises those tools to the provider. Tool calls come back on the `AIMessage` as `tool_calls`, a list of dicts with `name`, `args`, and `id`:

```python
model_with_tools = model.bind_tools([get_weather])
response = model_with_tools.invoke("What's the weather?")
for tool_call in response.tool_calls:
    print(f"Tool: {tool_call['name']}, Args: {tool_call['args']}")
```

A documented hazard applies here. Chaining `.bind(tools=[...])` followed by `.with_structured_output(schema)` on the OpenAI integration silently drops the tool bindings, because `with_structured_output()` creates fresh bindings that overwrite rather than merge previously bound kwargs. The code appears to work — structured JSON is returned — while the model hallucinates instead of calling the tool. This is tracked as an open issue; see `LC-04` and `SH-08`.

## LC-03.3 — Schemas and args_schema

For inputs more complex than simple type hints express, tools accept an `args_schema` parameter taking a Pydantic model or a JSON schema. This is how you attach per-field descriptions and validation rules, which materially improves the model's ability to populate arguments correctly. Field descriptions in a Pydantic model become part of the schema the model sees, so they function as inline prompting for each argument.

## LC-03.4 — ToolNode and runtime injection via ToolRuntime

**`ToolNode`** executes tools inside LangGraph workflows, managing how tools access graph state and run-scoped context. It is the bridge between a tool definition and the graph runtime described in `LG-02`.

**`ToolRuntime`** is the current injection pattern giving a tool access to state, run context, the store, the stream writer, and execution metadata. The documentation identifies it as the modern replacement for older patterns including `InjectedState`. If you encounter tutorials using `InjectedState` — and many third-party tutorials still do — treat them as describing a superseded API.

The stream-writer access matters for user experience: it is how a long-running tool emits incremental progress into a `custom` stream rather than going silent until completion. See `LG-06`.

## LC-03.5 — Error handling

Tool error handling is implemented through **middleware** rather than a per-tool try/except convention. The `@wrap_tool_call` decorator intercepts tool execution, catches exceptions, and returns a custom `ToolMessage` in place of a crash — which keeps the agent loop alive and gives the model a chance to recover or re-plan.

Two prebuilt middlewares cover the common cases without custom code: `ToolErrorMiddleware` converts tool exceptions into error messages the model can act on, and `ToolRetryMiddleware` retries failed tool calls with exponential backoff. Both are catalogued in `LC-06`.

## LC-03.6 — Tool return values

Tools may return several kinds of thing, and the choice affects control flow. A plain string or object becomes the tool's content. Returning a **`Command`** instance lets the tool update graph state directly and even redirect control flow — the same `Command` primitive documented in `LG-03`, which is a notable capability because it means a tool is not restricted to returning data; it can steer the graph. Tools may also return **multimodal content blocks**, matching the taxonomy in `LC-02`.

Setting **`return_direct=True`** causes the tool's output to be returned to the caller immediately, bypassing a further model call. This is the right setting for a tool whose output is already the final answer, and it saves both latency and a billable model invocation.

## Sources

- [Tools — official docs](https://docs.langchain.com/oss/python/langchain/tools) — accessed 2026-08-13 (Tier 1)
- [Chat models: bind_tools reference](https://reference.langchain.com/python/langchain-core/language_models/chat_models/BaseChatModel/bind_tools) — accessed 2026-08-13 (Tier 1)
- [Issue #35320 — with_structured_output drops bound tools](https://github.com/langchain-ai/langchain/issues/35320) — verified open, accessed 2026-08-13 (Tier 1)
