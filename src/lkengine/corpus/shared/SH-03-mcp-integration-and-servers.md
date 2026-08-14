---
doc_id: SH-03
title: MCP Integration & LangChain's Official MCP Servers
series: SH
product: both
version_scope: langchain-mcp-adapters 0.3.2, mcpdoc
last_verified: 2026-08-13
source_tier: 1
tags: [mcp, model-context-protocol, MultiServerMCPClient, load_mcp_tools, mcpdoc, llms-txt, stdio, streamable-http, transports]
---

# SH-03 — MCP Integration & Official MCP Servers

## SH-03.1 — Two distinct things called "LangChain MCP"

Precision matters here because two different artifacts get conflated.

**Consuming MCP** — using MCP servers as tool sources for LangChain/LangGraph agents — is handled by `langchain-mcp-adapters`. This is the common case, covered in `SH-03.2` through `SH-03.5`.

**Serving MCP** — LangChain publishing MCP servers others connect to — takes two forms: a hosted documentation MCP endpoint at `https://docs.langchain.com/mcp`, and an **open-source MCP server, `mcpdoc`**, published at [langchain-ai/mcpdoc](https://github.com/langchain-ai/mcpdoc). These are covered in `SH-03.6`.

## SH-03.2 — langchain-mcp-adapters

`langchain-mcp-adapters` bridges Anthropic's Model Context Protocol with LangChain and LangGraph. Install with `pip install langchain-mcp-adapters`; the JavaScript package is `@langchain/mcp-adapters`.

Verified version **0.3.2** across 32 releases, queried from PyPI on 2026-08-13. An earlier compilation pass of this corpus reported 0.2.2 from a cached README summary — corrected here, and a reminder that adapter versions move quickly. **Tier 1** ([MCP docs](https://docs.langchain.com/oss/python/langchain/mcp), [repo](https://github.com/langchain-ai/langchain-mcp-adapters)).

## SH-03.3 — Key classes

**`MultiServerMCPClient`** is the primary interface. It connects to one or more MCP servers and retrieves their tools, resources, and prompts. Its default behavior is **stateless** — each tool call creates a fresh session and cleans up afterward. For persistent connections with explicit lifecycle control, use `client.session()`.

The stateless default is worth understanding before profiling: per-call session setup is correctness-preserving but not free, and a chatty agent against a remote MCP server will pay it repeatedly.

**`load_mcp_tools`** extracts tools from an MCP server and converts them into LangChain-compatible tool objects, at which point they behave like any other tool from `LC-03`.

## SH-03.4 — Transports

Three transports are documented, with materially different deployment characteristics.

**`stdio`** communicates with a local subprocess and is inherently stateful. The documentation cautions explicitly that stdio "was designed primarily for user machines" and advises evaluating alternatives before using it in web-server contexts. Many tutorials wire stdio MCP servers straight into backends — treat that as a shortcut, not a recommended pattern.

**`http` / `streamable-http`** handles remote connections with optional custom headers and authentication. This is the appropriate choice for server-side deployments.

**`sse`** is deprecated by the MCP specification itself but still supported by the adapter for compatibility.

## SH-03.5 — Advanced features and error semantics

The adapter supports **tool interceptors** for middleware-style control, **progress notifications**, **logging subscriptions**, and **elicitation** — interactive user input during tool execution, which maps naturally onto the LangGraph interrupt mechanism in `LG-07`.

One default worth knowing: **errors are passed back as tool messages rather than raised as exceptions.** An MCP tool failure therefore reaches the model as content it can react to, rather than terminating the run. This is usually desirable, but it means a systematically failing MCP tool can burn model calls quietly instead of failing loudly — pair it with `ToolCallLimitMiddleware` from `LC-06` if that risk matters.

`MultiServerMCPClient` integrates with `StateGraph` and LangGraph API Server deployments directly.

## SH-03.6 — mcpdoc: LangChain's open-source MCP server

**`mcpdoc`** is LangChain's open-source MCP server, described as exposing `llms.txt` documentation files to IDEs and AI applications — Cursor, Windsurf, Claude and others — with the stated goal of giving users "full control over tools used by these applications."

It exposes **two MCP tools**: `list_doc_sources`, which retrieves available documentation sources, and `fetch_docs`, which reads URLs referenced within the `llms.txt` files.

Run it with `uvx`:

```bash
uvx --from mcpdoc mcpdoc --urls "LangGraph:https://langchain-ai.github.io/langgraph/llms.txt"
```

It ships pointing at four official `llms.txt` sources: LangGraph Python (`langchain-ai.github.io/langgraph/llms.txt`), LangGraph JS (`langchain-ai.github.io/langgraphjs/llms.txt`), LangChain Python (`python.langchain.com/llms.txt`), and LangChain JS (`js.langchain.com/llms.txt`). Example configurations are documented for Cursor (`~/.cursor/mcp.json`), Windsurf (`~/.codeium/windsurf/mcp_config.json`), and Claude Desktop, all using the same JSON structure with `--transport stdio`.

## SH-03.7 — llms.txt as a corpus ingestion path

Separately from `mcpdoc`, the unified documentation site publishes a machine-readable index at **`https://docs.langchain.com/llms.txt`**. It enumerates the Build, OSS (Deep Agents, LangChain, LangGraph, Integrations), LangSmith, and Studio sections, with `.md` URLs for individual pages — for example `docs.langchain.com/oss/python/langgraph/graph-api.md`.

For anyone building a RAG index or corpus over LangChain documentation, this is the correct entry point: it gives a complete, structured, machine-readable inventory rather than requiring a crawl. Combining `llms.txt` for enumeration with `mcpdoc` for serving is the officially supported pattern for making LangChain docs available to an agent.

## Sources

- [Model Context Protocol (MCP) — official docs](https://docs.langchain.com/oss/python/langchain/mcp) — accessed 2026-08-13 (Tier 1)
- [langchain-ai/langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters) — accessed 2026-08-13 (Tier 1)
- [langchain-ai/mcpdoc](https://github.com/langchain-ai/mcpdoc) — accessed 2026-08-13 (Tier 1)
- [docs.langchain.com/llms.txt](https://docs.langchain.com/llms.txt) — accessed 2026-08-13 (Tier 1)
- [MultiServerMCPClient API reference](https://reference.langchain.com/python/langchain-mcp-adapters/client/MultiServerMCPClient) — accessed 2026-08-13 (Tier 1)
- [PyPI: langchain-mcp-adapters](https://pypi.org/pypi/langchain-mcp-adapters/json) — queried 2026-08-13 (Tier 1)
