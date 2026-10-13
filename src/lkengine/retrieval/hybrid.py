"""Hybrid retrieval API (issue E3-1): dense + sparse + lexical, fused by RRF.

Pipeline for one query::

    query ──encode──▶ dense vec + sparse vec
      │
      ├─ dense   : cosine ANN/exact over ``dense``            ─┐
      ├─ sparse  : learned-sparse inner product over ``sparse`` ├─▶ RRF ─▶ top_k
      └─ lexical : Postgres full-text (websearch_to_tsquery)   ─┘
              (each channel: metadata-filtered, top ``pool`` candidates)

Why three channels?  This corpus is API documentation full of exact
identifiers (``InvalidUpdateError``, ``wrap_model_call``, ``langgraph.json``).
Dense embeddings capture meaning but blur literals; lexical channels pin
literals but miss paraphrase. Fusing by rank lets each cover the other.
The lexical full-text channel is down-weighted (0.5) because it overlaps the
learned-sparse channel; it is nearly free and catches literals the sparse
model down-weights.

Design choices worth knowing:

* **Channels run as separate small queries and are fused in Python.** One
  giant CTE (as in the reference ``corpus/rag/search.py``) is harder to read
  and impossible to unit-test; here the SQL is trivial and ``rrf_fuse`` is
  tested in isolation. At this scale the extra round trips are noise.
* **Zero-overlap rows are excluded from the sparse channel.** An inner
  product of 0 means "shares no token with the query"; ranking such rows
  would inject arbitrary noise into the fusion.
* **Filters are applied inside every channel** (pre-filter), so a
  ``product=LangGraph`` query is never diluted by LangChain results.
* A reranker (issue #20) slots in between ``search`` and the caller; the
  ``pool`` default of 40 is sized for it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date

import psycopg
from psycopg.rows import dict_row

from lkengine.db.migrate import assert_compatible
from lkengine.db.vectors import dense_literal, sparse_literal
from lkengine.embed.base import Embedder
from lkengine.retrieval.fusion import RRF_K, rrf_fuse

DEFAULT_WEIGHTS: Mapping[str, float] = {"dense": 1.0, "sparse": 1.0, "fts": 0.5}

_FILTER_SQL = """
    is_retrievable
    AND (%(product)s::text[] IS NULL OR product = ANY(%(product)s::text[]))
    AND (%(series)s::text[]  IS NULL OR series  = ANY(%(series)s::text[]))
    AND (%(max_tier)s::smallint IS NULL OR source_tier <= %(max_tier)s::smallint)
"""

_CHANNEL_SQL = {
    "dense": f"""
        SELECT chunk_id FROM corpus_chunks WHERE {_FILTER_SQL}
        ORDER BY dense <=> %(qdense)s::vector, chunk_id LIMIT %(pool)s""",
    # '<#>' is *negative* inner product; < 0 keeps only rows sharing a token.
    "sparse": f"""
        SELECT chunk_id FROM corpus_chunks
        WHERE {_FILTER_SQL} AND (sparse <#> %(qsparse)s::sparsevec) < 0
        ORDER BY sparse <#> %(qsparse)s::sparsevec, chunk_id LIMIT %(pool)s""",
    "fts": f"""
        SELECT chunk_id FROM corpus_chunks
        WHERE {_FILTER_SQL} AND fts @@ websearch_to_tsquery('english', %(q)s)
        ORDER BY ts_rank_cd(fts, websearch_to_tsquery('english', %(q)s)) DESC, chunk_id
        LIMIT %(pool)s""",
}

_HIT_FIELDS = (
    "chunk_id", "section_id", "doc_id", "doc_title", "heading", "body", "product",
    "series", "source_tier", "recency_class", "version_scope", "last_verified",
    "tags", "has_code",
)


def _cols(prefix: str = "") -> str:
    return ", ".join(prefix + f for f in _HIT_FIELDS)


@dataclass(frozen=True)
class SearchFilters:
    """Metadata pre-filters. ``None`` means "don't filter on this".

    ``product`` takes the corpus values ``LangChain`` / ``LangGraph`` / ``both``;
    for a LangGraph question you usually want ``("LangGraph", "both")``.
    ``max_tier=1`` restricts to primary sources (rows with no tier are excluded).
    """

    product: Sequence[str] | None = None
    series: Sequence[str] | None = None
    max_tier: int | None = None

    def params(self) -> dict:
        return {
            "product": list(self.product) if self.product else None,
            "series": list(self.series) if self.series else None,
            "max_tier": self.max_tier,
        }


@dataclass(frozen=True)
class RetrievalHit:
    """One retrieved chunk with the provenance an answer needs to cite it."""

    chunk_id: str
    section_id: str          # the citation anchor
    doc_id: str
    doc_title: str
    heading: str
    body: str
    product: str
    series: str
    source_tier: int | None
    recency_class: str
    version_scope: str | None
    last_verified: date
    tags: list[str]
    has_code: bool
    score: float = 0.0       # fused RRF score (higher is better)
    channel_ranks: dict[str, int] = field(default_factory=dict)  # explainability


class HybridRetriever:
    def __init__(
        self,
        conn: psycopg.Connection,
        embedder: Embedder,
        *,
        pool: int = 40,
        weights: Mapping[str, float] = DEFAULT_WEIGHTS,
        rrf_k: int = RRF_K,
    ) -> None:
        assert_compatible(conn, dense_dim=embedder.dense_dim, sparse_dim=embedder.sparse_dim)
        self._conn = conn
        self._embedder = embedder
        self._pool = pool
        self._weights = dict(weights)
        self._rrf_k = rrf_k

    def search(
        self, query: str, *, filters: SearchFilters | None = None, top_k: int = 6
    ) -> list[RetrievalHit]:
        if not query.strip():
            return []
        rankings = self._channel_rankings(query, (filters or SearchFilters()).params())
        fused = rrf_fuse(rankings, weights=self._weights, k=self._rrf_k)[:top_k]
        return self._hydrate(fused)

    def expand_xrefs(self, hits: Sequence[RetrievalHit], *, limit: int = 3) -> list[RetrievalHit]:
        """Context expansion along the corpus's explicit cross-references.

        For the top 3 hits, pull ``.1`` (the overview section) of every
        document they cite that is not already represented. Cheap, mechanical
        and high-precision because the corpus cites ids, not "see above".
        """
        if not hits:
            return []
        have_docs = list({h.doc_id for h in hits})
        top_sections = [h.section_id for h in hits[:3]]
        with self._conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                SELECT DISTINCT {_cols('c.')}
                FROM corpus_xrefs x
                JOIN corpus_chunks c ON c.chunk_id = x.to_doc_id || '.1'
                WHERE x.from_section_id = ANY(%s) AND c.is_retrievable
                  AND NOT (c.doc_id = ANY(%s))
                ORDER BY c.chunk_id LIMIT %s""",
                (top_sections, have_docs, limit),
            )
            return [RetrievalHit(**row) for row in cur.fetchall()]

    # -- internals ------------------------------------------------------------

    def _channel_rankings(self, query: str, filt: dict) -> dict[str, list[str]]:
        emb = self._embedder.encode([query])[0]
        params = {"q": query, "pool": self._pool, **filt}
        dense_ok = any(emb.dense)  # an all-zero vector has undefined cosine distance
        sparse_ok = bool(emb.sparse)
        if dense_ok:
            params["qdense"] = dense_literal(emb.dense)
        if sparse_ok:
            params["qsparse"] = sparse_literal(emb.sparse, self._embedder.sparse_dim)

        enabled = {"dense": dense_ok, "sparse": sparse_ok, "fts": True}
        rankings = {}
        for channel, sql in _CHANNEL_SQL.items():
            if enabled[channel]:
                rows = self._conn.execute(sql, params).fetchall()
                rankings[channel] = [r[0] for r in rows]
        return rankings

    def _hydrate(self, fused) -> list[RetrievalHit]:
        if not fused:
            return []
        with self._conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"SELECT {_cols()} FROM corpus_chunks WHERE chunk_id = ANY(%s)",
                ([f.chunk_id for f in fused],),
            )
            rows = {r["chunk_id"]: r for r in cur.fetchall()}
        return [
            RetrievalHit(**rows[f.chunk_id], score=f.score, channel_ranks=f.channel_ranks)
            for f in fused
        ]
