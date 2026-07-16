"""Tests for tracking.tracer."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tracking.tracer import Tracer, TraceSpan


def test_write_and_query(tmp_path: Path):
    db = tmp_path / "traces.db"
    tracer = Tracer(db_path=db)
    span = TraceSpan(
        trace_id="t1",
        agent="responder",
        model="claude-sonnet-4-6",
        input_tokens=100,
        output_tokens=50,
        cost_cents=0.25,
        outcome="success",
    )
    tracer.write(span)
    rows = tracer.query("SELECT * FROM traces WHERE trace_id = ?", ("t1",))
    assert len(rows) == 1
    assert rows[0]["agent"] == "responder"
    assert rows[0]["input_tokens"] == 100
    tracer.close()


def test_span_context_manager_records_duration(tmp_path: Path):
    tracer = Tracer(db_path=tmp_path / "traces.db")
    with tracer.span(agent="r", model="claude-sonnet-4-6") as span:
        span.input_tokens = 10
        span.output_tokens = 5
    rows = tracer.query("SELECT duration_ms, outcome FROM traces ORDER BY started_at DESC LIMIT 1")
    assert rows[0]["duration_ms"] >= 0
    assert rows[0]["outcome"] == "success"


def test_span_records_failure(tmp_path: Path):
    tracer = Tracer(db_path=tmp_path / "traces.db")
    with pytest.raises(RuntimeError):
        with tracer.span(agent="r"):
            raise RuntimeError("nope")
    rows = tracer.query(
        "SELECT outcome, error FROM traces ORDER BY started_at DESC LIMIT 1"
    )
    assert rows[0]["outcome"] == "failure"
    assert "RuntimeError" in (rows[0]["error"] or "")


def test_replace_on_duplicate_span_id(tmp_path: Path):
    tracer = Tracer(db_path=tmp_path / "traces.db")
    span = TraceSpan(span_id="fixed", trace_id="t1", agent="a", outcome="success")
    tracer.write(span)
    span.outcome = "failure"
    tracer.write(span)  # INSERT OR REPLACE
    rows = tracer.query("SELECT outcome FROM traces WHERE span_id = ?", ("fixed",))
    assert len(rows) == 1
    assert rows[0]["outcome"] == "failure"
