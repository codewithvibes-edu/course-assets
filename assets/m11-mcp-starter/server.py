"""
Minimal MCP server demonstrating tools, resources, and prompts.
Wraps a personal notes SQLite database.

Run with:
    python server.py

Wire to Claude Desktop via claude_config.json.example.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

DB = Path(__file__).parent / "notes.db"

mcp = FastMCP("notes-server")


def _conn():
    return sqlite3.connect(DB)


# ---------- Tools ----------


@mcp.tool()
def search_notes(query: str, limit: int = 5) -> list[dict]:
    """
    Search the user's personal notes by keyword.
    Returns up to 'limit' matching notes with id, title, excerpt, and created_at.
    Use this first when the user references their notes or past thoughts.
    """
    if not query.strip():
        return []
    pattern = f"%{query}%"
    rows = _conn().execute(
        "SELECT id, title, body, created_at FROM notes "
        "WHERE title LIKE ? OR body LIKE ? "
        "ORDER BY created_at DESC LIMIT ?",
        (pattern, pattern, limit),
    ).fetchall()
    return [
        {
            "id": row[0],
            "title": row[1],
            "excerpt": (row[2] or "")[:200],
            "created_at": row[3],
        }
        for row in rows
    ]


@mcp.tool()
def add_note(title: str, body: str = "") -> dict:
    """
    Append a new note to the user's notes database.
    Returns the new note's id and timestamp. Audit-logged via the database
    record itself (created_at is set automatically). Idempotency is the
    caller's concern; this tool is straightforwardly side-effecting.
    """
    if not title.strip():
        return {"error": "title cannot be empty"}
    cur = _conn()
    res = cur.execute(
        "INSERT INTO notes (title, body) VALUES (?, ?) RETURNING id, created_at",
        (title, body),
    )
    note_id, created_at = res.fetchone()
    cur.commit()
    return {"id": note_id, "title": title, "created_at": created_at}


@mcp.tool()
def count_notes_by_day(days: int = 30) -> list[dict]:
    """
    Aggregate notes per calendar day for the last 'days' days.
    Useful for spotting writing-cadence patterns. Read-only.
    """
    days = max(1, min(days, 365))
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = _conn().execute(
        "SELECT DATE(created_at) AS day, COUNT(*) FROM notes "
        "WHERE created_at >= ? "
        "GROUP BY day ORDER BY day DESC",
        (cutoff,),
    ).fetchall()
    return [{"day": day, "count": count} for day, count in rows]


# ---------- Resources ----------


@mcp.resource("notes://recent")
def recent_notes() -> str:
    """The 10 most recent notes as plain text, ready to embed in a prompt."""
    rows = _conn().execute(
        "SELECT title, body, created_at FROM notes ORDER BY created_at DESC LIMIT 10"
    ).fetchall()
    if not rows:
        return "No notes yet."
    return "\n\n".join(
        f"# {title}\n{body}\n_({created_at})_"
        for title, body, created_at in rows
    )


# ---------- Prompts ----------


@mcp.prompt()
def weekly_review() -> str:
    """
    A templated prompt that asks the model to summarize the user's
    notes from the past week into themes, surprising connections, and
    open questions to revisit.
    """
    return (
        "Use the search_notes tool to find notes from the last 7 days. "
        "Group them into themes. Identify any surprising connections between "
        "themes. List 3 open questions worth revisiting. Output as a short "
        "structured summary, no fluff."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
