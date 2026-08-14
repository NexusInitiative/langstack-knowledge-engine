---
doc_id: LG-05
title: LangGraph — Memory (short-term & long-term)
series: LG
product: LangGraph
version_scope: langgraph 1.x
last_verified: 2026-08-13
source_tier: 1
tags: [memory, Store, InMemoryStore, namespaces, semantic-search, trim_messages, RemoveMessage, summarization, TTL]
---

# LG-05 — Memory: Short-Term & Long-Term

## LG-05.1 — Two memory systems, two scopes

LangGraph separates memory into two systems with different scopes, and choosing the wrong one is a common design error.

**Short-term memory** is the checkpointer. It is **thread-scoped** — it holds the conversation and working state for one thread, enabling multi-turn conversation. Enabled by compiling with a checkpointer and passing a `thread_id`. Covered in `LG-04`.

**Long-term memory** is the **`Store`**. It is **cross-thread** — it holds application-defined key-value data that must outlive any single conversation, such as user preferences, learned facts, and shared knowledge.

The rule of thumb: if the data belongs to *this conversation*, it goes in state and is checkpointed. If it belongs to *this user across all conversations*, it goes in the Store. **Tier 1** ([add-memory docs](https://docs.langchain.com/oss/python/langgraph/add-memory)).

## LG-05.2 — Store implementations and access

`InMemoryStore` serves development and supports optional semantic search. Production backends include **PostgresStore**, **RedisStore**, **MongoDB**, and **Oracle**; like the database checkpointers, these require an initial **`setup()`** call.

Stores are reached inside nodes through the `Runtime` object:

```python
await runtime.store.aput(namespace, key, value)
results = await runtime.store.asearch(namespace, query=...)
```

The core operations are put, get, and search, each with sync and async forms.

## LG-05.3 — Namespaces

Store data is organized by **namespace** — a tuple such as `("memories", "alice")` — which scopes and isolates entries. Namespaces are the natural way to separate users, tenants, or memory categories.

**A security caveat applies directly here.** CVE-2026-71433 documented that the Postgres and SQLite stores serialized hierarchical namespaces as dot-joined strings and matched scoped reads with `LIKE '<path>%'`. Because `LIKE` does not respect the dot separator, reads could match sibling namespaces sharing leading characters, crossing what applications treated as tenant boundaries — with no crafted input required. Fixed in 3.1.1. If you use namespaces as a tenancy boundary, patch to at least that version and enforce tenancy in your own authorization layer as well. See `SH-06`.

## LG-05.4 — Semantic search over memory

Stores support semantic search by supplying an embedding model and dimension specification at initialization. Retrieval then happens by meaning rather than exact key, via `store.asearch(namespace, query=...)`.

This makes the Store a genuine alternative to a vector-store retriever for *user-scoped* knowledge. The distinction from RAG in `LC-07` is scope and ownership: a vector store retriever is designed for a shared document corpus, while the Store is designed for per-user or per-namespace memory that accumulates over time. Using a document-RAG pipeline to hold user memories, or the Store to hold a large shared corpus, both work badly.

## LG-05.5 — Managing conversation history

When a conversation outgrows the context window, three documented strategies apply.

**Trim.** `trim_messages()` keeps a bounded recent window using token counting.

**Delete.** `RemoveMessage` removes specific messages by ID, and the **`REMOVE_ALL_MESSAGES`** sentinel clears the history entirely. This works because `add_messages` performs ID-based overwrite (see `LG-03`).

**Summarize.** Generate a summary with the model, then delete the older messages it replaces — preserving meaning at a fraction of the token cost.

LangChain provides these as prebuilt middleware for agents: `SummarizationMiddleware` and `ContextEditingMiddleware` (see `LC-06`), so agent builders generally should not hand-roll them.

## LG-05.6 — Why history management is a cost control, not just a context fix

Trimming and summarization are frequently treated as a way to avoid context-length errors. The measured evidence in `SH-10` shows they are more consequentially a **cost** control. In a study of 66 real agent sessions, input tokens exceeded output tokens by roughly 1.9:1, and per-step cost at step 200 was around 100× the cost at step 1 for equivalent work — because each step re-bills the entire accumulated context. Raw tool output was identified as the largest single input-cost driver.

That is the strongest available argument for `ContextEditingMiddleware`'s specific behavior of clearing older *tool outputs*: it targets the dominant cost term directly. Memory management in LangGraph should be designed with the token bill in view, not only the context limit.

## Sources

- [Add memory — official docs](https://docs.langchain.com/oss/python/langgraph/add-memory) — accessed 2026-08-13 (Tier 1)
- [Memory overview — official docs (JS)](https://docs.langchain.com/oss/javascript/langgraph/memory) — accessed 2026-08-13 (Tier 1)
- [Prebuilt middleware — official docs](https://docs.langchain.com/oss/python/langchain/middleware/built-in) — accessed 2026-08-13 (Tier 1)
- [GitLab Advisory: CVE-2026-71433](https://advisories.gitlab.com/pypi/langgraph-checkpoint-postgres/CVE-2026-71433/) — accessed 2026-08-13 (Tier 1)
- [LangChain Forum: token cost of long agent runs, 66 sessions measured](https://forum.langchain.com/t/the-token-cost-of-long-agent-runs-compounds-harder-than-i-expected-i-measured-66-real-sessions/4240) — accessed 2026-08-13 (Tier 1)
