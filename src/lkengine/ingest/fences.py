"""CommonMark-style fenced-code-block tracking, shared by parser and chunker.

A naive "toggle on any ``` or ~~~ line" breaks on legitimate markdown such as a
```` ````markdown ```` block that *demonstrates* a ```` ``` ```` fence, or a
``~~~`` block containing backticks. CommonMark's rule is: a fence closes only
on a line of the **same character**, **at least as long** as the opener, with
nothing after it. That is all this implements (indentation > 3 spaces and
info-string subtleties are ignored; the corpus doesn't use them).
"""

from __future__ import annotations

import re

_FENCE_LINE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


class FenceTracker:
    """Feed lines in order; ``update`` reports what each line is."""

    def __init__(self) -> None:
        self._open: tuple[str, int] | None = None  # (char, length) of the open fence

    @property
    def in_fence(self) -> bool:
        return self._open is not None

    def update(self, line: str) -> str:
        """Return ``'open'``, ``'close'``, ``'inside'`` or ``'outside'`` for ``line``."""
        m = _FENCE_LINE.match(line)
        if self._open is None:
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):  # info string can't hold `
                self._open = (m.group(1)[0], len(m.group(1)))
                return "open"
            return "outside"
        char, length = self._open
        if m and m.group(1)[0] == char and len(m.group(1)) >= length and not m.group(2).strip():
            self._open = None
            return "close"
        return "inside"


def contains_fence(text: str) -> bool:
    """True if ``text`` contains at least one fenced code block."""
    tracker = FenceTracker()
    return any(tracker.update(line) == "open" for line in text.split("\n"))
