import math

from lkengine.db.vectors import dense_literal, sparse_literal
from lkengine.embed.hashing import HashingEmbedder


def test_hashing_embedder_is_deterministic_and_unit_norm():
    e = HashingEmbedder()
    a, b = e.encode(["InvalidUpdateError in a reducer"] * 2)
    assert a == b
    assert len(a.dense) == e.dense_dim
    assert math.isclose(sum(x * x for x in a.dense), 1.0, rel_tol=1e-6)


def test_hashing_embedder_similar_texts_are_closer_than_unrelated():
    e = HashingEmbedder()
    q, near, far = e.encode(
        ["checkpointer thread_id persistence",
         "persistence with a checkpointer and thread_id",
         "reranker cross encoder latency"])
    dot = lambda x, y: sum(i * j for i, j in zip(x.dense, y.dense))
    assert dot(q, near) > dot(q, far)


def test_sparse_weights_are_positive_and_in_range():
    e = HashingEmbedder()
    (v,) = e.encode(["with_structured_output and StateGraph"])
    assert v.sparse and all(0 < w <= 1.0 for w in v.sparse.values())
    assert all(0 <= i < e.sparse_dim for i in v.sparse)


def test_empty_text_gives_zero_vectors_without_crashing():
    (v,) = HashingEmbedder().encode([""])
    assert v.sparse == {}


def test_sparse_literal_is_one_indexed_sorted_and_drops_nonpositive():
    # pgvector sparsevec indices start at 1; model token ids start at 0.
    assert sparse_literal({5: 0.25, 0: 1.0, 3: 0.0, 9: -1.0}, dim=10) == "{1:1,6:0.25}/10"


def test_sparse_literal_empty():
    assert sparse_literal({}, dim=10) == "{}/10"


def test_sparse_literal_rejects_out_of_range_index():
    import pytest
    with pytest.raises(ValueError):
        sparse_literal({10: 1.0}, dim=10)


def test_dense_literal():
    assert dense_literal([0.5, -1.0, 0.0]) == "[0.5,-1,0]"
