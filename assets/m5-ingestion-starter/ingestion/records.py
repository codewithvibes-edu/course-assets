"""
Canonical record shape. Every ingestion path produces records of this
shape so downstream cleaning + storage code does not have to special-case
by source type.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass
class IngestRecord:
    source_id: str            # natural ID from the source (URL, primary key, file path)
    source_type: str          # 'file' | 'api' | 'webhook' | 'scrape'
    source_name: str          # name of the source system (e.g., 'newsapi', 'gmail', 'docs/')
    payload: dict[str, Any]   # the actual data
    ingested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_jsonl(self) -> str:
        """One JSON object per line, stable key order, no embedded newlines."""
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)


def canonicalize(payload: dict[str, Any]) -> str:
    """
    Stable serialization for hashing: sorted keys, no whitespace.
    Useful for dedup and idempotency keys.
    """
    return json.dumps(payload, separators=(",", ":"), sort_keys=True, default=str)


def hash_record(record: IngestRecord) -> str:
    """SHA-256 over (source_type, source_name, source_id, canonical payload)."""
    parts = [
        record.source_type,
        record.source_name,
        record.source_id,
        canonicalize(record.payload),
    ]
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest
