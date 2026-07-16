"""
Idempotency-key store. Insert-and-check pattern: handlers attempt to
insert the key first; if it already exists, skip. Postgres unique
constraint does the heavy lifting.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator


class IdempotencyStore:
    """
    Wraps an idempotency_keys table:

        CREATE TABLE idempotency_keys (
            key TEXT PRIMARY KEY,
            scope TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb
        );

    Use one store per logical scope (e.g., 'stripe_webhook', 'newsapi_pull').
    """

    def __init__(self, conn, scope: str):
        self.conn = conn
        self.scope = scope

    def claim(self, key: str, metadata: dict | None = None) -> bool:
        """
        Try to claim the key. Returns True if newly inserted (proceed),
        False if already present (skip).
        """
        import json
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO idempotency_keys (key, scope, metadata)
                VALUES (%s, %s, %s::jsonb)
                ON CONFLICT (key) DO NOTHING
                RETURNING key
                """,
                (key, self.scope, json.dumps(metadata or {})),
            )
            row = cur.fetchone()
            self.conn.commit()
            return row is not None
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    @contextmanager
    def guard(self, key: str, metadata: dict | None = None) -> Iterator[bool]:
        """
        Context manager. Yields True if proceed, False if already-seen.
        Caller is responsible for skipping work when False.

        Usage:
            with store.guard(event_id) as proceed:
                if not proceed:
                    return
                do_the_work()
        """
        proceed = self.claim(key, metadata)
        try:
            yield proceed
        except Exception:
            # Note: we do NOT roll back the idempotency claim on failure.
            # If the work fails after claiming, retry must use a different
            # mechanism (queue + dead-letter, not key reuse), or we lose
            # the at-least-once guarantee. This matches Stripe's webhook
            # design.
            raise
