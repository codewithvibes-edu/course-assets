"""
Generic worker. Drains a queue, calls a handler per item, ack/nack
based on the handler's success or failure.
"""

from __future__ import annotations

import time
import traceback
from dataclasses import dataclass
from typing import Callable

from .queue import QueueClient, QueueItem


@dataclass
class Worker:
    queue_client: QueueClient
    queue_name: str
    handler: Callable[[QueueItem], None]
    poll_interval_seconds: float = 1.0
    max_attempts: int = 5
    visibility_seconds: int = 60

    def run_once(self) -> bool:
        """
        Process at most one item. Returns True if an item was processed,
        False if the queue was empty.
        """
        item = self.queue_client.claim_one(
            self.queue_name, visibility_seconds=self.visibility_seconds
        )
        if item is None:
            return False
        try:
            self.handler(item)
            self.queue_client.ack(item.id)
        except Exception:
            error_msg = traceback.format_exc()
            self.queue_client.nack(item.id, error_msg, max_attempts=self.max_attempts)
        return True

    def run_forever(self, stop_signal: Callable[[], bool] | None = None) -> None:
        """
        Drain the queue indefinitely. Polls every `poll_interval_seconds`
        when the queue is empty. Honors the stop_signal callback if provided.
        """
        while True:
            if stop_signal and stop_signal():
                break
            processed = self.run_once()
            if not processed:
                time.sleep(self.poll_interval_seconds)
