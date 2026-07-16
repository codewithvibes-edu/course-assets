"""
Postgres-as-queue. The standard "FOR UPDATE SKIP LOCKED" pattern.
Don't reach for Kafka or RabbitMQ until your volume actually demands it.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any


@dataclass
class QueueItem:
    id: str
    queue: str
    payload: dict[str, Any]
    attempts: int
    created_at: str


class QueueClient:
    """
    Wraps a queue table:

        CREATE TABLE queue (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            queue TEXT NOT NULL,
            payload JSONB NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0,
            visible_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMPTZ,
            last_error TEXT
        );

    plus a dead_letter table with the same shape (less status).
    """

    def __init__(self, conn, default_visibility_seconds: int = 60):
        self.conn = conn
        self.default_visibility_seconds = default_visibility_seconds

    def enqueue(self, queue: str, payload: dict[str, Any]) -> str:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO queue (queue, payload)
                VALUES (%s, %s::jsonb)
                RETURNING id
                """,
                (queue, json.dumps(payload, default=str)),
            )
            (item_id,) = cur.fetchone()
            self.conn.commit()
            return str(item_id)
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def claim_one(
        self,
        queue: str,
        visibility_seconds: int | None = None,
    ) -> QueueItem | None:
        """
        Claim a single pending item. Returns None if nothing is ready.
        Sets visible_at = now() + visibility_seconds so a crashed worker's
        item becomes available again after the timeout.
        """
        v = visibility_seconds or self.default_visibility_seconds
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                WITH claim AS (
                    SELECT id FROM queue
                    WHERE queue = %s
                      AND status = 'pending'
                      AND visible_at <= NOW()
                    ORDER BY created_at
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE queue q
                SET status = 'in_flight',
                    attempts = attempts + 1,
                    visible_at = NOW() + (%s || ' seconds')::interval
                FROM claim
                WHERE q.id = claim.id
                RETURNING q.id, q.queue, q.payload, q.attempts, q.created_at
                """,
                (queue, str(v)),
            )
            row = cur.fetchone()
            self.conn.commit()
            if not row:
                return None
            item_id, q_name, payload, attempts, created_at = row
            return QueueItem(
                id=str(item_id),
                queue=q_name,
                payload=payload if isinstance(payload, dict) else json.loads(payload),
                attempts=attempts,
                created_at=created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
            )
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def ack(self, item_id: str) -> None:
        """Mark item completed."""
        cur = self.conn.cursor()
        try:
            cur.execute(
                "UPDATE queue SET status = 'done', completed_at = NOW() WHERE id = %s",
                (item_id,),
            )
            self.conn.commit()
        finally:
            cur.close()

    def nack(self, item_id: str, error: str, max_attempts: int = 5) -> None:
        """
        Mark item failed. If attempts < max, return to pending after a
        backoff. If attempts >= max, route to dead_letter.
        """
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT attempts, queue, payload FROM queue WHERE id = %s", (item_id,))
            row = cur.fetchone()
            if row is None:
                self.conn.commit()
                return
            attempts, queue_name, payload = row
            if attempts >= max_attempts:
                cur.execute(
                    """
                    INSERT INTO dead_letter (queue, payload, attempts, last_error)
                    VALUES (%s, %s::jsonb, %s, %s)
                    """,
                    (queue_name, json.dumps(payload, default=str), attempts, error[:1000]),
                )
                cur.execute(
                    "UPDATE queue SET status = 'dead', last_error = %s WHERE id = %s",
                    (error[:1000], item_id),
                )
            else:
                # Exponential backoff before next retry attempt.
                backoff = 2**attempts
                cur.execute(
                    """
                    UPDATE queue
                    SET status = 'pending',
                        last_error = %s,
                        visible_at = NOW() + (%s || ' seconds')::interval
                    WHERE id = %s
                    """,
                    (error[:1000], str(backoff), item_id),
                )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()
