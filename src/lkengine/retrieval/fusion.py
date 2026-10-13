"""Weighted Reciprocal Rank Fusion (Cormack et al., SIGIR 2009).

Why RRF and not "add the scores"?  Cosine similarity, sparse inner product and
``ts_rank_cd`` live on incomparable scales; normalising them is fragile and
corpus-dependent. RRF ignores magnitudes and uses only *ranks*:

    score(d) = sum over channels c of  weight_c / (k + rank_c(d))

with k=60 the standard damping constant. A document that several channels put
near the top beats one that a single channel loves - exactly the behaviour we
want when dense catches paraphrases and lexical catches ``InvalidUpdateError``.

This is a pure function (no DB) so the fusion maths is unit-tested directly.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

RRF_K = 60


@dataclass(frozen=True)
class FusedHit:
    chunk_id: str
    score: float
    channel_ranks: dict[str, int] = field(default_factory=dict)  # channel -> 1-based rank


def rrf_fuse(
    rankings: Mapping[str, Sequence[str]],
    *,
    weights: Mapping[str, float],
    k: int = RRF_K,
) -> list[FusedHit]:
    """Fuse ranked id lists (best first). Ties break by ``chunk_id`` so results
    are deterministic. Raises ``KeyError`` if a channel has no weight - a
    silent default would hide a misconfigured channel."""
    scores: dict[str, float] = {}
    ranks: dict[str, dict[str, int]] = {}
    for channel, ids in rankings.items():
        w = weights[channel]
        for rank, cid in enumerate(ids, start=1):
            scores[cid] = scores.get(cid, 0.0) + w / (k + rank)
            ranks.setdefault(cid, {})[channel] = rank
    ordered = sorted(scores, key=lambda cid: (-scores[cid], cid))
    return [FusedHit(cid, scores[cid], ranks[cid]) for cid in ordered]
