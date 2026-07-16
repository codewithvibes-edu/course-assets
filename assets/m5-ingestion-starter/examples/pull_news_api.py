"""
Worked example: paginated news API ingestion. Demonstrates the
APIIngester pattern with cursor-based pagination, retry/backoff, and
state persistence for crash recovery.

This example uses a fake in-process API for repeatability. Replace
fetch_one_page() with a real httpx call against your provider.

Usage:
    python examples/pull_news_api.py --output out.jsonl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.api_pull import APIIngester
from ingestion.records import IngestRecord


# ---- A tiny fake API so the example is runnable without keys ----

FAKE_PAGES = [
    {
        "items": [
            {"id": "n-1", "title": "Anthropic ships X", "published": "2026-05-06", "body": "..."},
            {"id": "n-2", "title": "OpenAI launches Y", "published": "2026-05-06", "body": "..."},
        ],
        "next_cursor": "cursor-2",
    },
    {
        "items": [
            {"id": "n-3", "title": "Vector DBs benchmarked", "published": "2026-05-05", "body": "..."},
        ],
        "next_cursor": "cursor-3",
    },
    {
        "items": [
            {"id": "n-4", "title": "RAG patterns roundup", "published": "2026-05-05", "body": "..."},
        ],
        "next_cursor": None,
    },
]


def fetch_one_page(cursor: str | None) -> tuple[list[dict], str | None]:
    if cursor is None:
        page = FAKE_PAGES[0]
    elif cursor == "cursor-2":
        page = FAKE_PAGES[1]
    elif cursor == "cursor-3":
        page = FAKE_PAGES[2]
    else:
        return [], None
    return page["items"], page["next_cursor"]


def to_record(item: dict) -> IngestRecord:
    return IngestRecord(
        source_id=item["id"],
        source_type="api",
        source_name="news_api_demo",
        payload=item,
        metadata={"published": item.get("published")},
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--state-path", type=Path, default=Path(".state/news_api_cursor"))
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    ingester = APIIngester(
        name="news_api_demo",
        state_path=args.state_path,
        fetch=fetch_one_page,
        to_record=to_record,
    )

    n = 0
    with args.output.open("w", encoding="utf-8") as out:
        for record in ingester.run():
            out.write(record.to_jsonl() + "\n")
            n += 1

    print(f"Ingested {n} record(s) to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
