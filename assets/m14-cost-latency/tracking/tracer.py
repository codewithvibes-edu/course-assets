"""
SQLite-backed trace store. Every LLM call writes one TraceSpan row.
Schema mirrors what production teams ship to OpenTelemetry / Langfuse /
custom Postgres tables; SQLite is the dev default so the starter runs
without infra.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


_SCHEMA = """
CREATE TABLE IF NOT EXISTS traces (
    span_id        TEXT PRIMARY KEY,
    trace_id       TEXT NOT NULL,
    parent_span_id TEXT,
    agent          TEXT,
    model          TEXT,
    started_at     TEXT NOT NULL,
    completed_at   TEXT,
    duration_ms    INTEGER,
    input_tokens   INTEGER,
    output_tokens  INTEGER,
    cost_cents     REAL,
    outcome        TEXT,
    error          TEXT,
    metadata       TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_traces_trace_id ON traces (trace_id);
CREATE INDEX IF NOT EXISTS idx_traces_started_at ON traces (started_at DESC);
CREATE INDEX IF NOT EXISTS idx_traces_agent_started ON traces (agent, started_at DESC);
"""


@dataclass
class TraceSpan:
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    trace_id: str = ""
    parent_span_id: str | None = None
    agent: str | None = None
    model: str | None = None
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str | None = None
    duration_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_cents: float | None = None
    outcome: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_row(self) -> tuple:
        return (
            self.span_id,
            self.trace_id,
            self.parent_span_id,
            self.agent,
            self.model,
            self.started_at,
            self.completed_at,
            self.duration_ms,
            self.input_tokens,
            self.output_tokens,
            self.cost_cents,
            self.outcome,
            self.error,
            json.dumps(self.metadata, default=str),
        )


class Tracer:
    """SQLite-backed trace store with per-process thread safety."""

    def __init__(self, db_path: Path | str = "traces.db"):
        self.db_path = Path(db_path)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def write(self, span: TraceSpan) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO traces VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                span.as_row(),
            )
            self._conn.commit()

    def query(self, sql: str, params: tuple | None = None) -> list[dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute(sql, params or ())
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def span(
        self,
        agent: str | None = None,
        model: str | None = None,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Iterator[TraceSpan]:
        """
        Context manager that creates a TraceSpan, yields it for mutation,
        then writes on exit. Exceptions are recorded in `error` and
        `outcome='failure'`.
        """
        import time

        span = TraceSpan(
            trace_id=trace_id or uuid.uuid4().hex[:16],
            parent_span_id=parent_span_id,
            agent=agent,
            model=model,
            metadata=metadata or {},
        )
        t0 = time.perf_counter()
        try:
            yield span
            if span.outcome is None:
                span.outcome = "success"
        except Exception as exc:
            span.outcome = "failure"
            span.error = f"{type(exc).__name__}: {exc}"[:500]
            raise
        finally:
            span.completed_at = datetime.now(timezone.utc).isoformat()
            span.duration_ms = int((time.perf_counter() - t0) * 1000)
            self.write(span)
