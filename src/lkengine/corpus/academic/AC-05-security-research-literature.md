---
doc_id: AC-05
title: Security Research Literature on LLM Agent Frameworks
series: AC
product: both
version_scope: 2023-2026 security literature
last_verified: 2026-08-13
source_tier: 1
recency_class: current
tags: [academic, security, prompt-injection, p2sql, mcp-security, threat-taxonomy, defense]
---

# AC-05 — Security Research Literature

## AC-05.1 — How this differs from the CVE register

`SH-06` catalogues **specific patched vulnerabilities** in LangChain and LangGraph packages, each with an affected range and a fixed version. This document covers **the research literature on the attack classes** those CVEs belong to — the systematic threat modeling that explains why these bugs keep appearing and what categories to defend against beyond the ones already patched.

The distinction matters operationally: patching closes known holes, while the taxonomy below tells you what to threat-model for in your own application code, which no upstream patch can do for you.

## AC-05.2 — The comprehensive agent-workflow threat survey

**Ferrag, M. A., Tihanyi, N., Hamouda, D., Maglaras, L., & Debbah, M. "From Prompt Injections to Protocol Exploits: Threats in LLM-Powered AI Agents Workflows."** arXiv:2506.23260 (2025).

This survey catalogues **over 30 attack techniques** against LLM-powered autonomous agents, and reports two figures that should calibrate expectations: adaptive prompt-injection attacks bypass existing defenses in **over 50% of cases**, and sophisticated jailbreak techniques routinely achieve **greater than 90% success rates**.

Its **four-domain taxonomy** is the most useful structure available for threat-modeling a LangChain application:

**Input manipulation** — direct prompt injection, Prompt-to-SQL (P2SQL), indirect and compositional injection, adaptive hijacking, jailbreaking, adversarial examples.

**Model compromise** — prompt-level backdoors, parameter backdoors, composite and encrypted multi-backdoors, data and memory poisoning.

**System and privacy attacks** — speculative side-channels, membership inference, retrieval poisoning, social engineering.

**Protocol vulnerabilities** — MCP, Agent Communication Protocol (ACP), Agent Network Protocol (ANP), and Agent-to-Agent (A2A) exploits.

Both LangChain and MCP are treated explicitly: LangChain is analyzed for Prompt-to-SQL injection susceptibility, and Section VI of the survey addresses MCP and A2A protocol vulnerabilities directly.

## AC-05.3 — Prompt-to-SQL injection in LLM-integrated applications

**"From Prompt Injections to SQL Injection Attacks: How Protected is Your LLM-Integrated Web Application?"** arXiv:2308.01990 (2023).

This is the P2SQL work the survey above references. Its finding, as summarized in that survey, is that **seven state-of-the-art LLMs are widely susceptible** to prompt-to-SQL injection, and that defense strategies significantly reduce success rates.

**Direct relevance to this corpus:** text-to-SQL is a headline LangGraph use case — LinkedIn's text-to-SQL system appears in LangChain's own case-study list (`LG-01.5`), and the LangGraph practitioner paper in `AC-04.4` uses "SQL analytics with repair loops" as its first worked recipe. Any such system is in scope for this attack class. A tool that constructs SQL from model output is an injection surface regardless of how carefully the graph around it is built.

## AC-05.4 — Retrieval poisoning and the RAG attack surface

The survey's inclusion of **retrieval poisoning** and **data/memory poisoning** matters specifically for the components in `LC-07` and `LG-05`.

A RAG pipeline ingests documents and retrieves them into model context. If an attacker can influence what enters the corpus, they can influence what the model reads — with no exploit against LangChain itself required. Similarly, the LangGraph `Store` persists cross-thread, cross-session memory (`LG-05`); anything written there is content the model will later treat as trusted context.

This connects to a documented CVE pattern rather than remaining theoretical. **CVE-2025-68664 (LangGrinch)** had realistic injection vectors in LLM response fields such as `additional_kwargs` and `response_metadata` (see `SH-06.3`) — meaning model output itself reached a serialization path. The literature's framing generalizes that: **in agent systems, model output and retrieved documents are untrusted input**, not intermediate values you can assume are safe.

## AC-05.5 — Protocol-layer security and MCP

The survey's protocol-vulnerability domain covers MCP directly, and the peer-reviewed survey in `AC-04.5` situates MCP as the vertical agent-to-tool layer of a three-layer stack over JSON-RPC 2.0. The empirical study in `AC-04.2` separately flags **insecure credential storage** and **limited multi-tenant scalability** as MCP-ecosystem concerns.

Three practices in this corpus follow from that literature. Prefer **`streamable-http` over `stdio`** for server deployments, which is also LangChain's own documented caution (`SH-03.4`). Recognize that **MCP tool errors return as tool messages rather than exceptions** by default (`SH-03.5`), so a hostile or failing MCP server degrades quietly rather than loudly — pair it with call limits. And treat **MCP server output as untrusted input** on the same reasoning as AC-05.4.

## AC-05.6 — The multi-tenancy theme across literature and CVEs

Multi-tenant isolation appears as a weakness in the academic literature and independently as a CVE cluster, which is unusually strong convergent evidence.

The empirical study (`AC-04.2`) reports limited multi-tenant scalability across the MCP ecosystem and notes AutoGen lacking multi-tenant isolation. The CVE register (`SH-06.6`) documents two distinct advisories where tenancy boundaries failed in LangGraph storage: **CVE-2026-71433**, where dot-joined namespaces matched with `LIKE` crossed sibling namespaces with no crafted input required, and **CVE-2026-48121**, where MongoDB operator injection through `config.configurable` reached other tenants' checkpoints.

The conclusion both lines of evidence support is stated in `SH-11.1` and bears repeating: **`thread_id` and store namespaces are convenience scoping, not security boundaries.** Enforce tenancy in your own authorization layer above the checkpointer.

## AC-05.7 — Defensive posture implied by the literature

Synthesizing across these sources, five defenses are indicated. **Patch to the floors in `SH-06.7`** — necessary but not sufficient. **Treat model output, retrieved documents, and MCP responses as untrusted input** wherever they reach a parser, serializer, query builder, or filesystem path. **Constrain SQL and tool-call construction** with parameterization and allowlists rather than trusting model-generated strings. **Enforce tenancy above the framework**, per AC-05.6. And **bound agent loops** with `ModelCallLimitMiddleware` and `ToolCallLimitMiddleware` (`LC-06`), which is a cost control and also a containment measure — an injected instruction that induces a loop is bounded by the same limit.

Given the survey's finding that adaptive prompt injection bypasses existing defenses in over half of cases, defense-in-depth rather than input filtering alone is the posture the literature supports.

## Sources

- [From Prompt Injections to Protocol Exploits: Threats in LLM-Powered AI Agents Workflows — arXiv:2506.23260](https://arxiv.org/abs/2506.23260) — accessed 2026-08-13 (Tier 1)
- [From Prompt Injections to SQL Injection Attacks — arXiv:2308.01990](https://arxiv.org/abs/2308.01990) — accessed 2026-08-13 (Tier 1)
- [LLM-Based Multi-Agent Orchestration: A Survey — Future Internet 18(6):326](https://www.mdpi.com/1999-5903/18/6/326) — accessed 2026-08-13 (Tier 1, peer-reviewed)
- [An Empirical Study of Agent Developer Practices — arXiv:2512.01939](https://arxiv.org/abs/2512.01939) — accessed 2026-08-13 (Tier 1)
- Cross-reference: `SH-06` (CVE register), `SH-03` (MCP), `LC-07` (RAG), `LG-05` (Store)
