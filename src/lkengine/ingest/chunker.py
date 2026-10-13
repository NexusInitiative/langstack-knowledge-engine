"""Structure-aware chunking (issue E2-3).

The corpus is already sectioned by authors into self-contained ``## ID.n``
blocks (median ~124 words), so the heading boundary is the primary chunk
boundary and, almost always, the *only* one. This module handles the tail:
a section too long for the downstream cross-encoder reranker.

Rules, in priority order:

1. **Heading-bounded** - a chunk never spans two sections.
2. **A code fence is atomic** - never split inside ``` ... ```, and blank
   lines inside a fence do not count as paragraph breaks.
3. **A fence keeps its lead-in** - the paragraph immediately before a fence
   ("Use the checkpointer like this:") is glued to it. Embedding a bare code
   block without the sentence that explains it is a classic RAG failure.
4. **Token-capped** - pack whole units greedily up to ``max_tokens``. A single
   unit that alone exceeds the cap (a huge fence) is emitted oversized rather
   than broken; rule 2 beats rule 4.

Why 480 by default: ``bge-reranker-v2-m3`` reads (query + passage) within 512
tokens, so a passage needs ~30 tokens of headroom for the query. See
``corpus/rag/README.md`` for the measurement behind this.

Token counting is a heuristic (``words * 1.4``), not a real tokenizer, so the
chunker has no model dependency and stays deterministic in tests. It is
deliberately conservative for English prose/code mixes.
"""

from __future__ import annotations

import math

from lkengine.ingest.fences import FenceTracker

DEFAULT_MAX_TOKENS = 480


def approx_tokens(text: str) -> int:
    """Cheap token estimate: ceil(words * 1.4)."""
    return math.ceil(len(text.split()) * 1.4)


def split_section_body(body: str, *, max_tokens: int = DEFAULT_MAX_TOKENS) -> list[str]:
    """Split one section (heading line + body) into parts of <= ``max_tokens``.

    Returns ``[body]`` unchanged when it already fits. Parts after the first
    are prefixed with ``<heading> (cont.)`` so each chunk is self-describing
    when retrieved alone.
    """
    if approx_tokens(body) <= max_tokens:
        return [body]

    heading, _, rest = body.partition("\n")
    units = _glue_lead_ins(_blocks(rest))

    parts: list[list[str]] = [[]]
    used = approx_tokens(heading)
    for unit in units:
        cost = approx_tokens(unit)
        if parts[-1] and used + cost > max_tokens:
            parts.append([])
            used = approx_tokens(heading) + 2  # repeated '(cont.)' heading
        parts[-1].append(unit)
        used += cost

    out = []
    for i, units_in_part in enumerate(parts):
        head = heading if i == 0 else f"{heading} (cont.)"
        out.append("\n\n".join([head, *units_in_part]))
    return out


def _blocks(text: str) -> list[tuple[str, bool]]:
    """Split on blank lines, except inside fences. Returns (text, is_fence)."""
    blocks: list[tuple[str, bool]] = []
    buf: list[str] = []
    fences = FenceTracker()

    def flush(is_fence: bool) -> None:
        if buf:
            blocks.append(("\n".join(buf).strip("\n"), is_fence))
            buf.clear()

    for line in text.split("\n"):
        event = fences.update(line)
        if event == "open":
            flush(False)  # prose before the fence ends here
            buf.append(line)
        elif event == "close":
            buf.append(line)
            flush(True)
        elif event == "inside":
            buf.append(line)
        elif line.strip() == "":
            flush(False)
        else:
            buf.append(line)
    flush(fences.in_fence)  # unterminated fence: keep it atomic anyway
    return [(t, f) for t, f in blocks if t.strip()]


def _glue_lead_ins(blocks: list[tuple[str, bool]]) -> list[str]:
    """Merge each prose block that directly precedes a fence into that fence."""
    units: list[str] = []
    i = 0
    while i < len(blocks):
        text, is_fence = blocks[i]
        nxt_is_fence = i + 1 < len(blocks) and blocks[i + 1][1]
        if not is_fence and nxt_is_fence:
            units.append(text + "\n\n" + blocks[i + 1][0])
            i += 2
        else:
            units.append(text)
            i += 1
    return units
