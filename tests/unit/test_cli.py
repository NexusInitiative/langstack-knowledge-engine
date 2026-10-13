import pytest

from lkengine.cli import build_parser, main
from lkengine.embed import make_embedder


def test_parser_wires_every_command():
    p = build_parser()
    assert p.parse_args(["ingest"]).command == "ingest"
    a = p.parse_args(["search", "q", "--product", "LangGraph", "both", "--max-tier", "1", "--embedder", "hash"])
    assert (a.embedder, a.query, a.product, a.max_tier) == ("hash", "q", ["LangGraph", "both"], 1)
    assert p.parse_args(["eval", "--ks", "1", "5"]).ks == [1, 5]
    assert p.parse_args(["db", "init", "--ann"]).ann is True


def test_parser_rejects_unknown_embedder_and_missing_command():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["ingest", "--embedder", "nope"])
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_make_embedder_factory():
    assert make_embedder("hash").model_id == "hashing-bow-v1"
    with pytest.raises(ValueError):
        make_embedder("nope")


def test_embedder_flag_is_accepted_after_the_subcommand():
    p = build_parser()
    assert p.parse_args(["ingest", "--embedder", "hash"]).embedder == "hash"
    assert p.parse_args(["search", "q", "--embedder", "hash"]).embedder == "hash"
    assert p.parse_args(["eval", "--embedder", "hash"]).embedder == "hash"
    assert p.parse_args(["db", "init", "--embedder", "hash"]).embedder == "hash"
