---
doc_id: SH-11
title: Must-Knows Checklist
series: SH
product: both
version_scope: LangChain 1.x / LangGraph 1.x
last_verified: 2026-08-13
source_tier: 1
tags: [checklist, must-know, gotchas, summary, best-practices, quickref]
---

# SH-11 — Must-Knows Checklist

## SH-11.1 — Security must-knows

**1. Patch before anything else.** Six CVEs affected this stack between December 2025 and 2026, including a 9.2–9.3 critical serialization-injection flaw in `langchain-core` ("LangGrinch," CVE-2025-68664) that leaked environment secrets, and a pickle-fallback RCE in `langgraph-checkpoint` (CVE-2026-27794). Minimum safe versions: `langchain-core` ≥1.2.22, `langgraph-checkpoint` ≥4.0.0, `langgraph-checkpoint-sqlite` ≥3.1.1, `langgraph-checkpoint-postgres` ≥3.1.1, `@langchain/langgraph-checkpoint-mongodb` ≥1.3.1. See `SH-06`.

**2. `thread_id` and store namespaces are not security boundaries.** Two separate CVEs showed both crossable — NoSQL operator injection through `config.configurable` (CVE-2026-48121) and `LIKE`-based namespace prefix matching crossing tenant boundaries (CVE-2026-71433). Enforce tenancy in your own authorization layer. See `SH-06`, `LG-04`, `LG-05`.

**3. Untrusted content reaches serialization paths.** LangGrinch's realistic vectors included LLM response fields such as `additional_kwargs` and `response_metadata` — meaning model output itself is an attack surface, not just user input. See `SH-06`.

## SH-11.2 — Architecture must-knows

**4. LangChain runs on LangGraph now.** `create_agent` is implemented on the LangGraph runtime, so checkpointers, stores, interrupts, and streaming surface directly through LangChain agent parameters. Choosing LangChain does not mean avoiding LangGraph. See `LC-01`, `LC-05`.

**5. Three tiers, pick deliberately.** LangGraph for custom control flow; `create_agent` for the standard tool-calling loop with middleware; Deep Agents for long-horizon work needing filesystem, planning, and subagents pre-wired. If you find yourself stacking filesystem, todo, and subagent middleware onto `create_agent`, you are rebuilding Deep Agents. See `LC-01`, `LC-08`.

**6. Legacy agent APIs are superseded.** Official guidance is `create_agent` over `create_react_agent`; legacy chains move to `langchain-classic`. The widely-cited "`AgentExecutor` EOL December 2026" date is **unverified** and could not be found in official docs — the officially documented December 2026 date applies to the 0.3/0.4 maintenance lines. See `SH-02`, `LC-05`.

**7. Read the middleware catalogue before writing custom code.** Twenty prebuilt middlewares cover summarization, HITL, PII, retries, fallbacks, call limits, tool selection, filesystem, subagents, and rubric grading. Most production hardening people hand-roll already exists. See `LC-06`.

## SH-11.3 — LangGraph runtime must-knows

**8. `interrupt()` restarts the entire node on resume.** It does not resume mid-function. Code before the interrupt runs again — so never place non-idempotent side effects there, never wrap `interrupt()` in try/except (it swallows the control-flow exception and silently disables pausing), and never call it in a loop (each resume replays all prior iterations). Use conditional edges to route back instead. See `LG-07`.

**9. Concurrent writes need reducers.** Multiple outgoing edges execute in parallel; two nodes writing one state key without a reducer raises `InvalidUpdateError`. Attach reducers via `Annotated` when you design the schema, not after the first error. `Send` fan-out always needs one. See `LG-03`.

**10. Checkpoints go to the database, not pod memory.** High pod memory means large objects in your node code, not checkpoint accumulation. Conversely, database growth is unbounded without TTL — configure `checkpointer.ttl` in `langgraph.json`, use `durability="exit"`, or keep large payloads in external storage with only a reference in state. See `LG-04`, `LG-10`.

**11. Sync/async checkpointer mismatch hangs rather than errors.** An async checkpointer with sync `invoke`, `get_state`, or `get_state_history` produces a silent hang. If a graph hangs, check this first. See `LG-04`, `SH-07`.

**12. Subgraph checkpointer mode is three-valued and consequential.** `None` (per-invocation, recommended default), `True` (per-thread, accumulates — and conflicts under parallel invocation), `False` (stateless). A `GraphRecursionError` in a parent containing a per-thread subgraph is a signal to check that mode. See `LG-08`.

**13. Compile-time versus runtime checkpointer resolution diverges in deployment.** The API Server injects the checkpointer at runtime; `@task` resolves it at compile time and therefore re-executes tasks on resume. Test HITL and persistence end-to-end in the deployment environment, not just locally. See `LG-09`, `LG-10`.

## SH-11.4 — Model and tool must-knows

**14. Structured output is provider-specific and fails silently.** `ProviderStrategy` uses native APIs; `ToolStrategy` emulates via tool calls. Chaining `.bind(tools=[...])` then `.with_structured_output(schema)` **silently drops the tools** (issue #35320, verified open) — you get valid JSON while the model hallucinates. Test against the exact model and provider you ship on. Note `strict` requires langchain ≥1.2. See `LC-04`.

**15. Tool type hints are mandatory and docstrings are prompts.** Type hints define the input schema; the docstring is what the model reads to decide when to call the tool. `ToolRuntime` is the current injection pattern — `InjectedState` is superseded. See `LC-03`.

**16. Stream format versions differ by surface.** LangGraph `.stream()` documents `version="v2"` with the unified `StreamPart` shape; LangChain `agent.stream_events()` documents `version="v3"`. Different APIs, independently versioned. Never parse stream output by positional unpacking. See `LG-06`, `LC-05`.

## SH-11.5 — Operational must-knows

**17. Python floor is 3.10, not 3.8.** Core packages require ≥3.10, `deepagents` ≥3.11, and `langgraph.json` accepts only 3.11/3.12/3.13 (default 3.11). See `SH-01`, `LG-10`.

**18. Only Python and JS/TS are official.** `langchain4j` (Java) and `langchaingo` (Go) are independent community projects with separate maintainers, versioning, and security posture. Nothing in the `LC-*`/`LG-*` series is guaranteed to apply. See `SH-04`.

**19. Cost is a multiplier, not a constant.** Measured across 66 real sessions: ~1.9:1 input-to-output token ratio and per-step cost at step 200 running ~100× step 1, because each step re-bills accumulated context, with raw tool output the largest driver. Design context management as cost control, not just context-limit avoidance. See `SH-10`, `LG-05`.

**20. Pin versions and read release notes.** 509 releases of `langchain`, 276 of `langgraph`, 520 of `langsmith`. Query PyPI's JSON API for current versions rather than trusting any article — including this corpus, which is a dated snapshot. See `SH-01`.

**21. Use `llms.txt` and `mcpdoc` for docs ingestion.** `https://docs.langchain.com/llms.txt` is the official machine-readable documentation index, and `langchain-ai/mcpdoc` is LangChain's open-source MCP server for serving `llms.txt` sources to IDEs and agents. This is the supported path for building a docs corpus or RAG index. See `SH-03`.

**22. Abstraction complexity is maintainer-acknowledged.** LangChain's co-founder publicly agreed with the best-known "we dropped LangChain" critique and pointed to LangGraph and standardized interfaces as the answer. Weight criticism by vintage — most widely-circulated critiques describe the 0.x chain-heavy design that 1.0 substantially replaced. See `SH-10`.

## Sources

This checklist synthesizes `LC-01` through `LC-08`, `LG-01` through `LG-10`, and `SH-01` through `SH-10`. Each item cites the source document carrying its full provenance and citations.
