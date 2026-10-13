"""Python -> pgvector text literals.

We pass vectors as text and cast in SQL (``%s::vector``), which avoids a
dependency on the ``pgvector`` Python package and keeps the wire format
visible and testable.
"""

from __future__ import annotations


def dense_literal(vec: list[float]) -> str:
    """``[0.1,0.2,...]`` for a ``vector`` column."""
    return "[" + ",".join(f"{x:.8g}" for x in vec) + "]"


def sparse_literal(weights: dict[int, float], dim: int) -> str:
    """``{idx:val,...}/dim`` for a ``sparsevec`` column.

    pgvector sparse indices are **1-based**, model token ids are 0-based, so
    every index is shifted by one here - the single place that translation
    happens, used by both ingest and query so they can never disagree.
    Non-positive weights carry no signal and are dropped.
    """
    items = sorted((int(i), float(w)) for i, w in weights.items() if float(w) > 0)
    for i, _ in items:
        if not 0 <= i < dim:
            raise ValueError(f"sparse index {i} out of range for dim {dim}")
    return "{" + ",".join(f"{i + 1}:{w:.6g}" for i, w in items) + "}/" + str(dim)
