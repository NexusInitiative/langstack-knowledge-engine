---
doc_id: META-01
title: Corpus Methodology, Integrity Gates & Known Gaps
series: META
product: both
last_verified: 2026-08-13
tags: [methodology, provenance, verification, limitations]
---

# META-01 — Methodology, Integrity Gates & Known Gaps

## META-01.1 — Scope and the dual-recency policy

This corpus documents **LangChain** and **LangGraph** as of **2026-08-13**. Recency is governed by **two policies**, applied according to a document's `recency_class` frontmatter field, because a single window would be wrong for half the material.

**`recency_class: current` — the three-year window.** Applies to everything version-sensitive: APIs, package versions, CVEs, current recommendations, community discourse, and studies *about* the frameworks. Every such source was published or last materially updated within **2023-08-13 → 2026-08-13**. Historical version milestones inside that window (LangChain 0.1 stabilization January 2024, the v0.3 Pydantic 2 migration September 2024) are retained because they explain present-day API shape.

**`recency_class: foundational` — no window.** Applies to seminal academic papers in `AC-01` through `AC-03`. A foundational citation does not expire. Replacing ReAct (Yao et al., 2022), the RAG paper (Lewis et al., 2020), or Pregel (Malewicz et al., 2010) with a recent secondary summary would **reduce** accuracy, not improve it — these are the canonical sources for concepts LangChain and LangGraph productize, and the frameworks' own documentation cites them. Excluding them to satisfy a recency rule would be a methodological error dressed as rigor.

Note that `AC-04` (empirical studies of LangChain) and `AC-05` (security research) are classed **`current`**, not foundational, and do sit inside the three-year window — they make claims about the present state of the frameworks and therefore decay.

**Product separation.** `langchain/` files carry `LC-*` IDs, `langgraph/` files carry `LG-*` IDs, cross-cutting material lives in `shared/` with `SH-*` IDs, and academic literature in `academic/` with `AC-*` IDs. Where the two products intersect — for example, `create_agent` is a LangChain API implemented on a LangGraph runtime — the fact is stated in both series with an explicit cross-reference rather than duplicated silently.

## META-01.2 — Source confidence tiers

Every claim in this corpus carries one of three tiers. Tiers are stated per-section, not per-file.

- **Tier 1 — Primary.** Official LangChain documentation (`docs.langchain.com`, `reference.langchain.com`), official GitHub repositories under `langchain-ai/`, official GitHub Security Advisories, the PyPI JSON API queried directly, and official LangChain-hosted community forum threads. These are authoritative statements from the maintainers or from a canonical registry.
- **Tier 2 — Corroborated secondary.** A claim independently attested by two or more unaffiliated third parties, or by one reputable specialist outlet whose reporting was cross-checked against a primary artifact. Security reporting is Tier 2 when the news article was verified against the underlying CVE record or GitHub advisory.
- **Tier 3 — Single-source / low confidence.** A claim appearing in exactly one secondary source, particularly commercial or SEO-driven content. Tier 3 claims are retained only when useful, and are always labeled inline. They should not be treated as fact without independent confirmation.

## META-01.3 — Integrity gates applied

Four gates were applied before any claim entered this corpus.

**Gate 1 — Primary-source preference.** Where an official docs page exists for a topic, the official page was fetched and used as the basis for the section, rather than a blog summarizing it. Roughly forty official documentation pages and repository artifacts were fetched directly.

**Gate 2 — Registry over prose for anything numeric.** Version numbers, Python floors, and release counts were taken from the **PyPI JSON API** (`https://pypi.org/pypi/<package>/json`), not from articles. This gate exists because the first pass of this research inherited two wrong version numbers from blog posts. See META-01.5.

**Gate 3 — Identifier verification for security claims.** Every CVE cited was checked against at least one authoritative vulnerability record (GitHub Security Advisory, Snyk, Tenable, or GitLab Advisory Database) for its identifier, affected range, fixed version, and score. News coverage alone was never sufficient. Where two authoritative sources disagreed on a CVSS score, both figures are reported rather than one being silently chosen.

**Gate 4 — Falsifiable attribution.** Any claim that cannot be traced to a retrievable artifact was either dropped or explicitly marked as unverified. Paraphrased "developers say…" material with no linkable origin was removed.

## META-01.4 — Documented gaps and access limitations

These are limitations of the compilation environment, disclosed so you can fill them deliberately rather than assuming coverage.

- **Stack Overflow is entirely inaccessible from this environment.** Both direct page fetches and domain-filtered searches against `stackoverflow.com` were rejected at the network proxy (HTTP 403/400). No Stack Overflow content appears in this corpus. This is a real coverage gap for practical Q&A, and it is a gap by access restriction, not by editorial choice — nothing was invented to paper over it. If you need SO coverage, the tags `langchain`, `langgraph`, `langchain-js`, and `py-langchain` sorted by votes are the natural starting points, and the Stack Exchange API (`api.stackexchange.com/2.3/questions?tagged=langchain&sort=votes&site=stackoverflow`) will return structured data from an unrestricted network.
- **GitHub's issue-search endpoints are restricted here.** The GitHub REST search API is scoped away from arbitrary repositories in this environment, and `github.com/<org>/<repo>/issues?q=…` list views are disallowed by robots. Individual issue pages *are* fetchable and several were verified that way. Consequently the issue material in `SH-08` is a **thematically clustered sample with individually verified exemplars**, not an exhaustive or reaction-ranked census. Do not read issue counts or "most upvoted" ordering into it, because that ordering could not be computed.
- **Some official doc pages returned partial content.** A few `docs.langchain.com` fetches returned page shells whose deeper content (for example, exact middleware hook method names on the middleware overview page, and durability-mode parameter values) was not present in the retrieved text. Where this happened, the section says what was confirmed and marks the remainder as not-yet-verified rather than filling it from memory.
- **One registry/repo discrepancy was observed and is unresolved.** The GitHub releases page for `langchain-ai/langgraph` surfaced `1.2.4` as the newest tag at fetch time, while the PyPI JSON API reported `1.2.11` as the current published version on the same day. PyPI is treated as authoritative for what is installable; the discrepancy is most plausibly a cached or paginated view of the releases page. It is recorded here rather than smoothed over.

## META-01.5 — Corrections carried forward from the first compilation pass

An earlier pass of this research contained four defects, all caused by trusting secondary sources for facts a primary source could settle. They are listed here because a corpus that hides its own error history is less trustworthy, not more.

1. **Stale version numbers.** A comparison blog's "LangChain v1.2.7 / LangGraph v1.0.7" and a cached README's "`langchain-mcp-adapters` 0.2.2" were both wrong. Corrected via the PyPI API; see `SH-01`.
2. **An invented-sounding EOL date.** "`AgentExecutor` EOL December 2026" appeared in a single commercial blog and could not be found in LangChain's official v1 migration guide. It is now labeled Tier 3 / unconfirmed in `SH-02` rather than stated as fact.
3. **An over-weighted criticism source.** A training-company marketing blog supplied per-query dollar figures and unattributed "Reddit quotes." It was demoted; the cost argument is now carried by a first-party measured study on LangChain's own forum plus the Octomind/Hacker News exchange, both retrievable. See `SH-10`.
4. **Python version floor stated imprecisely.** The earlier pass said only that Python 3.8 was dropped at v0.3. The actual current floor, read from package metadata, is **Python ≥3.10** across the core packages and **≥3.11** for `deepagents`. See `SH-01`.

## META-01.7 — Second verification pass (2026-08-13, post-academic expansion)

A dedicated re-verification pass was run after the initial compilation. Four things changed; two previously-flagged gaps closed and two remain.

**Closed — middleware hook names.** `LC-06.2` previously listed the `AgentMiddleware` hook names as unverified inference. They were confirmed Tier 1 against [`reference.langchain.com/python/langchain/agents/middleware/`](https://reference.langchain.com/python/langchain/agents/middleware/): the six hooks are `before_agent`, `before_model`, `wrap_model_call`, `after_model`, `wrap_tool_call`, `after_agent`, each with a matching decorator, plus `@generate_system_prompt`, `@configure_hook`, and `set_default_trace_policy`. The earlier inference was correct but is now sourced rather than guessed.

**Closed — durability mode values.** `LG-09.5` previously confirmed only `"exit"`. The full set was confirmed Tier 1 from [`langgraph.types.Durability`](https://reference.langchain.com/python/langgraph/types/Durability) as `Literal['sync', 'async', 'exit']`, with least-to-most-durable ordering from LangChain's public framing (Tier 2). `AC-03.3` now explains these as bulk-synchronous barrier policies.

**Confirmed stable — package versions.** All twenty packages in `SH-01` were re-queried against the PyPI JSON API. Every value held. Upload timestamps were captured on the second pass and show that every core package shipped a release within the two weeks preceding compilation, which substantiates the cadence warning in `SH-01.1` with dates rather than assertion.

**Still open — two items.** Middleware **composition ordering** with stacked middleware remains unspecified in both the narrative docs and the reference index. The narrative **durable-execution documentation page** remained partially unretrievable, though the type values it would describe are now verified independently. Both are flagged in place in `LC-06.2` and `LG-09.5` rather than filled by inference.

**Structural change.** The `academic/` series (`AC-01` through `AC-05`) was added in this pass, along with the dual-recency policy in `META-01.1` that it necessitated, a `README.md` at corpus root documenting RAG ingestion, and a machine-readable `_meta/manifest.csv`. The academic literature was checked for contradictions against existing claims; **none were found.** The empirical findings in `AC-04` independently corroborate several claims that had previously rested on informal sources — most notably the 42%-of-developers abstraction-overhead figure supporting what `SH-10` had carried only as blog and Hacker News testimony.

## META-01.6 — Formatting contract for downstream chunking and embedding

This corpus is written to be chunked mechanically without losing meaning.

- **Every file opens with YAML frontmatter** carrying `doc_id`, `title`, `series`, `product`, `version_scope`, `last_verified`, and `tags`. Retain frontmatter as chunk metadata rather than embedding it as body text.
- **Every section has a stable, globally unique ID** of the form `<DOC-ID>.<n>` (for example `LG-04.3`), used as its heading prefix. These IDs are stable across revisions of this corpus and are safe to use as citation anchors or primary keys.
- **Sections are self-contained.** Each opens by restating its subject in full rather than relying on a pronoun referring to the previous section, so a section extracted in isolation still reads correctly. Sections are sized roughly 120–450 words, which sits comfortably inside common 512- and 1024-token chunk budgets.
- **Prose over dense tables** for anything an embedding model needs to understand semantically. Tables are used only for genuinely tabular reference data (version matrices, CVE registers, error codes), where row-wise chunking is acceptable and the surrounding prose supplies context.
- **Citations are inline as markdown links** at the point of claim, and every file ends with a `Sources` section listing each URL with its access date. Tier labels appear next to claims, not only in the source list, so a chunk carries its own provenance.
- **No cross-file pronouns.** References to other documents always use the explicit doc ID (for example "see `LG-04`"), never "as described above," so that relationships survive chunk reordering.
