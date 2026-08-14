---
doc_id: AC-01
title: Foundational Agent Papers Behind LangChain/LangGraph Patterns
series: AC
product: both
version_scope: foundational — not currency-sensitive
last_verified: 2026-08-13
source_tier: 1
recency_class: foundational
tags: [academic, react, reflexion, papers, agent-patterns, plan-and-execute, rewoo, citations]
---

# AC-01 — Foundational Agent Papers

## AC-01.1 — Why foundational papers sit outside the 3-year recency window

This corpus enforces a three-year recency window on **currency-sensitive** claims — versions, APIs, CVEs, current recommendations. Seminal papers are governed by a **different rule**, documented in `META-01`: a foundational citation does not expire, and replacing ReAct (2022) or Pregel (2010) with a recent secondary summary would *reduce* accuracy rather than improve it.

Papers in the `AC-*` series are therefore tagged `recency_class: foundational` and are exempt from the window. Papers *about* LangChain (`AC-04`) and security research (`AC-05`) are `recency_class: current` and do fall inside it.

## AC-01.2 — ReAct: the pattern LangChain's agent loop implements

**Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2022). "ReAct: Synergizing Reasoning and Acting in Language Models."** arXiv:2210.03629, submitted 6 October 2022; v3 is the ICLR 2023 camera-ready.

The paper's contribution is interleaving reasoning traces with task-specific actions rather than treating them as separate capabilities. In the authors' framing, "reasoning traces help the model induce, track, and update action plans as well as handle exceptions, while actions allow it to interface with external sources, such as knowledge bases or environments, to gather additional information."

**Direct relevance:** this is the loop `create_agent` implements, and it is the literal source of the name `create_react_agent` — the API that LangChain's v1 migration guide now supersedes with `langchain.agents.create_agent` (see `LC-05`, `SH-02`). Anyone reading LangChain's "give an LLM tools, call it, execute tool calls, repeat" description in `LC-01` is reading a productized ReAct loop.

Paper site: [react-lm.github.io](https://react-lm.github.io/) · Code: [ysymyth/ReAct](https://github.com/ysymyth/ReAct)

## AC-01.3 — Reflexion: self-critique loops

**Shinn, N., et al. (2023). "Reflexion: Language Agents with Verbal Reinforcement Learning."** arXiv:2303.11366, NeurIPS 2023.

Reflexion has agents verbally reflect on task feedback and maintain that reflection in an episodic memory buffer to improve subsequent attempts — reinforcement learning through language rather than weight updates.

**Direct relevance:** LangGraph ships a Reflexion tutorial, and the pattern maps cleanly onto the graph model — the reflection step is a node, the retry decision is a conditional edge, and the reflection buffer is state (see `LG-02`, `LG-03`). LangChain's `RubricMiddleware`, which applies LLM-as-judge grading for self-evaluation and iteration (see `LC-06`), is a productized instance of this idea.

Code: [noahshinn/reflexion](https://github.com/noahshinn/reflexion)

## AC-01.4 — The single-agent pattern family

LangGraph publishes tutorials implementing four distinct single-agent architectures, each traceable to research. **ReAct** (AC-01.2) interleaves thought and action. **Plan-and-Execute** separates a planning phase from execution, reducing per-step model calls. **ReWOO (Reasoning WithOut Observation)** decouples reasoning from observation to cut token consumption by planning the full tool sequence upfront. **Reflexion** (AC-01.3) adds self-critique.

The practical distinction is cost and latency shape. ReAct calls the model once per step, so cost scales with trajectory length — which is exactly the compounding effect measured in `SH-10`. Plan-and-Execute and ReWOO front-load planning to reduce that call count. Choosing among them is an architectural decision with direct token-bill consequences, not a stylistic one.

LangChain's [Reflection Agents blog post](https://www.langchain.com/blog/reflection-agents) covers the reflection family; LangGraph tutorials exist for ReWOO and Reflexion.

## AC-01.5 — How to use these papers with this corpus

Three practical uses. **Vocabulary alignment:** when documentation or a tutorial says "ReAct agent," it means the AC-01.2 loop — the term is load-bearing, not marketing. **Debugging intuition:** the failure modes these papers describe (unbounded trajectories, reflection that fails to converge) are the same ones that surface as `GraphRecursionError` and runaway cost in `SH-07` and `SH-10`. **Design selection:** the pattern family in AC-01.4 is the menu you are actually choosing from when you configure an agent, whether or not the framework names it.

## Sources

- [ReAct — arXiv:2210.03629](https://arxiv.org/abs/2210.03629) — accessed 2026-08-13 (Tier 1, foundational)
- [ReAct project site](https://react-lm.github.io/) · [ysymyth/ReAct](https://github.com/ysymyth/ReAct) — accessed 2026-08-13 (Tier 1)
- [Reflexion — arXiv:2303.11366](https://arxiv.org/abs/2303.11366) — accessed 2026-08-13 (Tier 1, foundational)
- [noahshinn/reflexion](https://github.com/noahshinn/reflexion) — accessed 2026-08-13 (Tier 1)
- [LangChain: Reflection Agents](https://www.langchain.com/blog/reflection-agents) — accessed 2026-08-13 (Tier 1)
