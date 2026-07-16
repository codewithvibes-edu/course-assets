"""
Worked example: SQL-backed cost dashboard. Queries the trace store
(populated by tracked() / traced()) and prints daily breakdowns.

This is what production teams build on top of their trace store. With
SQLite the queries below are 1:1 with what you would run against a
Postgres traces table.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tracking.tracer import Tracer


def cost_by_agent(tracer: Tracer, days: int = 7) -> list[dict]:
    sql = """
    SELECT
        DATE(started_at) AS day,
        agent,
        model,
        COUNT(*) AS calls,
        COALESCE(SUM(input_tokens), 0)  AS input_tokens,
        COALESCE(SUM(output_tokens), 0) AS output_tokens,
        ROUND(COALESCE(SUM(cost_cents), 0) / 100.0, 4) AS cost_usd,
        ROUND(AVG(duration_ms), 1) AS avg_latency_ms
    FROM traces
    WHERE started_at >= datetime('now', ?)
    GROUP BY day, agent, model
    ORDER BY day DESC, cost_usd DESC
    """
    return tracer.query(sql, (f"-{days} days",))


def fallback_rate(tracer: Tracer, hours: int = 24) -> dict:
    """Returns {fallback_count, total_count, rate} for the last N hours."""
    sql_total = "SELECT COUNT(*) AS total FROM traces WHERE started_at >= datetime('now', ?)"
    sql_fb = """
    SELECT COUNT(*) AS fb FROM traces
    WHERE started_at >= datetime('now', ?)
      AND json_extract(metadata, '$.fallback_level') > 0
    """
    total = tracer.query(sql_total, (f"-{hours} hours",))[0]["total"]
    fb = tracer.query(sql_fb, (f"-{hours} hours",))[0]["fb"]
    return {
        "total": total,
        "fallback": fb,
        "rate": round(fb / max(total, 1), 4),
    }


def slow_calls(tracer: Tracer, threshold_ms: int = 3000, limit: int = 20) -> list[dict]:
    sql = """
    SELECT span_id, agent, model, duration_ms, started_at
    FROM traces
    WHERE duration_ms >= ?
    ORDER BY duration_ms DESC
    LIMIT ?
    """
    return tracer.query(sql, (threshold_ms, limit))


def main():
    tracer = Tracer(db_path="traces.db")

    print("=== Cost by agent (last 7 days) ===")
    rows = cost_by_agent(tracer, days=7)
    if not rows:
        print("(no traces; run examples/tracked_call.py first)")
    for row in rows:
        print(
            f"  {row['day']}  {row['agent'] or '-'}  {row['model'] or '-'}  "
            f"calls={row['calls']}  cost=${row['cost_usd']:.4f}  "
            f"avg_latency={row['avg_latency_ms'] or 0:.0f}ms"
        )

    print("\n=== Fallback rate (last 24h) ===")
    fr = fallback_rate(tracer, hours=24)
    print(f"  {fr['fallback']}/{fr['total']} = {fr['rate']:.2%}")

    print("\n=== Slowest 10 calls (>3000ms) ===")
    slow = slow_calls(tracer, threshold_ms=3000, limit=10)
    if not slow:
        print("  (none)")
    for row in slow:
        print(f"  {row['span_id']}  {row['duration_ms']}ms  {row['agent'] or '-'}  {row['started_at']}")


if __name__ == "__main__":
    main()
