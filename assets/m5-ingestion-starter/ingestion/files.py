"""
File ingestion: PDF, CSV, JSON / JSONL. Each generator yields IngestRecord
instances ready for downstream cleaning + storage.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterator

from .records import IngestRecord


def ingest_pdf(path: Path, source_name: str | None = None) -> IngestRecord:
    """
    Extract text + metadata from a single PDF using pdfplumber.
    Returns one record per file with pages as a list under payload.
    """
    import pdfplumber  # imported lazily so the module loads without pdfplumber installed

    with pdfplumber.open(path) as pdf:
        pages = []
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            pages.append({"page_num": i + 1, "text": text})
        metadata = pdf.metadata or {}

    return IngestRecord(
        source_id=str(path),
        source_type="file",
        source_name=source_name or "pdf",
        payload={
            "title": metadata.get("Title", ""),
            "author": metadata.get("Author", ""),
            "pages": pages,
            "page_count": len(pages),
        },
        metadata={"format": "pdf", "size_bytes": path.stat().st_size if path.exists() else None},
    )


def ingest_csv(
    path: Path,
    source_name: str | None = None,
    *,
    encoding: str | None = None,
) -> Iterator[IngestRecord]:
    """
    Yield one IngestRecord per CSV row. Tries the supplied encoding first;
    on failure, retries with utf-8-sig and latin-1 (the most common shapes
    we see for CSVs out in the wild).
    """
    encodings_to_try = [encoding] if encoding else ["utf-8", "utf-8-sig", "latin-1"]

    last_exc: Exception | None = None
    for enc in encodings_to_try:
        if enc is None:
            continue
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, 1):
                    yield IngestRecord(
                        source_id=f"{path}:row_{row_num}",
                        source_type="file",
                        source_name=source_name or "csv",
                        payload={k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()},
                        metadata={"format": "csv", "encoding": enc, "row_num": row_num},
                    )
            return
        except UnicodeDecodeError as exc:
            last_exc = exc
            continue
    if last_exc is not None:
        raise last_exc


def ingest_jsonl(path: Path, source_name: str | None = None) -> Iterator[IngestRecord]:
    """
    Yield one IngestRecord per JSON line. Skip blank lines; raise on parse
    error so malformed input is loud, not silent.
    """
    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            # Source ID: prefer an `id` field if present; fall back to file:line.
            sid = str(payload.get("id", f"{path}:line_{line_num}"))
            yield IngestRecord(
                source_id=sid,
                source_type="file",
                source_name=source_name or "jsonl",
                payload=payload if isinstance(payload, dict) else {"value": payload},
                metadata={"format": "jsonl", "line_num": line_num},
            )
