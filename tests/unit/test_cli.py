import pytest

from lkengine.cli import build_parser, main
from lkengine.embed import make_embedder


def test_parser_wires_every_command():
    p = build_parser()
    assert p.parse_args(["ingest"]).command == "ingest"
    a = p.parse_args(["--embedder", "hash", "search", "q", "--product", "LangGraph", "both", "--max-tier", "1"])
    assert (a.embedder, a.query, a.product, a.max_tier) == ("hash", "q", ["LangGraph", "both"], 1)
    assert p.parse_args(["eval", "--ks", "1", "5"]).ks == [1, 5]
    assert p.parse_args(["db", "init", "--ann"]).ann is True


def test_parser_rejects_unknown_embedder_and_missing_command():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--embedder", "nope", "ingest"])
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_make_embedder_factory():
    assert make_embedder("hash").model_id == "hashing-bow-v1"
    with pytest.raises(ValueError):
        make_embedder("nope")
