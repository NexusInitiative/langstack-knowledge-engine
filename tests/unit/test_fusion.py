from lkengine.retrieval.fusion import rrf_fuse


def test_single_channel_preserves_order():
    hits = rrf_fuse({"dense": ["a", "b", "c"]}, weights={"dense": 1.0})
    assert [h.chunk_id for h in hits] == ["a", "b", "c"]


def test_agreement_across_channels_beats_a_single_top_rank():
    hits = rrf_fuse(
        {"dense": ["x", "a"], "sparse": ["y", "a"], "fts": ["z", "a"]},
        weights={"dense": 1, "sparse": 1, "fts": 1},
    )
    assert hits[0].chunk_id == "a"  # rank 2 in all three beats rank 1 in one


def test_rrf_score_formula():
    (h,) = rrf_fuse({"dense": ["a"]}, weights={"dense": 1.0}, k=60)
    assert abs(h.score - 1 / 61) < 1e-12
    (h,) = rrf_fuse({"fts": ["a"]}, weights={"fts": 0.5}, k=60)
    assert abs(h.score - 0.5 / 61) < 1e-12


def test_channel_ranks_are_reported_for_explainability():
    hits = rrf_fuse({"dense": ["a", "b"], "sparse": ["b"]}, weights={"dense": 1, "sparse": 1})
    by_id = {h.chunk_id: h for h in hits}
    assert by_id["a"].channel_ranks == {"dense": 1}
    assert by_id["b"].channel_ranks == {"dense": 2, "sparse": 1}


def test_ties_break_deterministically_by_chunk_id():
    hits = rrf_fuse({"dense": ["b"], "sparse": ["a"]}, weights={"dense": 1, "sparse": 1})
    assert [h.chunk_id for h in hits] == ["a", "b"]


def test_empty_input():
    assert rrf_fuse({}, weights={}) == []
    assert rrf_fuse({"dense": []}, weights={"dense": 1}) == []


def test_unweighted_channel_defaults_to_weight_one_is_an_error():
    import pytest
    with pytest.raises(KeyError):
        rrf_fuse({"dense": ["a"]}, weights={})
