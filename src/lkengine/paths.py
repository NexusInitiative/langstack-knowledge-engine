"""Filesystem locations that ship inside the package."""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
CORPUS_DIR = PACKAGE_DIR / "corpus"
GOLDEN_SET_PATH = CORPUS_DIR / "rag" / "eval_questions.jsonl"
SCHEMA_PATH = PACKAGE_DIR / "db" / "schema.sql"
