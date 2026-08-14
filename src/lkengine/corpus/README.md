# LangChain & LangGraph Research Corpus

A verified, source-tiered, embedding-ready knowledge corpus covering **LangChain** and **LangGraph** — official API documentation, versioning, MCP integration, security advisories, troubleshooting, community findings, academic literature, and production guidance.

**Compiled:** 2026-08-13 · **37 documents** · **220 addressable sections** · **~31,400 words** · **5 series** · every claim cited and confidence-tiered.

---

## 1. What this is

This corpus was built to be **loaded into a RAG system** and queried by an agent or a developer. It is not a tutorial and not a blog. Every section is a self-contained, individually addressable unit of knowledge with its own provenance attached, so a retrieved chunk carries enough context to be trusted and cited on its own.

Three properties make it different from scraping the docs yourself:

**It is verified, not summarized.** Version numbers come from the PyPI JSON API, not from articles. CVEs are checked against GitHub Security Advisories, Snyk, Tenable, and the GitLab Advisory Database. GitHub issue states were confirmed by direct fetch. Where a claim could not be verified, it says so rather than guessing.

**It carries confidence tiers.** Tier 1 is primary/official, Tier 2 is corroborated secondary, Tier 3 is single-source and explicitly flagged. Your RAG system can filter or weight on this.

**It documents its own gaps.** Stack Overflow was inaccessible from the compilation environment; nothing was fabricated to cover that. Sampling limitations on GitHub issues are stated in the document that uses them.

---

## 2. Directory structure

```
corpus/
├── README.md                  ← you are here
├── _meta/
│   ├── INDEX.md               Full manifest, reading paths, chunking guide
│   ├── METHODOLOGY.md         Recency policy, tier definitions, integrity gates, gaps
│   ├── SOURCE-REGISTER.md     Every source with tier, date, consuming documents
│   └── manifest.csv           Machine-readable file index for ingestion
├── langchain/    (LC-01…08)   LangChain-specific: models, tools, agents, middleware, RAG
├── langgraph/    (LG-01…10)   LangGraph-specific: graph API, state, persistence, streaming, HITL
├── shared/       (SH-01…11)   Cross-cutting: versions, MCP, security, troubleshooting, criticism
├── academic/     (AC-01…05)   Research literature: foundations, RAG lineage, Pregel, studies, security
└── rag/                       Deployment: pgvector schema, BGE-M3 ingest, hybrid search, 30-question eval set
```

**Why product separation matters for RAG:** LangChain and LangGraph questions have different correct answers, and merging them causes retrieval to return LangGraph internals for a LangChain question. Every document carries a `product` field (`LangChain` / `LangGraph` / `both`) in its frontmatter — filter on it.

---

## 3. Quick start: ingesting this corpus for RAG

### 3.1 Recommended chunking strategy

**Chunk on `##` headings. Do not use a fixed-size splitter.**

Every section is written as a self-contained unit with a globally unique ID (`LG-04.3`, `SH-06.5`, `AC-01.2`). Sections run 120–450 words, which fits inside standard 512- and 1024-token budgets without further splitting. A character-count splitter will cut mid-argument and destroy the self-containment property this corpus was written to have.

```python
import re, yaml, glob

def load_corpus(root="corpus"):
    chunks = []
    for path in glob.glob(f"{root}/**/*.md", recursive=True):
        raw = open(path).read()
        # Split YAML frontmatter from body
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
        if not m:
            continue
        meta, body = yaml.safe_load(m.group(1)), m.group(2)

        # Split on section headings, keeping the heading with its content
        parts = re.split(r"\n(?=## )", body)
        for part in parts:
            heading = part.split("\n", 1)[0].lstrip("# ").strip()
            sec_id = re.match(r"((?:LC|LG|SH|AC|META)-\d+\.\d+)", heading)
            if not sec_id:
                continue  # skips the H1 title block and the Sources footer
            chunks.append({
                "text": f"# {meta['title']}\n\n{part.strip()}",
                "metadata": {
                    "section_id": sec_id.group(1),
                    "doc_id": meta["doc_id"],
                    "doc_title": meta["title"],
                    "series": meta["series"],
                    "product": meta["product"],
                    "source_tier": meta.get("source_tier"),
                    "recency_class": meta.get("recency_class", "current"),
                    "version_scope": meta.get("version_scope"),
                    "last_verified": str(meta["last_verified"]),
                    "tags": meta.get("tags", []),
                    "path": path,
                },
            })
    return chunks
```

Note the `text` field prepends the **document title** to each chunk. This is deliberate: it gives the embedding model document-level context for a section that might otherwise read ambiguously in isolation.

**This loader was executed against this corpus and validated.** Measured output:

| Metric | Value |
|---|---|
| Chunks produced | **220** |
| Unique `section_id`s | 220 (**zero duplicates**) |
| Words per chunk — median | **124** |
| Words per chunk — mean / min / max | 136 / 37 / 524 |
| Chunks over 500 words | **1** (`META-00.1`, the manifest table) |
| Product distribution | `both` 110 · `LangGraph` 63 · `LangChain` 45 |

A median of 124 words is roughly 165–190 tokens, so every chunk fits a 512-token budget with headroom and no chunk needs secondary splitting. The single 524-word chunk is a reference table; split it further only if your budget is tight.

A pre-generated machine-readable index of all 37 documents — including per-document section counts, section ID lists, word counts, and tags — is at **`_meta/manifest.csv`** if you prefer to drive ingestion from that rather than walking the tree.

### 3.2 Metadata fields and what to do with each

| Field | Type | Use it for |
|---|---|---|
| `section_id` | string | Stable citation anchor and primary key. Never changes. |
| `doc_id` | string | Grouping chunks by document; resolving `see LG-04` cross-references. |
| `product` | enum | **Pre-filter.** `LangChain` / `LangGraph` / `both`. |
| `series` | enum | `LC` / `LG` / `SH` / `AC` / `META`. Filter `AC` out for how-to questions. |
| `source_tier` | 1–3 | **Rank/weight.** Prefer Tier 1 when answers conflict. |
| `recency_class` | enum | `current` (version-sensitive) vs `foundational` (papers, never stale). |
| `version_scope` | string | Show in citations so users see what version an answer applies to. |
| `last_verified` | date | Staleness warnings. |
| `tags` | list | Hybrid/keyword search and faceting. |

### 3.3 Suggested retrieval configuration

**Embedding.** Any general-purpose text embedding model works; the corpus is plain technical English with code identifiers. If your model supports it, embed the `text` field as constructed above (title + section).

**Hybrid search is strongly recommended.** Much of this corpus turns on exact identifiers — `InvalidUpdateError`, `with_structured_output`, `CVE-2026-34070`, `langgraph.json`, `wrap_model_call`. Dense retrieval alone handles these poorly. Combine BM25/keyword with dense vectors and fuse (RRF works well).

**Top-k.** Start at k=6–8. Sections are dense and cross-referenced, so a correct answer often needs 2–3 sections plus one cross-referenced document.

**Filter before ranking.** For a question mentioning LangGraph, pre-filter `product in ("LangGraph", "both")`. For "how do I" questions, consider excluding `series == "AC"`. For security questions, boost `tags contains "security"`.

**Cross-reference expansion.** After retrieval, scan chunk text for `` `LG-04` ``-style references and optionally pull those documents' section 1 as additional context. This corpus deliberately uses explicit IDs rather than "as described above" so this expansion is mechanical.

### 3.4 System prompt guidance for a RAG agent over this corpus

Tell your agent these four things, because they materially change answer quality:

1. **Cite by `section_id`.** Answers should reference `LG-07.2` rather than "the docs say," so users can verify.
2. **Surface the tier.** If an answer rests on a Tier 3 claim, say so. `SH-02.5` (the unverified `AgentExecutor` EOL date) exists specifically to prevent confident repetition of a wrong claim.
3. **Surface `version_scope` and `last_verified`.** Version-sensitive answers should carry the date they were verified.
4. **Never state a current version number from this corpus as live fact.** Direct users to PyPI. `SH-01.1` explains why.

---

## 4. What's in each series

### `langchain/` — LC-01 to LC-08
Overview and three-tier positioning · chat models, messages, and content blocks · tools and tool calling · structured output and its silent failure modes · `create_agent` · the middleware system and its 20 prebuilt classes · retrieval and RAG · Deep Agents.

### `langgraph/` — LG-01 to LG-10
Core model and Pregel lineage · the Graph API · state, reducers, `Command`, `Send` · persistence and checkpointers · short- and long-term memory · streaming's seven modes · human-in-the-loop and interrupt semantics · subgraphs · the Functional API and durable execution · deployment, CLI, and `langgraph.json`.

### `shared/` — SH-01 to SH-11
Verified package/version matrix · versioning policy and migration · MCP integration and LangChain's open-source `mcpdoc` server · language support · LangSmith observability and evaluation · **security advisories and CVEs** · error reference and troubleshooting · GitHub issue analysis · community and learning resources · triangulated criticism · **the 22-item must-knows checklist**.

### `academic/` — AC-01 to AC-05
Foundational agent papers (ReAct, Reflexion) · RAG research lineage (Lewis 2020, Self-RAG, CRAG) · systems lineage (Pregel/BSP, and why LangGraph behaves as it does) · **empirical studies of LangChain itself** · security research literature.

### `_meta/`
Index and reading paths · methodology, integrity gates, and documented gaps · complete source register.

---

## 5. Where to start reading (human, not RAG)

| Goal | Path |
|---|---|
| New to the stack | `LC-01` → `LG-01` → `LC-05` → `LG-02` → `SH-11` |
| Shipping to production | `SH-06` (patch first) → `SH-01` → `LG-04` → `LG-10` → `SH-05` |
| Debugging something | `SH-07` (start at the silent-failure list) → relevant LC/LG doc → `SH-08` |
| Evaluating adoption | `AC-04` → `SH-10` → `LC-01` → `LG-01` → `SH-04` |
| Building agents | `LC-05` → `LC-06` → `LC-03` → `LC-04` → `LG-07` → `LC-08` |
| Understanding *why* LangGraph is weird | `AC-03` → `LG-01` → `LG-03` |
| Security review | `SH-06` → `AC-05` → `LG-04` → `LG-10` |

**If you read one document:** `SH-11`, the must-knows checklist. **If you read two:** add `SH-06`, the CVE register.

---

## 6. Known limitations — read before relying on this

These are disclosed so you can fill them deliberately. Full detail in `_meta/METHODOLOGY.md`.

- **Version numbers are a dated snapshot.** Every core package shipped a release within two weeks of compilation. Re-query PyPI for anything you will pin.
- **Two API details remain unverified:** middleware composition ordering with stacked middleware, and the narrative durable-execution page (the `Durability` type values themselves *are* verified). Both are flagged in place.
- **One Tier 3 claim is deliberately retained and flagged:** the "`AgentExecutor` EOL December 2026" date, which could not be found in official documentation. See `SH-02.5`.

---

## 7. Keeping it current

Three things decay at different rates:

- **Version numbers (`SH-01`)** — days to weeks. Re-query `https://pypi.org/pypi/<package>/json`.
- **CVE register (`SH-06`)** — weeks to months. Check GitHub Security Advisories for `langchain-ai/*`.
- **API specifics (LC/LG series)** — months. Diff against `https://docs.langchain.com/llms.txt`, the official machine-readable docs index, which enumerates every page as a `.md` URL.

The `academic/` series (`recency_class: foundational` in AC-01 through AC-03) does not decay. AC-04 and AC-05 are `current` and should be refreshed with new literature.

**Recommended refresh cadence:** monthly for `SH-01` and `SH-06`, quarterly for everything else.

---

## 8. A note on how this was built

Every factual claim traces to a retrievable artifact. Roughly 45 official documentation pages and repository artifacts were fetched directly; 20 packages were queried against the PyPI JSON API; 6 CVEs were verified against authoritative vulnerability databases; 4 GitHub issues were confirmed by direct fetch; and 9 academic papers were located and verified for title, authorship, and date.

Four defects from earlier compilation passes are documented in `_meta/METHODOLOGY.md` rather than quietly patched — including two wrong version numbers and one uncorroborated EOL date inherited from secondary sources. That section is the most useful part of the methodology document, because the failure mode it describes (trusting prose for facts a registry can settle) is the one most likely to degrade this corpus over time.
