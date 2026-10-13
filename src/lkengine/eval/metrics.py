"""Retrieval metrics (issue E1-2). Pure functions over ranked section ids.

Ranked lists are *section* ids, de-duplicated in rank order, because the unit
a user cites (and the golden set labels) is the section, not the chunk part.

* ``recall_at_k``  - what fraction of the labelled relevant sections appear in
  the top k. Answers "did we retrieve what the answer needs?" (multi-section
  questions need all of them).
* ``hit_at_k``     - 1 if *any* relevant section is in the top k. The lenient
  cousin; useful because many questions list alternates.
* ``reciprocal_rank`` - 1/rank of the first relevant section within the top k
  (0 if absent); its mean over questions is MRR@k. Rewards putting the right
  thing *first*, which is what matters when only a few chunks reach the LLM.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable


def unique_in_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def recall_at_k(ranked: list[str], relevant: Collection[str], k: int) -> float:
    if not relevant:
        raise ValueError("recall is undefined with no relevant items")
    return len(set(ranked[:k]) & set(relevant)) / len(set(relevant))


def hit_at_k(ranked: list[str], relevant: Collection[str], k: int) -> float:
    return 1.0 if set(ranked[:k]) & set(relevant) else 0.0


def reciprocal_rank(ranked: list[str], relevant: Collection[str], k: int = 10) -> float:
    rel = set(relevant)
    for rank, item in enumerate(ranked[:k], start=1):
        if item in rel:
            return 1.0 / rank
    return 0.0
