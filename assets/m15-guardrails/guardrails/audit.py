"""
Audit log helper. Append-only event records for high-stakes agent actions.
Use for irreversible actions (refunds, sends, deletes) so post-hoc
investigation is possible.
"""

from __future__ import annotations

import json
import os
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class AuditEvent:
    timestamp: str
    actor: str
    action: str
    target_type: str | None = None
    target_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    outcome: str | None = None  # "success" | "failure" | "pending"


class AuditLogger:
    """
    Thread-safe JSONL audit logger. Each call to log() appends one
    JSON object on a single line. Files are rotated daily by default.

    Production deployments should mirror to a separate immutable store
    (Supabase audit_log table, S3 with object lock, append-only DB).
    The local file is for development convenience.
    """

    def __init__(self, log_dir: Path | str = "audit_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _path_for_today(self) -> Path:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.log_dir / f"audit-{day}.jsonl"

    def log(
        self,
        actor: str,
        action: str,
        *,
        target_type: str | None = None,
        target_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        outcome: str | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata or {},
            outcome=outcome,
        )
        line = json.dumps(event.__dict__, ensure_ascii=False, default=str)
        path = self._path_for_today()
        with self._lock:
            try:
                with path.open("a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except OSError as exc:
                # Audit failure should not crash the calling flow; log to stderr.
                print(f"[audit] write failed: {exc}", file=sys.stderr)
        return event

    def read_all(self, day: str | None = None) -> list[dict[str, Any]]:
        """Read events for a given day (default: today)."""
        if day is None:
            day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = self.log_dir / f"audit-{day}.jsonl"
        if not path.exists():
            return []
        events: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return events
