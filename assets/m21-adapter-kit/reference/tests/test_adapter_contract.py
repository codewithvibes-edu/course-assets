"""THE contract suite. Every adapter passes every applicable test here
before any route may select it; that sentence is the module.

The whole suite runs offline. The lab adapter's network is replaced by
doubles through its opener seam, so success, failure, and malformed
shapes all cost nothing and finish in milliseconds. The live side-by-side
proof is a separate exercise (app_swap_demo.py); contract truth and live
demonstration are different jobs.

Run from reference/:  python3 -m unittest discover -s tests -v
"""

import io
import json
import socket
import sys
import unittest
import urllib.error
from email.message import Message
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adapter_lab import LabAdapter
from adapter_mock import MockAdapter
from canonical import (
    AdapterError, CanonicalRequest, CanonicalResponse, MediaRef,
    Message as Msg, StreamEvent,
)

SECRET = "test-secret-key-abc123"


def request(text="Summarize the weekly status.", media=None):
    return CanonicalRequest(messages=[Msg("user", text)], media=media or [])


# ---- doubles for the lab adapter's opener seam ------------------------------

def http_error(status, body, headers=None):
    msg = Message()
    for key, value in (headers or {}).items():
        msg[key] = value
    return urllib.error.HTTPError("http://double.invalid", status, "err", msg,
                                  io.BytesIO(json.dumps(body).encode()))


class FakeEchoResponse:
    def __init__(self, body, request_id="req_double"):
        self.headers = Message()
        self.headers["X-Request-Id"] = request_id
        self._data = json.dumps(body).encode()

    def read(self, *args):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeStreamResponse:
    def __init__(self, lines, request_id="req_double"):
        self.headers = Message()
        self.headers["X-Request-Id"] = request_id
        self._lines = [line.encode() for line in lines]

    def __iter__(self):
        return iter(self._lines)


def lab_with(response_or_exc):
    def opener(req, timeout=None):
        if isinstance(response_or_exc, Exception):
            raise response_or_exc
        return response_or_exc
    return LabAdapter("http://double.invalid", SECRET, "mock-1", opener=opener)


GOOD_ECHO = {"output": "the echo", "usage": {"input_tokens": 4, "output_tokens": 2}}
GOOD_STREAM = [
    'data: {"delta": "all "}',
    'data: {"delta": "good"}',
    'data: {"done": true, "usage": {"output_tokens": 2}}',
]


def adapters_for_generate():
    """(name, factory) pairs that produce a working generate() path."""
    return [
        ("mock", lambda: MockAdapter()),
        ("lab", lambda: lab_with(FakeEchoResponse(GOOD_ECHO))),
    ]


def adapters_for_stream():
    return [
        ("mock", lambda: MockAdapter()),
        ("lab", lambda: lab_with(FakeStreamResponse(GOOD_STREAM))),
    ]


# ---- the contract ------------------------------------------------------------

class CanonicalShape(unittest.TestCase):
    def test_generate_returns_only_canonical_fields(self):
        for name, factory in adapters_for_generate():
            with self.subTest(adapter=name):
                response = factory().generate(request())
                self.assertIsInstance(response, CanonicalResponse)
                self.assertIsInstance(response.content, str)
                self.assertIn(response.finish_reason,
                              ("complete", "length", "canceled"))
                self.assertGreaterEqual(response.usage.output_tokens, 0)
                self.assertGreaterEqual(response.latency_s, 0)
                self.assertTrue(response.request_id)

    def test_stream_is_typed_events_ending_in_done_with_usage(self):
        for name, factory in adapters_for_stream():
            with self.subTest(adapter=name):
                events = list(factory().stream(request()))
                self.assertTrue(all(isinstance(e, StreamEvent) for e in events))
                self.assertTrue(all(e.kind == "delta" for e in events[:-1]))
                done = events[-1]
                self.assertEqual(done.kind, "done")
                self.assertIsNotNone(done.usage)
                self.assertTrue(done.request_id)

    def test_deterministic_adapter_is_actually_deterministic(self):
        first = MockAdapter().generate(request())
        second = MockAdapter().generate(request())
        self.assertEqual(first.content, second.content)


class NormalizedFailures(unittest.TestCase):
    def test_invalid_access(self):
        adapter = lab_with(http_error(401, {"error": {"message": "bad key"}}))
        with self.assertRaises(AdapterError) as ctx:
            adapter.generate(request())
        self.assertEqual(ctx.exception.category, "auth")

    def test_limit_response_keeps_retry_hint(self):
        adapter = lab_with(http_error(
            429, {"error": {"message": "slow down"}}, {"Retry-After": "12"}))
        with self.assertRaises(AdapterError) as ctx:
            adapter.generate(request())
        self.assertEqual(ctx.exception.category, "rate_limit")
        self.assertEqual(ctx.exception.retry_after, 12.0)

    def test_timeout(self):
        adapter = lab_with(socket.timeout())
        with self.assertRaises(AdapterError) as ctx:
            adapter.generate(request())
        self.assertEqual(ctx.exception.category, "timeout")

    def test_malformed_provider_payload(self):
        broken = FakeStreamResponse(['data: {this is not json}'])
        with self.assertRaises(AdapterError) as ctx:
            list(lab_with(broken).stream(request()))
        self.assertEqual(ctx.exception.category, "malformed")

    def test_partial_stream_is_an_error_not_a_short_success(self):
        partial = FakeStreamResponse(['data: {"delta": "half"}'])
        with self.assertRaises(AdapterError) as ctx:
            list(lab_with(partial).stream(request()))
        self.assertEqual(ctx.exception.category, "malformed")
        self.assertIn("partial", str(ctx.exception))

    def test_request_id_survives_normalization(self):
        adapter = lab_with(http_error(
            500, {"error": {"message": "boom"}}, {"X-Request-Id": "req_evidence"}))
        with self.assertRaises(AdapterError) as ctx:
            adapter.generate(request())
        self.assertEqual(ctx.exception.category, "server")
        self.assertEqual(ctx.exception.request_id, "req_evidence")


class SecretsAndCapabilities(unittest.TestCase):
    def test_secret_never_appears_in_debug_or_messages(self):
        body = {"error": {"message": f"denied for key {SECRET}"}}
        adapter = lab_with(http_error(401, body))
        with self.assertRaises(AdapterError) as ctx:
            adapter.generate(request())
        self.assertNotIn(SECRET, ctx.exception.raw_debug)

    def test_capability_truthfulness_streaming(self):
        for name, factory in adapters_for_stream():
            with self.subTest(adapter=name):
                adapter = factory()
                self.assertTrue(adapter.capabilities().streaming)
                self.assertEqual(list(adapter.stream(request()))[-1].kind, "done")

    def test_unsupported_feature_is_explicit(self):
        media = [MediaRef(media_type="image/png", data_b64="aGk=")]
        for name, factory in adapters_for_generate():
            with self.subTest(adapter=name):
                adapter = factory()
                self.assertFalse(adapter.capabilities().image_input)
                with self.assertRaises(AdapterError) as ctx:
                    adapter.generate(request(media=media))
                self.assertEqual(ctx.exception.category, "unsupported")

    def test_cancellation_closes_cleanly(self):
        for name, factory in adapters_for_stream():
            with self.subTest(adapter=name):
                stream = factory().stream(request())
                first = next(stream)
                self.assertEqual(first.kind, "delta")
                stream.close()   # the application walked away; no exception


if __name__ == "__main__":
    unittest.main()
