"""Golden question set: loading and validation (issue E1-1a).

Each line of ``corpus/rag/eval_questions.jsonl``::

    {"id": "q03", "query": "...", "expect_sections": ["LG-07.2"],
     "expect_docs": ["LG-07"], "category": "semantics", "note": "..."}

``expect_sections`` empty means the corpus deliberately has no answer (a
"known gap"): the correct system behaviour is to abstain, so these are not
scored by retrieval metrics - they are listed for manual review and, later,
by the answer-quality judge (#18).
"""

from __future__ import annotations

import json
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GoldenQuestion:
    id: str
    query: str
    category: str
    expect_sections: tuple[str, ...]
    expect_docs: tuple[str, ...]
    note: str = ""

    @property
    def is_scored(self) -> bool:
        """Retrieval recall is only defined when there is something to find."""
        return bool(self.expect_sections)


def load_golden(path: str | Path) -> list[GoldenQuestion]:
    questions = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                questions.append(
                    GoldenQuestion(
                        id=row["id"],
                        query=row["query"],
                        category=row["category"],
                        expect_sections=tuple(row.get("expect_sections", ())),
                        expect_docs=tuple(row.get("expect_docs", ())),
                        note=row.get("note", ""),
                    )
                )
            except (json.JSONDecodeError, KeyError) as e:
                raise ValueError(f"{path}:{n}: bad golden-set row ({e!r})") from e
    return questions


def validate_golden(
    questions: list[GoldenQuestion],
    *,
    known_section_ids: Collection[str],
    known_doc_ids: Collection[str],
) -> list[str]:
    """Return human-readable problems (empty list = valid).

    A golden set that points at sections which no longer exist silently
    deflates recall; validating it against the live corpus turns a corpus
    edit that breaks a label into a test failure instead of a mystery.
    """
    problems: list[str] = []
    seen: set[str] = set()
    for q in questions:
        if q.id in seen:
            problems.append(f"{q.id}: duplicate question id")
        seen.add(q.id)
        if not q.query.strip():
            problems.append(f"{q.id}: empty query")
        problems += [f"{q.id}: unknown expect_section {s}" for s in q.expect_sections if s not in known_section_ids]
        problems += [f"{q.id}: unknown expect_doc {d}" for d in q.expect_docs if d not in known_doc_ids]
    return problems
