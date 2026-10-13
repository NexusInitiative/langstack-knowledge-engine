"""The embedding seam.

Everything downstream (ingest, retrieval) depends on this Protocol, never on a
concrete model. That buys three things:

* tests run in milliseconds with ``HashingEmbedder`` - no 2 GB model download;
* the embedding bake-off (issue #17) is "implement ``Embedder``, run eval";
* swapping models is a one-line change plus a re-index (``model_id`` is
  stored per chunk, so a model change is detected and re-embeds everything).

One call yields *both* a dense vector and a learned-sparse vector. BGE-M3
produces both in a single forward pass, which is why hybrid retrieval costs
one model rather than two.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Embedding:
    dense: list[float]           # L2-normalised; compared by cosine distance
    sparse: dict[int, float]     # model token id (0-based) -> positive weight


class Embedder(Protocol):
    model_id: str      # recorded per chunk; a change forces re-embedding
    dense_dim: int     # width of the pgvector ``vector`` column
    sparse_dim: int    # dimension of the pgvector ``sparsevec`` column

    def encode(self, texts: Sequence[str]) -> list[Embedding]:
        """Encode documents *and* queries identically (BGE-M3 needs no
        instruction prefix; a model that does must add it inside ``encode``)."""
        ...
