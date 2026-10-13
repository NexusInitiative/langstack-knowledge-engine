"""A tiny three-document corpus used by the integration tests."""

from pathlib import Path


def doc(doc_id, title, series, product, tier, sections, extra=""):
    body = "\n\n".join(f"## {sid} — {h}\n\n{text}" for sid, h, text in sections)
    tier_line = f"source_tier: {tier}\n" if tier else ""
    return (
        f"---\ndoc_id: {doc_id}\ntitle: {title}\nseries: {series}\nproduct: {product}\n"
        f"{tier_line}last_verified: 2026-08-13\ntags: [t]\n{extra}---\n\n# {doc_id}\n\n{body}\n"
    )


FILES = {
    "lg/LG-04.md": doc("LG-04", "LangGraph Persistence", "LG", "LangGraph", 1, [
        ("LG-04.1", "Checkpointers", "A checkpointer saves graph state per thread_id. Use AsyncPostgresSaver in production. See `SH-07` for errors."),
        ("LG-04.2", "Threads", "Each thread has an independent history identified by thread_id."),
    ]),
    "lg/LG-03.md": doc("LG-03", "LangGraph Reducers", "LG", "LangGraph", 1, [
        ("LG-03.1", "Reducers", "Concurrent writes to one state key raise InvalidUpdateError unless the key has a reducer."),
    ]),
    "lc/LC-04.md": doc("LC-04", "LangChain Structured Output", "LC", "LangChain", 2, [
        ("LC-04.1", "response_format", "Pass response_format to create_agent to get typed structured output from the model."),
    ]),
    "sh/SH-07.md": doc("SH-07", "Errors", "SH", "both", 3, [
        ("SH-07.1", "Troubleshooting", "InvalidUpdateError means two nodes wrote the same key in one superstep without a reducer."),
    ]),
    "_meta/M.md": doc("META-99", "Housekeeping", "META", "both", None, [
        ("META-99.1", "Register", "Source register entry mentioning checkpointer and reducer."),
    ]),
}


def write_corpus(root: Path) -> Path:
    for rel, text in FILES.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return root
