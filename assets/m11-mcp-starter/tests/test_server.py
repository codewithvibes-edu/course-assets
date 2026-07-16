"""Smoke tests for the notes MCP server. Tests against a fresh DB."""

import os
import sys
import sqlite3
from pathlib import Path

import pytest

# Run against an isolated DB; do not clobber the seeded notes.db.
TEST_DB = Path(__file__).parent / "test_notes.db"
os.environ["NOTES_DB_PATH"] = str(TEST_DB)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def _fresh_db(monkeypatch):
    if TEST_DB.exists():
        TEST_DB.unlink()
    schema = (Path(__file__).parent.parent / "notes.db.sql").read_text()
    conn = sqlite3.connect(TEST_DB)
    conn.executescript(schema)
    conn.commit()
    conn.close()

    # Patch the DB path in server.py
    import server
    monkeypatch.setattr(server, "DB", TEST_DB)
    yield
    if TEST_DB.exists():
        TEST_DB.unlink()


def test_add_then_search():
    from server import add_note, search_notes

    res = add_note("Test title", "Body containing the word elephant")
    assert "id" in res

    matches = search_notes("elephant")
    assert len(matches) == 1
    assert "elephant" in matches[0]["excerpt"]


def test_search_empty_query_returns_nothing():
    from server import search_notes
    assert search_notes("") == []


def test_count_by_day_returns_recent():
    from server import add_note, count_notes_by_day

    add_note("a", "")
    add_note("b", "")

    counts = count_notes_by_day(days=1)
    # Both adds happened today; one row, count of 2
    assert len(counts) == 1
    assert counts[0]["count"] == 2
