---
doc_id: META-00
title: Corpus Index & Chunking Guide
series: META
product: both
last_verified: 2026-08-13
tags: [index, manifest, chunking, embedding, navigation]
---

# META-00 — LangChain & LangGraph Corpus Index

A verified, product-separated, embedding-ready reference corpus for **LangChain** and **LangGraph**, compiled **2026-08-13**. **37 documents** across five directories — 34 content documents plus 3 provenance documents — containing **220 uniquely-addressable sections** and ~31,400 words, every claim source-tiered and cited.

**Start with `README.md` at corpus root** for RAG ingestion guidance, a validated loader, and chunking statistics. This file is the detailed manifest.

## META-00.1 — Manifest

### `langchain/` — LangChain-specific (LC series, 8 docs)

| ID | File | Covers |
|---|---|---|
| LC-01 | `LC-01-overview-and-architecture.md` | Positioning, three-tier model, package architecture, v1 shift, docs surfaces |
| LC-02 | `LC-02-models-and-messages.md` | `init_chat_model`, invoke/stream/batch, message classes, `.content_blocks`, rate limiting, caching, usage tracking |
| LC-03 | `LC-03-tools-and-tool-calling.md` | `@tool`, `bind_tools`, `args_schema`, `ToolNode`, `ToolRuntime`, error handling, `return_direct` |
| LC-04 | `LC-04-structured-output.md` | `response_format`, `ProviderStrategy` vs `ToolStrategy`, schema formats, retries, silent failure modes |
| LC-05 | `LC-05-agents-create-agent.md` | `create_agent` parameters, agent loop, context vs state schema, migration, multi-agent |
| LC-06 | `LC-06-middleware.md` | Hook points, 20 prebuilt middleware classes, selection guidance |
| LC-07 | `LC-07-retrieval-and-rag.md` | Loaders, splitters, embeddings, vector stores, retrievers, 2-step/agentic/hybrid RAG |
| LC-08 | `LC-08-deep-agents.md` | `create_deep_agent`, four pillars, `interrupt_on`, relationship to middleware |

### `langgraph/` — LangGraph-specific (LG series, 10 docs)

| ID | File | Covers |
|---|---|---|
| LG-01 | `LG-01-overview-and-core-model.md` | Positioning, Pregel lineage, supersteps, two authoring APIs, adoption |
| LG-02 | `LG-02-graph-api.md` | `StateGraph`, nodes, edges, conditional edges, `START`/`END`, `compile()` |
| LG-03 | `LG-03-state-reducers-command-send.md` | Reducers via `Annotated`, `add_messages`, `MessagesState`, `Command`, `Send` |
| LG-04 | `LG-04-persistence-and-checkpointers.md` | Checkpointer backends, threads, state inspection, TTL, connection pooling |
| LG-05 | `LG-05-memory-short-and-long-term.md` | Store, namespaces, semantic search, trimming/summarization, cost framing |
| LG-06 | `LG-06-streaming.md` | Seven stream modes, `StreamPart` v2, `get_stream_writer`, subgraph streaming |
| LG-07 | `LG-07-human-in-the-loop-interrupts.md` | `interrupt()`, node-restart semantics, try/except prohibition, loops, breakpoints, time travel |
| LG-08 | `LG-08-subgraphs.md` | Attachment patterns, three checkpointer modes, parallel conflicts, namespace isolation |
| LG-09 | `LG-09-functional-api-durable-execution.md` | `@entrypoint`, `@task`, determinism, replay, durability modes |
| LG-10 | `LG-10-deployment-cli-platform.md` | CLI commands, `langgraph.json` keys, security config, runtime injection, Platform |

### `shared/` — Cross-cutting (SH series, 11 docs)

| ID | File | Covers |
|---|---|---|
| SH-01 | `SH-01-package-and-version-matrix.md` | 20-package verified version/Python-floor matrix from PyPI, package topology |
| SH-02 | `SH-02-versioning-and-migration.md` | SemVer policy, LTS windows, release timeline, migration, unverified EOL claim |
| SH-03 | `SH-03-mcp-integration-and-servers.md` | `langchain-mcp-adapters`, transports, `mcpdoc` open-source MCP server, `llms.txt` |
| SH-04 | `SH-04-language-support.md` | Python/JS official, Python↔JS divergences, `langchain4j`, `langchaingo` |
| SH-05 | `SH-05-observability-and-evaluation.md` | LangSmith tracing, datasets, evaluators, experiments, `RubricMiddleware` |
| SH-06 | `SH-06-security-advisories-cves.md` | Six CVEs with affected/fixed versions, scores, minimum-safe guidance |
| SH-07 | `SH-07-error-reference-and-troubleshooting.md` | Exception reference, silent-failure catalogue, debugging toolkit, triage path |
| SH-08 | `SH-08-github-issues-solved-and-open.md` | Verified issues, thematic clusters, resolution patterns, sampling caveats |
| SH-09 | `SH-09-community-forums-learning.md` | Forum, Academy, tutorials, staleness markers, Stack Overflow gap |
| SH-10 | `SH-10-criticism-and-production-reality.md` | Triangulated criticism, Octomind/HN, measured cost, fit guidance |
| SH-11 | `SH-11-must-knows-checklist.md` | 22 must-knows across security, architecture, runtime, models, operations |

### `academic/` — Research literature (AC series, 5 docs)

| ID | File | Covers |
|---|---|---|
| AC-01 | `AC-01-foundational-agent-papers.md` | ReAct (arXiv:2210.03629), Reflexion (arXiv:2303.11366), single-agent pattern family, dual-recency rationale |
| AC-02 | `AC-02-rag-research-lineage.md` | RAG (Lewis 2020), Self-RAG (2310.11511), CRAG (2401.15884), Adaptive RAG, cost implications |
| AC-03 | `AC-03-systems-lineage-pregel.md` | Pregel/BSP (SIGMOD 2010) and why supersteps, reducers, checkpoints and durability modes behave as they do |
| AC-04 | `AC-04-empirical-studies-of-langchain.md` | Four studies incl. 1,575-repo and 42,267-commit analyses, a LangGraph practitioner paper, and a peer-reviewed taxonomy survey |
| AC-05 | `AC-05-security-research-literature.md` | Agent threat taxonomy, P2SQL, retrieval poisoning, MCP protocol security, multi-tenancy convergence |

### `_meta/` — Provenance (META series, 3 docs + manifest)

| ID | File | Covers |
|---|---|---|
| META-00 | `INDEX.md` | This file — manifest, chunking guide, reading paths |
| META-01 | `METHODOLOGY.md` | Dual-recency policy, tier definitions, four integrity gates, documented gaps, corrections, second-pass verification log |
| META-02 | `SOURCE-REGISTER.md` | Every source with tier, date, and consuming documents |
| — | `manifest.csv` | Machine-readable index: path, doc_id, series, product, tier, recency_class, section count, section IDs, word count, tags |

## META-00.2 — Chunking and embedding guide

The corpus is written to survive mechanical chunking.

**Chunk on section headings.** Every section carries a globally unique ID of the form `<DOC-ID>.<n>` — `LG-04.3`, `SH-06.5` — used as its heading prefix. Split on `##` boundaries and each chunk arrives with a stable primary key.

**Preserve frontmatter as metadata, not body text.** Each file's YAML block carries `doc_id`, `title`, `series`, `product`, `version_scope`, `last_verified`, `source_tier`, `recency_class`, and `tags`. Attach these as chunk metadata. `product` (LangChain / LangGraph / both) is the field to filter on for product-scoped retrieval — it is the reason the corpus is separated by product rather than merged. `recency_class` distinguishes version-sensitive material (`current`) from non-expiring academic foundations (`foundational`); see `META-01.1`.

**Measured chunking statistics.** Running the reference loader in `README.md` §3.1 against this corpus produces **220 chunks with zero duplicate section IDs**, a median of **124 words** per chunk (mean 136, min 37, max 524), and exactly one chunk above 500 words — `META-00.1`, the manifest table in this file. Product distribution is `both` 110, `LangGraph` 63, `LangChain` 45.

**Sections are self-contained.** Each opens by restating its subject rather than relying on a pronoun pointing at the previous section, so an isolated chunk still reads correctly. Sections run roughly 120–450 words, fitting comfortably inside 512- and 1024-token budgets without further splitting.

**Cross-references are explicit IDs.** References use `see LG-04`, never "as described above," so relationships survive chunk reordering and can be resolved into a graph if you want link-aware retrieval.

**Tier labels travel with claims.** Provenance appears inline next to claims, not only in the trailing source list, so a chunk separated from its file footer still carries its confidence level.

**Tables are for reference data only.** Version matrices, the CVE register, and the error reference use tables where row-wise chunking is acceptable. Conceptual material is prose, because tables embed poorly.

## META-00.3 — Suggested reading paths

**New to the stack:** LC-01 → LG-01 → LC-05 → LG-02 → SH-11.

**Shipping to production:** SH-06 (patch first) → SH-01 → LG-04 → LG-10 → SH-05 → SH-11.

**Debugging something broken:** SH-07 (start at the silent-failure catalogue) → the relevant LG/LC document → SH-08.

**Evaluating whether to adopt:** SH-10 → LC-01 → LG-01 → SH-04 → SH-02.

**Building agents specifically:** LC-05 → LC-06 → LC-03 → LC-04 → LG-07 → LC-08.

**Ingesting the official docs into your own index:** SH-03 (`llms.txt` and `mcpdoc`) → META-01.

## META-00.4 — How to keep this current

Three things go stale at different rates. **Version numbers** in SH-01 are a dated snapshot — re-query `https://pypi.org/pypi/<package>/json`. **The CVE register** in SH-06 needs re-checking against GitHub Security Advisories for `langchain-ai/*`. **API specifics** across LC and LG series should be re-verified against `docs.langchain.com/llms.txt`, which enumerates every page as a `.md` URL and is the cheapest way to diff documentation between compilations.

Everything in this corpus is a snapshot dated 2026-08-13, including its own version claims. `META-01` documents what was corrected in earlier passes and why — the same failure mode (trusting prose for facts a registry can settle) is the one most likely to degrade this corpus over time.
