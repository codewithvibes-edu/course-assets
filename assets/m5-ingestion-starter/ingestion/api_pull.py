"""
Cursor-based paginated API ingestion with retries, rate-limit handling,
and persistent state so a crashed run resumes where it left off.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator

import httpx

from .records import IngestRecord


class RateLimited(Exception):
    """Raised when the upstream API returns 429."""


class PermanentError(Exception):
    """Raised when the upstream returns a non-retryable status (4xx other than 429)."""


@dataclass
class APIIngester:
    """
    Generic paginated API ingester. The caller supplies:
      - a fetch function that takes a cursor and returns (items, next_cursor)
      - a record-builder that maps an item dict to an IngestRecord

    The ingester handles retries, backoff, cursor persistence, and a
    consistent IngestRecord output stream.
    """

    name: str
    state_path: Path
    fetch: Callable[[str | None], tuple[list[dict[str, Any]], str | None]]
    to_record: Callable[[dict[str, Any]], IngestRecord]
    max_retries: int = 5
    base_backoff: float = 1.0
    max_pages: int | None = None

    def _load_cursor(self) -> str | None:
        if self.state_path.exists():
            text = self.state_path.read_text().strip()
            return text or None
        return None

    def _save_cursor(self, cursor: str | None) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(cursor or "")

    def _fetch_with_retries(self, cursor: str | None) -> tuple[list[dict[str, Any]], str | None]:
        for attempt in range(self.max_retries):
            try:
                return self.fetch(cursor)
            except RateLimited:
                delay = self.base_backoff * (2**attempt)
                time.sleep(delay)
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code if exc.response is not None else 0
                if status == 429:
                    delay = self.base_backoff * (2**attempt)
                    time.sleep(delay)
                elif 500 <= status < 600:
                    delay = self.base_backoff * (2**attempt)
                    time.sleep(delay)
                elif 400 <= status < 500:
                    raise PermanentError(f"{status} on cursor={cursor!r}: {exc}") from exc
                else:
                    raise
            except httpx.RequestError:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.base_backoff * (2**attempt))
        raise RuntimeError("max retries exceeded")

    def run(self) -> Iterator[IngestRecord]:
        """Yield records across all pages. Persists cursor on every page."""
        cursor = self._load_cursor()
        page_count = 0
        while True:
            items, next_cursor = self._fetch_with_retries(cursor)
            for item in items:
                yield self.to_record(item)
            page_count += 1
            cursor = next_cursor
            self._save_cursor(cursor)
            if cursor is None:
                break
            if self.max_pages is not None and page_count >= self.max_pages:
                break


def respect_retry_after(response: httpx.Response) -> float | None:
    """Read the Retry-After header if present; return seconds to wait."""
    raw = response.headers.get("Retry-After")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None
