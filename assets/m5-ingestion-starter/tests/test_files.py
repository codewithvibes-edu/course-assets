"""Tests for file ingestion (CSV, JSONL). PDF tests skipped without pdfplumber."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.files import ingest_csv, ingest_jsonl


def test_csv_basic(tmp_path: Path):
    p = tmp_path / "rows.csv"
    p.write_text("name,age\nalice,30\nbob,25\n", encoding="utf-8")
    records = list(ingest_csv(p, source_name="test"))
    assert len(records) == 2
    assert records[0].payload["name"] == "alice"
    assert records[0].source_type == "file"
    assert records[1].payload["age"] == "25"


def test_csv_strips_whitespace(tmp_path: Path):
    p = tmp_path / "rows.csv"
    p.write_text("name,age\n  alice  ,  30  \n", encoding="utf-8")
    records = list(ingest_csv(p))
    assert records[0].payload["name"] == "alice"


def test_csv_handles_utf8_bom(tmp_path: Path):
    p = tmp_path / "rows.csv"
    # Write with BOM
    p.write_bytes("﻿name,age\nalice,30\n".encode("utf-8"))
    records = list(ingest_csv(p))
    assert len(records) == 1
    # The BOM should be stripped from the first column header by utf-8-sig fallback
    assert "alice" in records[0].payload.values()


def test_jsonl_basic(tmp_path: Path):
    p = tmp_path / "data.jsonl"
    p.write_text(
        '{"id": "x", "v": 1}\n'
        '{"id": "y", "v": 2}\n',
        encoding="utf-8",
    )
    records = list(ingest_jsonl(p))
    assert len(records) == 2
    assert records[0].source_id == "x"
    assert records[1].payload["v"] == 2


def test_jsonl_skips_blank_lines(tmp_path: Path):
    p = tmp_path / "data.jsonl"
    p.write_text(
        '{"id": "a"}\n'
        "\n"
        '{"id": "b"}\n',
        encoding="utf-8",
    )
    records = list(ingest_jsonl(p))
    assert len(records) == 2


def test_jsonl_raises_on_malformed(tmp_path: Path):
    p = tmp_path / "data.jsonl"
    p.write_text('{"id": "a"}\nnot json\n', encoding="utf-8")
    with pytest.raises(Exception):
        list(ingest_jsonl(p))


def test_jsonl_falls_back_source_id_when_id_missing(tmp_path: Path):
    p = tmp_path / "data.jsonl"
    p.write_text('{"v": 1}\n', encoding="utf-8")
    records = list(ingest_jsonl(p))
    assert "line_1" in records[0].source_id
