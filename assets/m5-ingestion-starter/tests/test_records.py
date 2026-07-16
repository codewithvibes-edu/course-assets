"""Tests for the IngestRecord shape + hashing."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.records import IngestRecord, canonicalize, hash_record


def test_jsonl_round_trip():
    record = IngestRecord(
        source_id="s-1",
        source_type="file",
        source_name="docs",
        payload={"title": "hello", "body": "world"},
    )
    serialized = record.to_jsonl()
    parsed = json.loads(serialized)
    assert parsed["source_id"] == "s-1"
    assert parsed["payload"]["title"] == "hello"


def test_canonicalize_is_stable_across_key_order():
    a = canonicalize({"a": 1, "b": 2})
    b = canonicalize({"b": 2, "a": 1})
    assert a == b


def test_hash_record_identical_for_equivalent_records():
    r1 = IngestRecord(source_id="x", source_type="file", source_name="docs", payload={"a": 1, "b": 2})
    r2 = IngestRecord(source_id="x", source_type="file", source_name="docs", payload={"b": 2, "a": 1})
    assert hash_record(r1) == hash_record(r2)


def test_hash_record_differs_when_payload_differs():
    r1 = IngestRecord(source_id="x", source_type="file", source_name="docs", payload={"a": 1})
    r2 = IngestRecord(source_id="x", source_type="file", source_name="docs", payload={"a": 2})
    assert hash_record(r1) != hash_record(r2)


def test_hash_record_differs_when_source_id_differs():
    r1 = IngestRecord(source_id="a", source_type="file", source_name="docs", payload={"v": 1})
    r2 = IngestRecord(source_id="b", source_type="file", source_name="docs", payload={"v": 1})
    assert hash_record(r1) != hash_record(r2)
