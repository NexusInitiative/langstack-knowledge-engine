---
doc_id: LG-10
title: LangGraph — Deployment, CLI & Platform
series: LG
product: LangGraph
version_scope: langgraph-cli 0.4.31, langgraph-sdk 0.4.2
last_verified: 2026-08-13
source_tier: 1
tags: [deployment, langgraph.json, cli, langgraph-dev, docker, platform, ttl, auth, http, python_version]
---

# LG-10 — Deployment, CLI & Platform

## LG-10.1 — The CLI commands

The LangGraph CLI (`langgraph-cli`, verified 0.4.31) exposes five documented commands covering the path from local development to deployment:

- **`dev`** — starts a lightweight local development server with no Docker requirement, intended for rapid testing.
- **`build`** — builds a Docker image of the LangGraph API server for deployment.
- **`up`** — starts the LangGraph API server locally in Docker.
- **`deploy`** — builds and deploys a LangGraph image directly to LangSmith Deployments in one step.
- **`dockerfile`** — emits a Dockerfile derived from your config, for custom build pipelines.

`dev` flags cover host, port, reload behavior, debugger configuration, browser control, Studio URL, and tunnel exposure. Build and deploy flags cover platform targeting, image tagging, pull behavior, config file path, and JS-only build/install commands. **Tier 1** ([CLI docs](https://docs.langchain.com/langsmith/cli)).

## LG-10.2 — langgraph.json: required keys

Deployment configuration lives in `langgraph.json`. Two keys are required.

**`dependencies`** specifies local packages or dependency files to install.

**`graphs`** maps graph IDs to compiled graphs or factory functions. The factory-function form matters for deployment, because it lets the server construct the graph at runtime — which is how runtime checkpointer injection works (see `LG-10.5`).

## LG-10.3 — langgraph.json: optional keys

Seven optional keys cover the rest of the deployment surface:

- **`env`** — environment variables, from a `.env` file or an inline mapping.
- **`python_version`** — `3.11`, `3.12`, or `3.13`, defaulting to **3.11**. Note this is narrower than the package floor of 3.10 in `SH-01`; the deployment target does not accept 3.10.
- **`node_version`** — set to `20` for LangGraph.js deployments.
- **`http`** — CORS, middleware ordering, authentication, and route disabling.
- **`store`** — semantic search indexing and TTL expiration for long-term memory (see `LG-05`).
- **`checkpointer`** — backend selection (PostgreSQL or MongoDB), **TTL**, and deserialization behavior.
- **`auth`** — path to an authentication handler.
- **`base_image`** and **`image_distro`** — custom base image, and Linux distribution chosen from debian, wolfi, bookworm, or bullseye.

The **`checkpointer.ttl`** and **`store.ttl`** settings are the deployment-level answer to unbounded checkpoint growth documented in `LG-04`. If you deploy without configuring TTL, database tables grow indefinitely absent manual cleanup.

## LG-10.4 — Security configuration is not optional

Three `langgraph.json` keys carry direct security weight given the CVE history in `SH-06`.

**`auth`** and the `http` authentication settings are the enforcement point for tenancy. Because `thread_id` and store namespaces were both shown to be crossable boundaries (CVE-2026-48121, CVE-2026-71433), authorization must be enforced here rather than assumed from checkpoint scoping.

**`checkpointer`** backend choice determines which CVE register applies — the SQLite, Postgres, MongoDB, and Redis backends each had distinct advisories with distinct fixed versions.

**`image_distro`** affects your base-image CVE surface independent of LangGraph itself; wolfi is the minimal-distro option among those listed.

## LG-10.5 — Compile-time versus runtime checkpointer in deployment

The single most consequential deployment behavior: **the LangGraph API Server injects the checkpointer at runtime.** Graphs are typically compiled *without* one, and the server supplies persistence.

Two documented consequences follow. First, `@task`-level checkpointing resolves its checkpointer at compile time and therefore cannot see the injected one, causing tasks to re-execute on resume — the trap detailed in `LG-09` and `LG-07`. Second, local development can diverge from production: issue [#5790](https://github.com/langchain-ai/langgraph/issues/5790), verified **closed**, documented `langgraph dev` forcing an in-memory runtime and logging `"Using langgraph_runtime_inmem"` regardless of a configured `AsyncSqliteSaver`, leaving `checkpoint.db` empty and losing conversation state on every hot reload.

That specific bug is fixed, but the class of problem — local dev not mirroring deployed persistence — is worth testing explicitly rather than assuming. Verify persistence behavior in the environment you will actually deploy to.

## LG-10.6 — Platform and SDK

LangGraph Platform reached general availability as the managed offering for deploying and managing long-running, stateful agents, and LangGraph deployments appear as a first-class surface within LangSmith. Client access is through `langgraph-sdk` (verified 0.4.2), with a JS counterpart.

For the observability side of a deployment — tracing, evaluation, and monitoring — see `SH-05`.

## Sources

- [LangGraph CLI — official docs](https://docs.langchain.com/langsmith/cli) — accessed 2026-08-13 (Tier 1)
- [LangGraph Platform GA announcement](https://www.langchain.com/blog/langgraph-platform-ga) — accessed 2026-08-13 (Tier 1)
- [Issue #5790 — langgraph dev ignores checkpointer configuration](https://github.com/langchain-ai/langgraph/issues/5790) — verified closed, accessed 2026-08-13 (Tier 1)
- [PyPI: langgraph-cli, langgraph-sdk](https://pypi.org/) — queried 2026-08-13 (Tier 1)
- [Understanding Checkpointers, Databases, API Memory and TTL](https://support.langchain.com/articles/6253531756-understanding-checkpointers-databases-api-memory-and-ttl) — accessed 2026-08-13 (Tier 1)
