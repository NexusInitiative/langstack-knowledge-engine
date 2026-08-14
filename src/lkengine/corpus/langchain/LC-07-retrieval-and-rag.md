---
doc_id: LC-07
title: LangChain — Retrieval & RAG
series: LC
product: LangChain
version_scope: langchain 1.x, langchain-text-splitters 1.x
last_verified: 2026-08-13
source_tier: 1
tags: [rag, retrieval, embeddings, vector-store, retriever, text-splitter, document-loader, agentic-rag]
---

# LC-07 — Retrieval & RAG

## LC-07.1 — The problem RAG addresses

LangChain frames retrieval-augmented generation as "enhancing an LLM's answers with context-specific information" by fetching relevant external knowledge at query time, compensating for the model's fixed training data and bounded context window. RAG remains one of the two use cases LangChain is most consistently recommended for in practice (the other being straightforward tool-calling agents), per the fit guidance in `SH-10`. **Tier 1** ([retrieval docs](https://docs.langchain.com/oss/python/langchain/retrieval)).

## LC-07.2 — The five components

The pipeline is built from five component types, each a swappable interface.

**Document loaders** ingest data from external sources and return standardized `Document` objects. Standardization is the point: downstream stages never need to know whether content came from a PDF, a web page, or a database.

**Text splitters** break large documents into chunks small enough to retrieve individually and to fit a context window. These live in the separately versioned `langchain-text-splitters` package (1.1.2 as of `SH-01`), with `RecursiveCharacterTextSplitter` the conventional default.

**Embedding models** convert text into vectors such that, per the docs, "texts with similar meaning land close together in that vector space."

**Vector stores** are "specialized databases for storing and searching embeddings."

**Retrievers** provide "an interface that returns documents given an unstructured query." The retriever is the abstraction boundary worth designing against, because it lets you swap the entire storage and search strategy underneath without touching the calling code.

## LC-07.3 — The standard indexing and retrieval flow

Indexing runs once per corpus change: documents are loaded, split into chunks, embedded, and written to a vector store. Query time follows the same embedding path — the query is embedded with the same model, similar chunks are retrieved, and those chunks are supplied to the LLM as context.

The requirement that query and documents use **the same embedding model** is the most common silent failure in hand-rolled pipelines: mismatched models produce vectors in incompatible spaces, and retrieval quality collapses without raising an error.

## LC-07.4 — Three RAG architectures

The documentation distinguishes three architectures with different cost and latency profiles.

**2-Step RAG** retrieves then generates, once. It is predictable and fast, and suits FAQ and documentation bots where the retrieval need is obvious from the query.

**Agentic RAG** puts an LLM-powered agent in charge of deciding *when* and *how* to retrieve during its reasoning. This buys flexibility for research-assistant workloads at the cost of unpredictable numbers of retrieval and model calls per query.

**Hybrid RAG** combines both, adding query enhancement, retrieval validation, and answer quality checks for iterative refinement.

The cost implication is direct and is the mechanism behind the "why is my bill higher than expected" pattern in `SH-10`: 2-Step RAG has a bounded call count per query, while agentic and hybrid architectures do not. Agentic RAG in particular can issue many retrieval rounds and model calls for a single user question. If cost predictability matters more than retrieval flexibility, 2-Step is the architecture that gives it to you.

## LC-07.5 — Practical performance expectations

Independent practitioner reporting on standard document-QA pipelines over corpora of roughly 10,000 to 500,000 documents describes retrieval latencies in the 200–800ms range with framework overhead under 50ms per call. These are secondary-source figures rather than benchmarks published by LangChain, and they depend heavily on vector store, index type, and hardware — treat them as an order-of-magnitude expectation rather than a specification. **Tier 3.** See `SH-10` for the sourcing caveats around this material.

## LC-07.6 — Where retrieval intersects the rest of the stack

Retrieval is not isolated from the agent machinery. A retriever is commonly exposed to an agent as a tool (`LC-03`), which is what turns 2-Step RAG into agentic RAG. Retrieved chunks land in message content and therefore count against the context budget every subsequent turn re-transmits — the compounding effect measured in `SH-10` — which is why `SummarizationMiddleware` and `ContextEditingMiddleware` from `LC-06` are relevant to RAG cost control. For cross-session knowledge that is *not* a document corpus, the LangGraph `Store` with semantic search (`LG-05`) is often a better fit than a vector store retriever, since it is designed for user-scoped memory rather than shared document search.

## Sources

- [Retrieval — official docs](https://docs.langchain.com/oss/python/langchain/retrieval) — accessed 2026-08-13 (Tier 1)
- [PyPI: langchain-text-splitters](https://pypi.org/pypi/langchain-text-splitters/json) — accessed 2026-08-13 (Tier 1)
- [Enterprise DNA practitioner report](https://enterprisedna.co/resources/blog/practitioner-langchain-2026/) — accessed 2026-08-13 (Tier 3; see `SH-10` for demotion rationale)
