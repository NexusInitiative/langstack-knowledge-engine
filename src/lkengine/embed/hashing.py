"""Deterministic, dependency-free embedder for tests and CI.

NOT a quality embedder. It hashes tokens into a fixed-size signed bag-of-words
(dense) and a token-id -> weight map (sparse). Because it is lexical it gives
*sensible* rankings on this identifier-heavy corpus, which lets integration
tests assert real retrieval behaviour (filters, fusion, eval plumbing)
without a model. Its eval numbers say nothing about BGE-M3 - the real
baseline is issue #12.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from collections.abc import Sequence

from lkengine.embed.base import Embedding

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*|\d+")
_CAMEL_RE = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+")
_STOP = frozenset(
    "a an and are as at be but by do does for from how i in into is it my not of on or "
    "our so than that the their then there this to was we what when which why with you your".split()
)


def _tokens(text: str) -> list[str]:
    """Identifiers keep their whole form *and* contribute their parts, so the
    query 'invalid update error' can still find ``InvalidUpdateError``."""
    out: list[str] = []
    for raw in _TOKEN_RE.findall(text):
        whole = raw.lower()
        out.append(whole)
        parts = [p.lower() for piece in raw.split("_") for p in _CAMEL_RE.findall(piece)]
        if len(parts) > 1:
            out.extend(parts)
    return [t for t in out if t not in _STOP and len(t) > 1]


def _h(token: str) -> int:
    return int.from_bytes(hashlib.blake2b(token.encode(), digest_size=8).digest(), "big")


class HashingEmbedder:
    model_id = "hashing-bow-v1"

    def __init__(self, dense_dim: int = 256, sparse_dim: int = 1 << 16) -> None:
        self.dense_dim = dense_dim
        self.sparse_dim = sparse_dim

    def encode(self, texts: Sequence[str]) -> list[Embedding]:
        return [self._encode_one(t) for t in texts]

    def _encode_one(self, text: str) -> Embedding:
        counts = Counter(_tokens(text))
        if not counts:
            return Embedding(dense=[0.0] * self.dense_dim, sparse={})

        dense = [0.0] * self.dense_dim
        for tok, n in counts.items():
            h = _h(tok)
            sign = 1.0 if (h >> 63) & 1 else -1.0
            dense[h % self.dense_dim] += sign * (1.0 + math.log(n))
        norm = math.sqrt(sum(x * x for x in dense)) or 1.0
        dense = [x / norm for x in dense]

        peak = max(counts.values())
        sparse: dict[int, float] = {}
        for tok, n in counts.items():
            idx = _h(tok) % self.sparse_dim
            sparse[idx] = max(sparse.get(idx, 0.0), n / peak)  # collisions: keep max
        return Embedding(dense=dense, sparse=sparse)
