"""Contract tests. Every failure here is a test double: no network, no
credits, no waiting for a real provider to have a bad day. The doubles
exist because client.py exposes an `opener` seam; that seam is the whole
reason these tests are free.

Run from the scaffold root:  python3 -m unittest discover -s tests -v
"""

import io
import json
import socket
import sys
import tempfile
import unittest
import urllib.error
from email.message import Message
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import client
import state
import usage_log

FIXTURES = Path(__file__).parent.parent / "fixtures"


def http_error(status, body, headers=None):
    msg = Message()
    for key, value in (headers or {}).items():
        msg[key] = value
    return urllib.error.HTTPError(
        "http://double.invalid/v1/stream", status, "err", msg,
        io.BytesIO(json.dumps(body).encode()),
    )


class FakeStreamResponse:
    """Stands in for urlopen's response: headers plus iterable byte lines."""

    def __init__(self, lines, request_id="req_test_double"):
        self.headers = Message()
        self.headers["X-Request-Id"] = request_id
        self._lines = [line.encode() for line in lines]

    def __iter__(self):
        return iter(self._lines)


def opener_returning(response):
    def opener(request, timeout=None):
        return response
    return opener


def opener_raising(exc):
    def opener(request, timeout=None):
        raise exc
    return opener


def drain(gen):
    return list(gen)


class ClientFailureDoubles(unittest.TestCase):
    def call(self, opener):
        return drain(client.stream_generate(
            "http://double.invalid", "k", "m", "text", 5, opener=opener))

    def test_invalid_credential(self):
        exc = http_error(401, {"error": {"type": "authentication_error",
                                         "message": "Invalid or missing API key."}})
        with self.assertRaises(client.ClientError) as ctx:
            self.call(opener_raising(exc))
        self.assertEqual(ctx.exception.kind, "auth")

    def test_rate_limit_carries_retry_after(self):
        exc = http_error(429, {"error": {"type": "rate_limit_error",
                                         "message": "Too many requests."}},
                         headers={"Retry-After": "12"})
        with self.assertRaises(client.ClientError) as ctx:
            self.call(opener_raising(exc))
        self.assertEqual(ctx.exception.kind, "rate_limit")
        self.assertEqual(ctx.exception.retry_after, 12.0)

    def test_timeout(self):
        with self.assertRaises(client.ClientError) as ctx:
            self.call(opener_raising(socket.timeout()))
        self.assertEqual(ctx.exception.kind, "timeout")

    def test_malformed_event(self):
        broken = (FIXTURES / "malformed-stream-event.txt").read_text().splitlines()
        with self.assertRaises(client.ClientError) as ctx:
            self.call(opener_returning(FakeStreamResponse(broken)))
        self.assertEqual(ctx.exception.kind, "malformed")

    def test_stream_without_done_is_partial_not_complete(self):
        lines = ['data: {"delta": "half an "}', 'data: {"delta": "answer"}']
        with self.assertRaises(client.ClientError) as ctx:
            self.call(opener_returning(FakeStreamResponse(lines)))
        self.assertEqual(ctx.exception.kind, "malformed")
        self.assertIn("partial", str(ctx.exception))

    def test_happy_path_deltas_then_done(self):
        lines = [
            'data: {"delta": "all "}',
            'data: {"delta": "good"}',
            'data: {"done": true, "usage": {"output_tokens": 2}}',
        ]
        events = self.call(opener_returning(FakeStreamResponse(lines)))
        self.assertEqual(events[0], ("delta", "all "))
        self.assertEqual(events[-1][0], "done")
        self.assertEqual(events[-1][1], {"output_tokens": 2})
        self.assertEqual(events[-1][2], "req_test_double")


class BoundedStateContract(unittest.TestCase):
    def test_bound_holds_and_drops_are_counted(self):
        history = state.BoundedHistory(max_turns=3)
        for n in range(5):
            history.add("user", f"turn {n}")
        self.assertEqual(len(history), 3)
        self.assertEqual(history.dropped, 2)
        sent = history.to_payload()
        self.assertEqual([t["content"] for t in sent],
                         ["turn 2", "turn 3", "turn 4"])


class UsageLogPrivacyContract(unittest.TestCase):
    def test_log_records_facts_never_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry = usage_log.record(
                route="summarize", model="mock-1", latency_s=1.234,
                usage={"input_tokens": 9, "output_tokens": 4},
                request_id="req_x", outcome="ok", log_dir=tmp,
            )
            self.assertEqual(
                sorted(entry.keys()),
                sorted(["ts", "route", "model", "latency_s", "usage",
                        "estimated_cost", "request_id", "outcome"]))
            written = (Path(tmp) / "usage.jsonl").read_text()
            for banned in ("content", "prompt", "input\":", "output\":"):
                self.assertNotIn(banned, written)


if __name__ == "__main__":
    unittest.main()
