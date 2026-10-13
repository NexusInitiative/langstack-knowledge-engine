"""Embedding models behind the ``Embedder`` protocol."""

from lkengine.embed.base import Embedder, EmbedderUnavailable, Embedding

EMBEDDER_NAMES = ("bge", "hash")


def make_embedder(name: str) -> Embedder:
    """Factory used by the CLI. ``bge`` imports torch lazily on first encode."""
    if name == "bge":
        from lkengine.embed.bge import BGEM3Embedder
        return BGEM3Embedder()
    if name == "hash":
        from lkengine.embed.hashing import HashingEmbedder
        return HashingEmbedder()
    raise ValueError(f"unknown embedder {name!r}; choose from {EMBEDDER_NAMES}")


__all__ = ["Embedder", "EmbedderUnavailable", "Embedding", "make_embedder", "EMBEDDER_NAMES"]
