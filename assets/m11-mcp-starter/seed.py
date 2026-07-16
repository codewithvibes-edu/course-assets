"""Initialize notes.db with the schema and a few sample rows."""

import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).parent / "notes.db.sql"
DB = Path(__file__).parent / "notes.db"

SAMPLES = [
    ("Idea for the weekly review", "Use the agent to surface notes I've forgotten about. Filter by date range; rank by recency * length."),
    ("Reading list", "Anthropic agent essay; Hamel on evals; modelcontextprotocol.io tutorials; Chip Huyen Ch 6."),
    ("Project notes — RAG starter", "Hybrid retrieval beat naive vector by ~12 hit-rate points on the small eval set."),
    ("Random thought", "Most LLM features that fail in production fail at the data layer, not the model."),
    ("Meeting summary", "Decided to ship the data layer first, agents second. Eval set before features."),
]


def main():
    if DB.exists():
        DB.unlink()
    conn = sqlite3.connect(DB)
    with open(SCHEMA) as f:
        conn.executescript(f.read())
    for title, body in SAMPLES:
        conn.execute("INSERT INTO notes (title, body) VALUES (?, ?)", (title, body))
    conn.commit()
    conn.close()
    print(f"Seeded {len(SAMPLES)} sample notes into {DB}.")


if __name__ == "__main__":
    main()
