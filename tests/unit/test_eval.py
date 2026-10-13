import pytest

from lkengine.eval.golden import GoldenQuestion, load_golden, validate_golden
from lkengine.eval.harness import evaluate
from lkengine.eval.metrics import hit_at_k, recall_at_k, reciprocal_rank, unique_in_order
from lkengine.ingest.build import build_chunks
from lkengine.ingest.parser import parse_corpus
from lkengine.paths import CORPUS_DIR, GOLDEN_SET_PATH


def Q(id, sections, category="c", docs=()):
    return GoldenQuestion(id, f"query {id}", category, tuple(sections), tuple(docs))


# -- metrics ------------------------------------------------------------------
def test_recall_is_fraction_of_relevant_found_in_top_k():
    ranked = ["a", "x", "b", "y"]
    assert recall_at_k(ranked, ["a", "b"], 1) == 0.5
    assert recall_at_k(ranked, ["a", "b"], 3) == 1.0
    assert recall_at_k(ranked, ["z"], 4) == 0.0


def test_recall_undefined_without_relevant():
    with pytest.raises(ValueError):
        recall_at_k(["a"], [], 1)


def test_hit_is_binary_any_match():
    assert hit_at_k(["x", "b"], ["a", "b"], 2) == 1.0
    assert hit_at_k(["x", "b"], ["a", "b"], 1) == 0.0


def test_reciprocal_rank_uses_first_relevant_and_respects_cutoff():
    assert reciprocal_rank(["x", "y", "b", "a"], ["a", "b"]) == pytest.approx(1 / 3)
    assert reciprocal_rank(["x", "y", "b"], ["b"], k=2) == 0.0
    assert reciprocal_rank([], ["b"]) == 0.0


def test_unique_in_order():
    assert unique_in_order(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


# -- harness ------------------------------------------------------------------
def test_harness_aggregates_overall_and_per_category():
    qs = [Q("q1", ["A-1.1"], "api"), Q("q2", ["B-1.1"], "api"), Q("q3", ["C-1.1"], "debug")]
    table = {"query q1": ["A-1.1"], "query q2": ["X-1.1", "B-1.1"], "query q3": ["X-1.1"]}
    rep = evaluate(lambda q: table[q], qs, ks=(1, 3))
    overall = rep.aggregate()
    assert overall["n"] == 3
    assert overall["recall@1"] == pytest.approx(1 / 3)
    assert overall["recall@3"] == pytest.approx(2 / 3)
    assert overall["mrr@3"] == pytest.approx((1 + 0.5 + 0) / 3)
    cats = rep.by_category()
    assert cats["api"]["recall@1"] == 0.5 and cats["debug"]["recall@3"] == 0.0


def test_unscored_known_gap_questions_are_excluded_from_metrics_but_reported():
    qs = [Q("q1", ["A-1.1"]), Q("gap", [], "known-gap")]
    rep = evaluate(lambda q: ["A-1.1"], qs, ks=(1,))
    assert rep.aggregate()["n"] == 1
    assert [r.question.id for r in rep.unscored] == ["gap"]
    assert rep.to_dict()["unscored"][0]["id"] == "gap"


def test_chunk_parts_of_one_section_collapse_before_scoring():
    rep = evaluate(lambda q: ["A-1.1", "A-1.1", "B-1.1"], [Q("q", ["B-1.1"])], ks=(2,))
    assert rep.results[0].retrieved == ("A-1.1", "B-1.1")
    assert rep.aggregate()["recall@2"] == 1.0


def test_doc_level_hit_credits_right_document_wrong_section():
    rep = evaluate(lambda q: ["LG-04.9"], [Q("q", ["LG-04.1"], docs=["LG-04"])], ks=(1,))
    assert rep.aggregate()["recall@1"] == 0.0
    assert rep.aggregate()["doc_hit@1"] == 1.0


def test_misses_and_text_report_render():
    rep = evaluate(lambda q: ["Z-1.1"], [Q("q1", ["A-1.1"])], ks=(1, 5))
    assert rep.to_dict()["misses"][0]["id"] == "q1"
    text = rep.format_text()
    assert "OVERALL" in text and "q1" in text
    assert '"recall@5"' in rep.to_json()


def test_empty_question_list_does_not_crash():
    rep = evaluate(lambda q: [], [])
    assert rep.aggregate() == {"n": 0}


# -- golden set against the real corpus ---------------------------------------
def test_shipped_golden_set_is_valid_against_the_shipped_corpus():
    chunks, _ = build_chunks(parse_corpus(CORPUS_DIR))
    problems = validate_golden(
        load_golden(GOLDEN_SET_PATH),
        known_section_ids={c.section_id for c in chunks},
        known_doc_ids={c.doc.doc_id for c in chunks},
    )
    assert problems == []


def test_validate_golden_flags_unknown_ids_and_duplicates():
    qs = [Q("q1", ["NOPE-1.1"], docs=["NOPE-1"]), Q("q1", ["A-1.1"])]
    problems = validate_golden(qs, known_section_ids={"A-1.1"}, known_doc_ids=set())
    assert any("unknown expect_section NOPE-1.1" in p for p in problems)
    assert any("unknown expect_doc NOPE-1" in p for p in problems)
    assert any("duplicate" in p for p in problems)


def test_golden_set_has_scored_and_known_gap_questions():
    qs = load_golden(GOLDEN_SET_PATH)
    assert len(qs) == 30
    assert sum(q.is_scored for q in qs) == 27 and sum(not q.is_scored for q in qs) == 3


def test_load_golden_reports_line_number_on_bad_row(tmp_path):
    p = tmp_path / "g.jsonl"
    p.write_text('{"id": "q1"}\n')
    with pytest.raises(ValueError, match=":1:"):
        load_golden(p)
