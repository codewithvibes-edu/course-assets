"""
Data layer for the research-papers assistant.

Ingests a folder of pre-extracted paper texts (real implementations
use LlamaParse / pdfplumber on actual PDFs — see Module 5), applies
section-aware chunking (Module 6), indexes by token-overlap BM25-style
+ keyword tags (Module 7's hybrid retrieval reduced to its simplest
form), and stores both papers and chunks in SQLite.

The agent layer (agent.py) calls search_library / get_chunks /
known_paper_ids through this module.

Real implementations would swap the toy retrieval for pgvector + a
real embedding model + a reranker (Module 7). The schema below stays
stable across that swap.
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


# ---------- Schema ----------


@dataclass
class Paper:
    id: str
    title: str
    authors: list = field(default_factory=list)
    year: int = 0
    venue: str = ""
    sections: dict = field(default_factory=dict)  # 'abstract' / 'methods' / 'results' / 'discussion'
    keywords: list = field(default_factory=list)


@dataclass
class Chunk:
    """A retrieval-sized slice of a paper. Section-aware (M6 pattern)."""

    id: str
    paper_id: str
    section: str  # 'abstract' | 'methods' | 'results' | 'discussion'
    text: str


# ---------- Ingest ----------


_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokens(text: str) -> list:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _chunk_paper(paper: Paper) -> list:
    """Section-aware chunking. One chunk per section."""
    out = []
    for section_name, section_text in paper.sections.items():
        if not section_text.strip():
            continue
        out.append(
            Chunk(
                id=f"{paper.id}-{section_name}",
                paper_id=paper.id,
                section=section_name,
                text=section_text.strip(),
            )
        )
    return out


def ingest_library(path: Path = None) -> list:
    """Read the library JSON; return typed Paper records."""
    if path is None:
        path = FIXTURES_DIR / "library.json"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fp:
        raw = json.load(fp)
    out = []
    for row in raw:
        out.append(
            Paper(
                id=row["id"],
                title=row["title"].strip(),
                authors=list(row.get("authors", [])),
                year=int(row.get("year", 0)),
                venue=row.get("venue", "").strip(),
                sections={k: v.strip() for k, v in (row.get("sections") or {}).items()},
                keywords=[k.lower() for k in row.get("keywords", [])],
            )
        )
    return out


# ---------- Storage ----------


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS papers (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            authors_json TEXT NOT NULL,
            year INTEGER NOT NULL,
            venue TEXT NOT NULL,
            keywords_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY,
            paper_id TEXT NOT NULL,
            section TEXT NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY (paper_id) REFERENCES papers(id)
        );
        CREATE INDEX IF NOT EXISTS idx_chunks_paper ON chunks(paper_id);
        """
    )


def build_store() -> sqlite3.Connection:
    """In-memory SQLite store loaded from fixtures. Idempotent."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _init_schema(conn)
    for p in ingest_library():
        conn.execute(
            "INSERT INTO papers VALUES (?, ?, ?, ?, ?, ?)",
            (p.id, p.title, json.dumps(p.authors), p.year, p.venue, json.dumps(p.keywords)),
        )
        for c in _chunk_paper(p):
            conn.execute(
                "INSERT INTO chunks VALUES (?, ?, ?, ?)",
                (c.id, c.paper_id, c.section, c.text),
            )
    conn.commit()
    return conn


# ---------- Read API ----------


def _paper_from_row(row: sqlite3.Row, sections: dict = None) -> Paper:
    return Paper(
        id=row["id"],
        title=row["title"],
        authors=json.loads(row["authors_json"]),
        year=row["year"],
        venue=row["venue"],
        keywords=json.loads(row["keywords_json"]),
        sections=sections or {},
    )


def get_paper(conn: sqlite3.Connection, paper_id: str):
    row = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
    if not row:
        return None
    chunk_rows = conn.execute(
        "SELECT section, text FROM chunks WHERE paper_id = ?", (paper_id,)
    ).fetchall()
    sections = {r["section"]: r["text"] for r in chunk_rows}
    return _paper_from_row(row, sections)


def all_papers(conn: sqlite3.Connection) -> list:
    rows = conn.execute("SELECT * FROM papers").fetchall()
    out = []
    for row in rows:
        chunk_rows = conn.execute(
            "SELECT section, text FROM chunks WHERE paper_id = ?", (row["id"],)
        ).fetchall()
        sections = {r["section"]: r["text"] for r in chunk_rows}
        out.append(_paper_from_row(row, sections))
    return out


def known_paper_ids(conn: sqlite3.Connection) -> set:
    rows = conn.execute("SELECT id FROM papers").fetchall()
    return {r["id"] for r in rows}


def get_chunks(conn: sqlite3.Connection, paper_id: str) -> list:
    rows = conn.execute(
        "SELECT * FROM chunks WHERE paper_id = ?", (paper_id,)
    ).fetchall()
    return [Chunk(**dict(r)) for r in rows]


# ---------- Retrieval (hybrid-lite) ----------


def _score_chunk(query_tokens: set, chunk_text: str, title: str, keywords: list) -> float:
    """
    Token-overlap BM25-style score boosted by title + keyword matches.
    This is a toy stand-in for the real hybrid retrieval covered in M7.
    """
    chunk_tokens = set(_tokens(chunk_text))
    title_tokens = set(_tokens(title))
    keyword_tokens = set(keywords)
    base = len(query_tokens & chunk_tokens)
    if base == 0 and not (query_tokens & title_tokens) and not (query_tokens & keyword_tokens):
        return 0.0
    title_bonus = 2.0 * len(query_tokens & title_tokens)
    keyword_bonus = 3.0 * len(query_tokens & keyword_tokens)
    # Light length normalization so short hits don't dominate
    norm = math.log(len(chunk_tokens) + 2)
    return (base + title_bonus + keyword_bonus) / norm


def search_library(conn: sqlite3.Connection, query: str, top_k: int = 5) -> list:
    """
    Toy hybrid retrieval: score each chunk by token overlap with title
    + keywords + body. Return top_k Papers (deduped, ordered by best
    chunk score).
    """
    query_tokens = set(_tokens(query))
    if not query_tokens:
        return []
    papers = all_papers(conn)
    best_per_paper: dict = {}
    for p in papers:
        for section_text in p.sections.values():
            score = _score_chunk(query_tokens, section_text, p.title, p.keywords)
            if score > best_per_paper.get(p.id, (0.0, None))[0]:
                best_per_paper[p.id] = (score, p)
    ranked = sorted(
        ((s, p) for s, p in best_per_paper.values() if s > 0),
        key=lambda x: x[0],
        reverse=True,
    )
    return [p for _, p in ranked[:top_k]]
