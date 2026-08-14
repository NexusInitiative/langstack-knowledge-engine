---
doc_id: SH-06
title: Security Advisories & CVEs (2025-2026)
series: SH
product: both
version_scope: langchain-core <1.2.22, langgraph-checkpoint <4.0.0, and related
last_verified: 2026-08-13
source_tier: 1
tags: [security, cve, vulnerability, advisory, patching, deserialization, path-traversal, sql-injection, multi-tenancy]
---

# SH-06 — Security Advisories & CVEs

## SH-06.1 — Why this section exists and how it was verified

LangChain and LangGraph sustained a cluster of significant vulnerability disclosures between December 2025 and mid-2026, several of them affecting `langchain-core` — the package almost every other component depends on. Any corpus intended to guide real builds has to carry these, because the mitigation in every case is a version bump, and several of the affected version ranges include versions people are still running.

Each CVE below was verified against at least one authoritative vulnerability record — a GitHub Security Advisory, Snyk, Tenable, or the GitLab Advisory Database — for its identifier, affected range, fixed version, and score. News coverage was used only for discovery narrative and attribution, never as the sole basis for a technical claim. Where two authoritative sources report different CVSS figures for the same CVE, both are given.

## SH-06.2 — CVE register

| CVE | Package | Affected | Fixed in | Score | Class |
|---|---|---|---|---|---|
| CVE-2025-68664 ("LangGrinch") | `langchain-core` | <0.3.81; >=1.0.0 <1.2.5 | 0.3.81 and 1.2.5 | 9.2–9.3 Critical | Serialization injection → secret exfiltration |
| CVE-2026-34070 | `langchain-core` | <1.2.22 | 1.2.22 | 7.5 High | Path traversal in prompt loading |
| CVE-2026-27794 | `langgraph-checkpoint` | <4.0.0 | 4.0.0 | 6.6 Moderate | Pickle deserialization → RCE |
| CVE-2025-67644 | `langgraph-checkpoint-sqlite` | <3.0.1 | 3.0.1 | 7.3 High | SQL injection via metadata filter keys |
| CVE-2026-71433 | `langgraph-checkpoint-postgres`, `-sqlite` | <3.1.1 | 3.1.1 | 5.3 Medium | Namespace prefix matching crosses tenant boundaries |
| CVE-2026-48121 | `@langchain/langgraph-checkpoint-mongodb` (npm) | <1.3.1 | 1.3.1 | 6.7 Medium | NoSQL operator injection → cross-tenant checkpoint access |

## SH-06.3 — CVE-2025-68664 "LangGrinch" — serialization injection in langchain-core

The most severe of the set. LangChain's serialization helpers `dumps()` and `dumpd()` failed to escape user-controlled dictionaries containing an `lc` key, which `langchain-core` reserves internally to mark a serialized LangChain object. An attacker who could get such a dictionary into user-controlled data could have it treated as a legitimate internal object on deserialization. With the default `secrets_from_env=True` behavior, this permitted extraction of environment-variable secrets such as API keys, and instantiation of arbitrary classes with attacker-controlled parameters.

The practical injection vectors are notable because they are not obviously "user input": reporting identifies LLM response fields such as `additional_kwargs` and `response_metadata` as realistic carriers, meaning a hostile or compromised upstream model provider — or a prompt-injection chain that shapes model output — becomes an exploitation path. Coverage additionally cites potential arbitrary code execution via Jinja2 templates.

Affected: `langchain-core` below 0.3.81, and 1.0.0 up to but not including 1.2.5. Fixed in **0.3.81 and 1.2.5**. Scored 9.2 (CVSS v4.0, Snyk) and reported as 9.3 elsewhere. Discovered by Yarden Porat of Cyata, reported 2025-12-04, published 2025-12-24. **Tier 1/2 (Snyk advisory record, corroborated by security press).**

## SH-06.4 — CVE-2026-34070 — path traversal in prompt loading

Multiple functions in `langchain_core.prompts.loading` read files from paths embedded in deserialized config dictionaries without validating against directory traversal or absolute-path injection. An attacker who controls a prompt config can therefore cause arbitrary file reads from the host, exposing configuration files and credentials.

Affected: `langchain-core` before **1.2.22**, which is the fixed version. CVSS v3.1 base score 7.5, vector `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N` — network-reachable, no privileges, no user interaction, high confidentiality impact with no integrity or availability impact, which is the classic signature of an arbitrary-read bug. Published 2026-03-31. Recommended hardening beyond patching is allowlisting permitted file paths and enforcing directory boundaries. **Tier 1 (Tenable CVE record).**

## SH-06.5 — CVE-2026-27794 — pickle fallback RCE in the LangGraph cache

LangGraph's caching layer defaulted to `JsonPlusSerializer(pickle_fallback=True)`. When msgpack serialization failed, cached values were deserialized through `pickle.loads()`. An attacker able to write a malicious pickle payload into the cache backend could therefore achieve arbitrary code execution in the LangGraph process.

Exploitation is conditional, which is why the score is Moderate rather than Critical: caching must be explicitly enabled with a `BaseCache` implementation, nodes must opt in via `CachePolicy`, and the attacker must be able to write to the cache backend — an unsecured Redis instance or a writable SQLite file being the realistic cases. Fixed in `langgraph-checkpoint` **4.0.0**, which flips the default to `pickle_fallback=False`. CWE-502. CVSS 6.6. Tracked as ZDI-CAN-28385 and published as GitHub advisory GHSA-mhr3-j7m5-c7c9. **Tier 1 (official GitHub Security Advisory on `langchain-ai/langgraph`).**

## SH-06.6 — The multi-tenancy cluster: CVE-2026-71433 and CVE-2026-48121

Two separate advisories describe the same underlying design hazard from different angles: **namespaces and thread IDs are frequently used as tenant boundaries, and the storage layers did not enforce them strictly.**

CVE-2026-71433 affects the Postgres and SQLite stores. Hierarchical namespaces were stored as dot-joined strings — the tuple `("memories", "alice")` becoming `memories.alice` — and scoped reads matched with `LIKE '<path>%'`. Because `LIKE` has no notion of the dot as a separator, a scoped read could match sibling namespaces sharing leading characters. No crafted input is required; ordinary requests can cross boundaries. Fixed in **3.1.1**, CVSS 5.3.

CVE-2026-48121 affects the JavaScript MongoDB checkpointer. Checkpoint identifier fields from `config.configurable` were used in MongoDB queries without strict type enforcement, so an object payload containing MongoDB operators such as `$gt` or `$ne` would be interpreted as query logic rather than a literal value. This bypasses thread scoping and reaches other tenants' checkpoints. CWE-943. Fixed in `@langchain/langgraph-checkpoint-mongodb` **1.3.1**, CVSS 6.7.

The design lesson generalizes beyond these two fixes: if you are multi-tenanting a LangGraph deployment, do not treat `thread_id` or store namespaces as a security boundary on their own. Enforce tenancy in your own authorization layer above the checkpointer as well. **Tier 1/2 (GitLab Advisory Database records).**

## SH-06.7 — Minimum-safe version guidance

Consolidating the register, the floor for a patched install as of this corpus is `langchain-core` **≥1.2.22** (which also covers the earlier 1.2.5 LangGrinch fix on the 1.x line), `langgraph-checkpoint` **≥4.0.0**, `langgraph-checkpoint-sqlite` **≥3.1.1**, `langgraph-checkpoint-postgres` **≥3.1.1**, and `@langchain/langgraph-checkpoint-mongodb` **≥1.3.1**. Cross-referencing `SH-01`, the versions published as current on 2026-08-13 — `langchain-core` 1.5.4, `langgraph-checkpoint` 4.2.0, `langgraph-checkpoint-sqlite` 3.1.1, `langgraph-checkpoint-postgres` 3.1.2 — all satisfy these floors. Anyone pinned to an older line, particularly the `langchain-core` 0.3.x maintenance line, needs at least 0.3.81.

## Sources

- [GHSA-mhr3-j7m5-c7c9 — official LangGraph security advisory (CVE-2026-27794)](https://github.com/langchain-ai/langgraph/security/advisories/GHSA-mhr3-j7m5-c7c9) — accessed 2026-08-13 (Tier 1)
- [Snyk: CVE-2025-68664 langchain-core deserialization](https://security.snyk.io/vuln/SNYK-PYTHON-LANGCHAINCORE-14560681) — accessed 2026-08-13 (Tier 1)
- [Tenable: CVE-2026-34070](https://www.tenable.com/cve/CVE-2026-34070) — accessed 2026-08-13 (Tier 1)
- [GitLab Advisory Database: CVE-2026-71433](https://advisories.gitlab.com/pypi/langgraph-checkpoint-postgres/CVE-2026-71433/) — accessed 2026-08-13 (Tier 1)
- [GitLab Advisory Database: CVE-2026-48121](https://advisories.gitlab.com/npm/@langchain/langgraph-checkpoint-mongodb/CVE-2026-48121/) — accessed 2026-08-13 (Tier 1)
- [The Hacker News: LangChain/LangGraph flaws expose files, secrets, databases](https://thehackernews.com/2026/03/langchain-langgraph-flaws-expose-files.html) — 2026-03, accessed 2026-08-13 (Tier 2)
- [The Hacker News: Critical LangChain Core vulnerability (LangGrinch)](https://thehackernews.com/2025/12/critical-langchain-core-vulnerability.html) — 2025-12, accessed 2026-08-13 (Tier 2)
- [CSO Online: LangChain path traversal bug](https://www.csoonline.com/article/4151814/langchain-path-traversal-bug-adds-to-input-validation-woes-in-ai-pipelines.html) — accessed 2026-08-13 (Tier 2)
- [Cloud Security Alliance research note on LangChain/LangGraph vulnerabilities](https://labs.cloudsecurityalliance.org/wp-content/uploads/2026/03/CSA_research_note_langchain_langgraph_vulnerabilities_20260329-csa-styled.pdf) — 2026-03-29 (Tier 2)
