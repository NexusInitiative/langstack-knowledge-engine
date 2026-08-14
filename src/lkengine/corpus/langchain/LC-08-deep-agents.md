---
doc_id: LC-08
title: LangChain — Deep Agents
series: LC
product: LangChain
version_scope: deepagents 0.7.5 (Python >=3.11)
last_verified: 2026-08-13
source_tier: 1
tags: [deepagents, create_deep_agent, agent-harness, subagents, filesystem, AGENTS.md, interrupt_on, skills]
---

# LC-08 — Deep Agents

## LC-08.1 — What Deep Agents is

Deep Agents is a standalone library described by LangChain as **"the batteries-included agent harness"** and, in its documentation, as "the easiest way to start building agents." It targets complex, multi-step tasks by shipping capabilities that most teams otherwise assemble by hand: a virtual filesystem, subagent spawning, planning, and long-term memory.

Its relationship to the rest of the stack is explicit — Deep Agents is built on LangChain's core building blocks and uses **LangGraph as its runtime**. The documentation characterizes it as offering "the same core tool calling loop as other agent frameworks, but with built-in capabilities." It is the top of the three-tier positioning described in `LC-01`, and the LangChain README points beginners to it rather than to raw primitives.

Install as `deepagents`. Verified version 0.7.5 with 117 releases and a Python floor of **3.11** — stricter than the 3.10 floor of the core packages, which is worth checking before adopting it (see `SH-01`). **Tier 1** ([Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview)).

## LC-08.2 — The entry point

The primary constructor is **`create_deep_agent()`**, which takes familiar parameters including `model`, `tools`, and `system_prompt`. The API surface deliberately mirrors `create_agent` from `LC-05`, so the mental model transfers; the difference is what comes pre-wired rather than how you call it.

## LC-08.3 — The four pillars

Deep Agents organizes its built-in capabilities into four groups.

**Execution environment.** Tools, a virtual filesystem, an optional sandbox, and code execution via a REPL. The virtual filesystem is the load-bearing piece: it gives the agent somewhere to put intermediate work that is not the conversation transcript.

**Context management.** Skills, memory backed by `AGENTS.md` files, summarization, context offloading, and prompt caching. Context offloading is the direct structural answer to the cost-compounding problem measured in `SH-10` — moving bulky intermediate state onto the filesystem instead of leaving it in the message history means it stops being re-billed on every subsequent turn.

**Delegation.** Task planning through the optional `TodoListMiddleware`, and subagent spawning through a built-in **`task`** tool. Subagents are how Deep Agents keeps a long task from exhausting a single context window: work is delegated to a fresh agent with its own context, and only the result returns.

**Steering.** Human-in-the-loop approval via an **`interrupt_on`** parameter, plus filesystem permissions. `interrupt_on` builds on the LangGraph interrupt mechanism documented in `LG-07`, so the resume semantics and the node-restart caveat described there apply.

## LC-08.4 — When Deep Agents is the right layer

The three-tier choice from `LC-01` resolves roughly as follows. Choose **Deep Agents** when the task is long-horizon and open-ended — research, multi-step investigation, code work — and you want filesystem, planning, and delegation without building them. Choose **`create_agent`** when you want the standard tool-calling loop with precise control over middleware and no opinions about filesystems or subagents. Choose **raw LangGraph** when your control flow is genuinely custom and the agent loop is not the right abstraction at all.

Deep Agents' release cadence is worth noting when planning adoption: 117 releases for a 0.x package indicates a fast-moving surface, so pin versions and read release notes rather than tracking latest.

## LC-08.5 — Relationship to middleware

Several Deep Agents capabilities correspond to middleware documented in `LC-06` — `TodoListMiddleware` for planning, `SubAgentMiddleware` for delegation, `FilesystemMiddleware` and `FilesystemFileSearchMiddleware` for the filesystem layer. This is the practical bridge between the two layers: **Deep Agents is substantially a curated, pre-wired assembly of LangChain middleware plus a harness around it.** If you find yourself adding those middlewares to a `create_agent` build one at a time, you are reconstructing Deep Agents and should evaluate adopting it directly instead.

## Sources

- [Deep Agents overview — official docs](https://docs.langchain.com/oss/python/deepagents/overview) — accessed 2026-08-13 (Tier 1)
- [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) — accessed 2026-08-13 (Tier 1)
- [deepagents on PyPI](https://pypi.org/pypi/deepagents/json) — queried 2026-08-13 (Tier 1)
- [deepagents API reference](https://reference.langchain.com/python/deepagents) — accessed 2026-08-13 (Tier 1)
- [LangChain Deep Agents product page](https://www.langchain.com/deep-agents) — accessed 2026-08-13 (Tier 1)
