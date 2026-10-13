"""Run the golden set through a retriever and aggregate (issue E1-2).

The harness depends only on a callable ``retrieve(query) -> ranked section
ids`` - not on Postgres or any model - so the scoring logic is unit-tested
with a dict, and the same code evaluates dense-only, hybrid, hybrid+rerank
or a competitor's MCP server by swapping the callable.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from lkengine.eval.golden import GoldenQuestion
from lkengine.eval.metrics import hit_at_k, recall_at_k, reciprocal_rank, unique_in_order

Retrieve = Callable[[str], Sequence[str]]
DEFAULT_KS = (1, 3, 5, 10)


@dataclass(frozen=True)
class QuestionResult:
    question: GoldenQuestion
    retrieved: tuple[str, ...]                 # section ids, deduped, best first
    recall: dict[int, float]                   # k -> recall (scored questions only)
    hit: dict[int, float]                      # k -> any-relevant-in-top-k
    doc_hit: dict[int, float]                  # k -> any expected *document* in top k
    rr: float | None                           # reciprocal rank @max(ks); None if unscored


def _doc_of(section_id: str) -> str:
    return section_id.rsplit(".", 1)[0]


@dataclass(frozen=True)
class EvalReport:
    ks: tuple[int, ...]
    results: tuple[QuestionResult, ...]

    @property
    def scored(self) -> list[QuestionResult]:
        return [r for r in self.results if r.question.is_scored]

    @property
    def unscored(self) -> list[QuestionResult]:
        return [r for r in self.results if not r.question.is_scored]

    def aggregate(self, results: Sequence[QuestionResult] | None = None) -> dict:
        rs = list(self.scored if results is None else results)
        n = len(rs)
        if n == 0:
            return {"n": 0}
        mean = lambda xs: sum(xs) / len(xs)
        out: dict = {"n": n, f"mrr@{max(self.ks)}": mean([r.rr for r in rs])}
        for k in self.ks:
            out[f"recall@{k}"] = mean([r.recall[k] for r in rs])
            out[f"hit@{k}"] = mean([r.hit[k] for r in rs])
            out[f"doc_hit@{k}"] = mean([r.doc_hit[k] for r in rs])
        return out

    def by_category(self) -> dict[str, dict]:
        groups: dict[str, list[QuestionResult]] = defaultdict(list)
        for r in self.scored:
            groups[r.question.category].append(r)
        return {cat: self.aggregate(rs) for cat, rs in sorted(groups.items())}

    def to_dict(self) -> dict:
        return {
            "ks": list(self.ks),
            "overall": self.aggregate(),
            "by_category": self.by_category(),
            "unscored": [
                {"id": r.question.id, "category": r.question.category,
                 "query": r.question.query, "retrieved": list(r.retrieved[:5])}
                for r in self.unscored
            ],
            "misses": [
                {"id": r.question.id, "query": r.question.query,
                 "expected": list(r.question.expect_sections), "retrieved": list(r.retrieved[:5])}
                for r in self.scored if r.hit[max(self.ks)] == 0
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def format_text(self) -> str:
        agg, top = self.aggregate(), max(self.ks)
        cols = [f"recall@{k}" for k in self.ks] + [f"mrr@{top}"]
        lines = [f"Scored questions: {agg.get('n', 0)}  "
                 f"(unscored known-gap: {len(self.unscored)})", ""]
        lines.append(f"{'category':<24}{'n':>4}" + "".join(f"{c:>11}" for c in cols))

        def row(label: str, a: dict) -> str:
            return f"{label:<24}{a['n']:>4}" + "".join(f"{a[c]:>11.3f}" for c in cols)

        lines.append(row("OVERALL", agg)) if agg["n"] else None
        lines += [row(cat, a) for cat, a in self.by_category().items()]
        misses = self.to_dict()["misses"]
        if misses:
            lines += ["", f"Misses (no expected section in top {top}):"]
            lines += [f"  {m['id']}: want {m['expected']} got {m['retrieved'][:3]}" for m in misses]
        return "\n".join(lines)


def evaluate(
    retrieve: Retrieve,
    questions: Sequence[GoldenQuestion],
    *,
    ks: Sequence[int] = DEFAULT_KS,
) -> EvalReport:
    ks = tuple(sorted(set(ks)))
    top = max(ks)
    results = []
    for q in questions:
        ranked = unique_in_order(retrieve(q.query))
        if q.is_scored:
            rel = q.expect_sections
            docs = set(q.expect_docs) or {_doc_of(s) for s in rel}
            ranked_docs = unique_in_order(_doc_of(s) for s in ranked)
            res = QuestionResult(
                q, tuple(ranked),
                recall={k: recall_at_k(ranked, rel, k) for k in ks},
                hit={k: hit_at_k(ranked, rel, k) for k in ks},
                doc_hit={k: hit_at_k(ranked_docs, docs, k) for k in ks},
                rr=reciprocal_rank(ranked, rel, top),
            )
        else:
            res = QuestionResult(q, tuple(ranked), {}, {}, {}, None)
        results.append(res)
    return EvalReport(ks=ks, results=tuple(results))
