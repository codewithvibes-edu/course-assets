"""
Data layer for the multi-platform content pipeline.

Ingests a long-form transcript (Whisper-style JSON), segments by
speaker turns and topic shifts, applies M6 cleaning (filler removal,
whitespace normalization, sentence boundary snapping), and stores
segments + previous published posts (for voice-consistency RAG) in
SQLite.

The agent layer (agent.py) reads segments + voice history through this
module's stable functions.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@dataclass
class Segment:
    """A speaker-bounded slice of a transcript."""

    id: str
    speaker: str
    text: str
    start_seconds: float
    end_seconds: float
    metadata: dict = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.end_seconds - self.start_seconds)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class HistoricalPost:
    """A previously published post; used for voice-consistency RAG."""

    id: str
    platform: str  # 'x' | 'ig' | 'linkedin' | 'tiktok'
    text: str
    published_at: str
    engagement_score: float = 0.0


# ---------- Cleaning ----------

# Common filler patterns. Module 6 covers cleaning operations in depth.
_FILLER_PATTERNS = (
    r"\bum+\b",
    r"\buh+\b",
    r"\blike\b(?= [,a-z])",  # "like, that thing" but not "like a"
    r"\byou know\b",
    r"\bI mean\b",
    r"\bsort of\b",
    r"\bkind of\b",
)
_FILLER_RE = re.compile("|".join(_FILLER_PATTERNS), re.IGNORECASE)


def clean_segment_text(text: str) -> str:
    """Normalize whitespace and strip common filler."""
    text = _FILLER_RE.sub("", text)
    return " ".join(text.split())


# ---------- Ingest ----------


def ingest_transcript(path: Path = None) -> list:
    """
    Read a Whisper-style transcript JSON; return cleaned Segment list.
    Each transcript entry: {id, speaker, text, start, end}.
    """
    if path is None:
        path = FIXTURES_DIR / "transcript.json"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fp:
        raw = json.load(fp)
    out = []
    for row in raw:
        out.append(
            Segment(
                id=row["id"],
                speaker=row.get("speaker", "host").lower(),
                text=clean_segment_text(row["text"]),
                start_seconds=float(row["start"]),
                end_seconds=float(row["end"]),
                metadata=row.get("metadata", {}),
            )
        )
    return out


def ingest_voice_history(path: Path = None) -> list:
    """Read prior posts for voice-consistency RAG."""
    if path is None:
        path = FIXTURES_DIR / "voice_history.jsonl"
    if not path.exists():
        return []
    out = []
    with path.open("r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            out.append(
                HistoricalPost(
                    id=row["id"],
                    platform=row["platform"].lower(),
                    text=row["text"],
                    published_at=row["published_at"],
                    engagement_score=float(row.get("engagement_score", 0.0)),
                )
            )
    return out


# ---------- Storage ----------


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS segments (
            id TEXT PRIMARY KEY,
            speaker TEXT NOT NULL,
            text TEXT NOT NULL,
            start_seconds REAL NOT NULL,
            end_seconds REAL NOT NULL,
            metadata_json TEXT
        );
        CREATE TABLE IF NOT EXISTS voice_history (
            id TEXT PRIMARY KEY,
            platform TEXT NOT NULL,
            text TEXT NOT NULL,
            published_at TEXT NOT NULL,
            engagement_score REAL NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_voice_platform ON voice_history(platform);
        """
    )


def build_store() -> sqlite3.Connection:
    """In-memory SQLite store loaded from fixtures. Idempotent."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _init_schema(conn)

    for seg in ingest_transcript():
        conn.execute(
            "INSERT INTO segments VALUES (?, ?, ?, ?, ?, ?)",
            (
                seg.id,
                seg.speaker,
                seg.text,
                seg.start_seconds,
                seg.end_seconds,
                json.dumps(seg.metadata),
            ),
        )
    for post in ingest_voice_history():
        conn.execute(
            "INSERT INTO voice_history VALUES (?, ?, ?, ?, ?)",
            (post.id, post.platform, post.text, post.published_at, post.engagement_score),
        )
    conn.commit()
    return conn


# ---------- Read API ----------


def all_segments(conn: sqlite3.Connection) -> list:
    rows = conn.execute("SELECT * FROM segments ORDER BY start_seconds").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["metadata"] = json.loads(d.pop("metadata_json") or "{}")
        out.append(Segment(**d))
    return out


def get_segment(conn: sqlite3.Connection, segment_id: str):
    row = conn.execute("SELECT * FROM segments WHERE id = ?", (segment_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["metadata"] = json.loads(d.pop("metadata_json") or "{}")
    return Segment(**d)


def voice_examples(conn: sqlite3.Connection, platform: str, limit: int = 3) -> list:
    """Top-engagement prior posts for the platform. Few-shot fodder."""
    rows = conn.execute(
        "SELECT * FROM voice_history WHERE platform = ? ORDER BY engagement_score DESC LIMIT ?",
        (platform.lower(), limit),
    ).fetchall()
    return [HistoricalPost(**dict(r)) for r in rows]
