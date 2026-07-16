"""Tests for cleaning.schema."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cleaning.schema import EnforcedRecord, validate_records


def _good_record() -> dict:
    return {
        "id": "rec-1",
        "source_name": "docs",
        "text": "This is a perfectly normal piece of cleaned text content.",
        "ingested_at": datetime.now(timezone.utc),
    }


def test_valid_record_validates():
    record = EnforcedRecord.model_validate(_good_record())
    assert record.id == "rec-1"
    assert record.cleaning_version == "1.0.0"


def test_text_too_short_rejects():
    raw = _good_record()
    raw["text"] = "abc"
    with pytest.raises(Exception):
        EnforcedRecord.model_validate(raw)


def test_non_alphabetic_text_rejects():
    raw = _good_record()
    raw["text"] = "1234567890 !!!!! @@@@@ ##### $$$$$$$"
    with pytest.raises(Exception):
        EnforcedRecord.model_validate(raw)


def test_missing_required_field_rejects():
    raw = _good_record()
    del raw["source_name"]
    with pytest.raises(Exception):
        EnforcedRecord.model_validate(raw)


def test_validate_records_drops_invalid():
    inputs = [_good_record(), {**_good_record(), "id": "rec-2"}, {"id": "broken"}]
    valid, rejected = validate_records(inputs)
    assert len(valid) == 2
    assert len(rejected) == 1


def test_validate_records_raise_mode():
    inputs = [_good_record(), {"id": "broken"}]
    with pytest.raises(Exception):
        validate_records(inputs, on_error="raise")
