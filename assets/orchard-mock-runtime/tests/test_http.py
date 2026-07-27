"""HTTP surface: three routes, deterministic bytes, explicit rejections.

Gate 4 lives here. The golden files under fixtures/golden/ pin the exact
response bytes and SSE event boundaries; if any byte moves, these tests
say so before a learner's saved evidence quietly stops matching the
course. Regenerate goldens ONLY after an intentional protocol or fixture
change: python3 scripts/make_goldens.py

    python3 -m unittest discover -s tests -v
"""

import json
import re
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import support
from support import Serve, pull

GOLDEN = support.ROOT / "fixtures" / "golden"
MODEL = "orchard-3b-instruct"
CANARY = "orchard-3b-instruct-canary"
RUN_ID = "golden-001"
PREFIX = "[COURSE MOCK, NOT MODEL OUTPUT]"

DOC_REQUEST = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "Summarize the weekly status."}],
    "max_tokens": 64,
}

_tmp = None
_serve = None


def setUpModule():
    global _tmp, _serve
    _tmp = tempfile.TemporaryDirectory()
    state = Path(_tmp.name) / ".orchard-runtime"
    pull(state)
    pull(state, CANARY)
    _serve = Serve(state, RUN_ID, load_delay_ms=0, ttft_ms=0,
                   tokens_per_second=0).start()
    _serve.wait_for_status("ready")


def tearDownModule():
    if _serve:
        _serve.stop()
    if _tmp:
        _tmp.cleanup()


def url(path):
    return f"http://127.0.0.1:{_serve.port}{path}"


def get(path):
    with urllib.request.urlopen(url(path), timeout=10) as response:
        return response.status, response.headers, response.read()


def post(payload, raw=None):
    request = urllib.request.Request(
        url("/v1/chat/completions"), method="POST",
        data=raw if raw is not None else json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, response.headers, response.read()


def golden(name):
    path = GOLDEN / name
    if not path.exists():
        raise AssertionError(
            f"missing golden fixtures/golden/{name}; generate it with "
            "python3 scripts/make_goldens.py")
    return path.read_bytes()


class GoldenBytes(unittest.TestCase):
    def test_models_list_matches_golden(self):
        status, headers, body = get("/v1/models")
        self.assertEqual(status, 200)
        self.assertEqual(body, golden("models-list.json"))
        self.assertEqual(headers["X-Mock-Runtime"], "orchard")

    def test_completion_matches_golden(self):
        status, headers, body = post(DOC_REQUEST)
        self.assertEqual(status, 200)
        self.assertEqual(body, golden("chat-completion.json"))
        self.assertEqual(headers["X-Mock-Runtime"], "orchard")

    def test_stream_matches_golden(self):
        status, _, body = post(dict(DOC_REQUEST, stream=True))
        self.assertEqual(status, 200)
        self.assertEqual(body, golden("chat-completion.sse"))

    def test_goldens_hold_no_pid_or_observed_values(self):
        """Only configured values belong in golden files. A PID or an
        observed timing in a golden would make determinism a lie."""
        for name in ("models-list.json", "chat-completion.json",
                     "chat-completion.sse"):
            data = golden(name)
            self.assertNotIn(b'"pid"', data, name)
            self.assertNotIn(b"observed_", data, name)


class ResponseContract(unittest.TestCase):
    def test_key_order_is_fixed(self):
        _, _, body = post(DOC_REQUEST)
        payload = json.loads(body)
        self.assertEqual(list(payload),
                         ["id", "object", "created", "model", "choices",
                          "usage", "mock"])

    def test_created_is_zero_and_request_id_shape(self):
        _, _, body = post(DOC_REQUEST)
        payload = json.loads(body)
        self.assertEqual(payload["created"], 0)
        self.assertRegex(payload["id"], r"^mockreq_[0-9a-f]{12}$")

    def test_same_request_produces_identical_bytes(self):
        _, _, first = post(DOC_REQUEST)
        _, _, second = post(DOC_REQUEST)
        self.assertEqual(first, second)

    def test_usage_counts_whitespace_words_and_says_so(self):
        _, _, body = post(DOC_REQUEST)
        payload = json.loads(body)
        self.assertEqual(payload["usage"],
                         {"prompt_tokens": 4, "completion_tokens": 7,
                          "total_tokens": 11})
        self.assertEqual(payload["mock"]["usage_unit"], "whitespace_words")
        self.assertFalse(payload["mock"]["thinking"])

    def test_content_always_carries_the_mock_prefix(self):
        _, _, body = post(DOC_REQUEST)
        content = json.loads(body)["choices"][0]["message"]["content"]
        self.assertTrue(content.startswith(PREFIX), content)

    def test_max_tokens_truncation_reports_length(self):
        _, _, body = post(dict(DOC_REQUEST, max_tokens=3))
        choice = json.loads(body)["choices"][0]
        self.assertEqual(choice["finish_reason"], "length")
        self.assertEqual(len(choice["message"]["content"].split()), 3)


class StreamContract(unittest.TestCase):
    def parse(self, body):
        blocks = body.decode().split("\n\n")
        self.assertEqual(blocks[-1], "", "stream must end with a blank line")
        lines = blocks[:-1]
        self.assertTrue(all(line.startswith("data: ") for line in lines))
        return [line[len("data: "):] for line in lines]

    def test_deltas_reassemble_to_the_exact_content(self):
        _, _, plain = post(DOC_REQUEST)
        content = json.loads(plain)["choices"][0]["message"]["content"]
        _, _, body = post(dict(DOC_REQUEST, stream=True))
        events = self.parse(body)

        self.assertEqual(events[-1], "[DONE]")
        chunks = [json.loads(event) for event in events[:-1]]
        deltas = [c["choices"][0]["delta"].get("content")
                  for c in chunks[:-1]]
        self.assertTrue(all(deltas), "every content event carries text")
        self.assertEqual("".join(deltas), content)
        self.assertEqual(deltas, re.findall(r"\S+\s*", content),
                         "event boundaries are deterministic word chunks")

        final = chunks[-1]
        self.assertEqual(final["choices"][0]["finish_reason"], "stop")
        self.assertEqual(final["usage"]["total_tokens"], 11)
        self.assertEqual(final["mock"]["usage_unit"], "whitespace_words")

    def test_one_request_id_across_the_whole_stream(self):
        _, headers, body = post(dict(DOC_REQUEST, stream=True))
        events = self.parse(body)
        ids = {json.loads(event)["id"] for event in events[:-1]}
        self.assertEqual(len(ids), 1)
        self.assertEqual(ids.pop(), headers["X-Request-Id"])


class ErrorPaths(unittest.TestCase):
    def expect_error(self, status, error_type, payload=None, raw=None,
                     path="/v1/chat/completions", method="POST"):
        request = urllib.request.Request(
            url(path), method=method,
            data=(raw if raw is not None
                  else json.dumps(payload).encode()) if method == "POST"
            else None,
            headers={"Content-Type": "application/json"})
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(request, timeout=10)
        err = ctx.exception
        self.assertEqual(err.code, status)
        body = json.load(err)
        self.assertEqual(body["error"]["type"], error_type, body)
        self.assertTrue(body["mock"])
        self.assertIn("mock", body["error"]["message"].lower())
        return body

    def request_with(self, **overrides):
        payload = dict(DOC_REQUEST)
        payload.update(overrides)
        return payload

    def test_unknown_paths_are_404_on_both_verbs(self):
        self.expect_error(404, "not_found", path="/v1/echo", method="GET")
        self.expect_error(404, "not_found", path="/v1/stream", method="POST",
                          payload={})

    def test_non_json_body_is_invalid_request(self):
        self.expect_error(400, "invalid_request", raw=b"{not json")

    def test_tools_and_response_format_are_unsupported_features(self):
        self.expect_error(400, "unsupported_feature",
                          self.request_with(tools=[{"type": "function"}]))
        self.expect_error(400, "unsupported_feature",
                          self.request_with(response_format={"type": "json"}))

    def test_non_text_content_is_an_unsupported_feature(self):
        payload = self.request_with(messages=[
            {"role": "user",
             "content": [{"type": "image_url", "image_url": {"url": "x"}}]}])
        self.expect_error(400, "unsupported_feature", payload)

    def test_unknown_model_is_404_and_names_the_loaded_one(self):
        body = self.expect_error(404, "not_found",
                                 self.request_with(model=CANARY))
        self.assertIn(MODEL, body["error"]["message"])

    def test_empty_or_malformed_messages_are_invalid(self):
        self.expect_error(400, "invalid_request",
                          self.request_with(messages=[]))
        self.expect_error(400, "invalid_request",
                          self.request_with(messages=[{"role": "user"}]))

    def test_max_tokens_must_be_a_positive_integer(self):
        self.expect_error(400, "invalid_request",
                          self.request_with(max_tokens=0))

    def test_fixture_word_limit_is_never_called_a_context_window(self):
        long_prompt = "word " * 513
        body = self.expect_error(
            400, "fixture_context_limit",
            self.request_with(messages=[{"role": "user",
                                         "content": long_prompt}]))
        self.assertIn("not a validated model context window",
                      body["error"]["message"])


if __name__ == "__main__":
    unittest.main()
