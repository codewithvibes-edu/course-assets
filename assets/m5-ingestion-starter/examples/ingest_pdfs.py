"""
Worked example: ingest a folder of PDFs and write IngestRecords to a
JSONL file. Failures on individual files are logged to stderr and the
loop continues.

Usage:
    python examples/ingest_pdfs.py --input-dir ./sample_pdfs --output out.jsonl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add the parent so we can import from ingestion.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.files import ingest_pdf


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-name", default="docs")
    args = parser.parse_args()

    if not args.input_dir.is_dir():
        print(f"Not a directory: {args.input_dir}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)

    n_ok = 0
    n_fail = 0
    with args.output.open("w", encoding="utf-8") as out:
        for pdf_path in sorted(args.input_dir.rglob("*.pdf")):
            try:
                record = ingest_pdf(pdf_path, source_name=args.source_name)
                out.write(record.to_jsonl() + "\n")
                n_ok += 1
            except Exception as exc:
                print(f"failed: {pdf_path}: {exc}", file=sys.stderr)
                n_fail += 1

    print(f"Ingested {n_ok} PDF(s); {n_fail} failed.")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
