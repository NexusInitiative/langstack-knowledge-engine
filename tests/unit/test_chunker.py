"""Structure-aware chunking (issue E2-3): heading-bounded, token-capped,
and a code fence is never separated from its lead-in prose."""

from lkengine.ingest.chunker import approx_tokens, split_section_body

HEADING = "## X-01.1 — Title"


def para(n_words: int, tag: str = "w") -> str:
    return " ".join(f"{tag}{i}" for i in range(n_words))


def test_small_section_is_a_single_part():
    body = f"{HEADING}\n\nShort body."
    assert split_section_body(body, max_tokens=100) == [body]


def test_oversized_section_splits_on_paragraph_boundaries_under_cap():
    body = "\n\n".join([HEADING] + [para(60, f"p{i}_") for i in range(6)])
    parts = split_section_body(body, max_tokens=150)
    assert len(parts) > 1
    assert all(approx_tokens(p) <= 150 for p in parts)
    # no paragraph is cut in half: every original paragraph appears intact exactly once
    joined = "\n\n".join(parts)
    for i in range(6):
        assert para(60, f"p{i}_") in joined


def test_every_part_after_the_first_repeats_the_heading_for_context():
    body = "\n\n".join([HEADING] + [para(60, f"p{i}_") for i in range(6)])
    parts = split_section_body(body, max_tokens=150)
    assert parts[0].startswith(HEADING)
    for p in parts[1:]:
        assert p.startswith(HEADING + " (cont.)")


def test_code_fence_stays_with_its_lead_in_paragraph():
    lead = "Use the checkpointer like this:"
    fence = "```python\nx = 1\n\ny = 2\n```"  # blank line inside the fence
    body = "\n\n".join([HEADING, para(80, "a"), lead, fence, para(80, "b")])
    parts = split_section_body(body, max_tokens=150)
    holder = [p for p in parts if fence in p]
    assert len(holder) == 1
    assert lead in holder[0]
    assert holder[0].index(lead) < holder[0].index(fence)


def test_fence_is_never_split_even_when_it_alone_exceeds_the_cap():
    fence = "```\n" + "\n".join(f"line {i}" for i in range(200)) + "\n```"
    body = "\n\n".join([HEADING, "Lead-in:", fence])
    parts = split_section_body(body, max_tokens=50)
    holder = [p for p in parts if "line 0" in p]
    assert len(holder) == 1 and "line 199" in holder[0]  # whole fence together


def test_blank_lines_inside_fences_do_not_create_paragraph_breaks():
    fence = "```\na\n\n\nb\n```"
    body = f"{HEADING}\n\n{fence}"
    assert split_section_body(body, max_tokens=1000) == [body]


def test_approx_tokens_uses_words_times_1_4_rounded_up():
    assert approx_tokens("one two three four five") == 7  # ceil(5 * 1.4)
    assert approx_tokens("") == 0
