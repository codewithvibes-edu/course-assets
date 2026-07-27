"""LocalProviderAdapter: the Orchard runtime behind the Module 21 boundary.

This file is the whole point of the fallback lane. A learner who cannot run
a real small model still writes a real adapter, against a real out-of-process
HTTP service, and passes the same contract suite everyone else passes.

Two rules govern it:

1. It imports the canonical types from the Module 21 kit. It does not copy
   them, does not extend them, and does not introduce a second set. One
   canonical boundary was the entire architectural argument; a fallback lane
   that quietly forks it would teach the opposite lesson.
2. Nothing Orchard-shaped crosses the boundary. The application never learns
   that its words came from a fixture instead of a model. That is what makes
   the swap in Module 24 a configuration change rather than a rewrite.

What it cannot do is make the fixture real. Every response it normalizes
starts with [COURSE MOCK, NOT MODEL OUTPUT], and the route it serves is
recorded as an exercise-only mock route.
"""

import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _locate_m21_src():
    """Find the Module 21 canonical types. Your own project will have them
    on the path already; this fallback kit ships next to the m21 kit, so it
    looks there, and it says so out loud when it cannot find them."""
    override = os.environ.get("CWV_M21_SRC")
    candidates = [Path(override)] if override else []
    candidates.append(HERE.parent.parent / "m21-adapter-kit" / "reference" / "src")
    for candidate in candidates:
        if (candidate / "canonical.py").exists():
            return candidate
    raise ImportError(
        "Could not find the Module 21 canonical types (canonical.py). This "
        "adapter imports them on purpose instead of redefining them. Point "
        "CWV_M21_SRC at your Module 21 src directory and run this again.")


sys.path.insert(0, str(_locate_m21_src()))

from canonical import (                                        # noqa: E402
    AdapterError, CanonicalResponse, Capabilities, StreamEvent, Usage, redact,
)

# Declared, dated, and truthful. These values are asserted against
# catalog.json in the test suite, so the declaration and the runtime cannot
# drift apart in silence.
CAPABILITIES = Capabilities(
    text=True, streaming=True, structured_output=False,
    tools=False, image_input=False, last_tested="2026-07-24",
)

FINISH_REASONS = {"stop": "complete", "length": "length", "canceled": "canceled"}


class LocalProviderAdapter:
    """test(), generate(), stream(), capabilities(): the same four methods
    every other adapter in this course implements."""

    adapter_id = "local"

    def __init__(self, base_url, model, opener=None):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._open = opener or urllib.request.urlopen
        # There is no credential. The list stays because redaction is a
        # habit, not a feature you add once a secret shows up.
        self._secrets = []

    # ---- protocol ------------------------------------------------------

    def capabilities(self):
        return CAPABILITIES

    def test(self):
        """One cheap call that proves the address and the loaded model
        together. A reachable port serving a different model is a failure
        worth catching before the first real request."""
        request = urllib.request.Request(self.base_url + "/v1/models",
                                         method="GET")
        try:
            with self._open(request, timeout=5) as response:
                body = json.load(response)
        except Exception as err:
            raise self._normalize(err) from None
        served = [entry.get("id") for entry in body.get("data", [])]
        if self.model not in served:
            raise AdapterError(
                "not_found",
                f"The runtime at {self.base_url} does not list '{self.model}'. "
                f"It lists: {', '.join(served) or 'nothing'}. Pull the model "
                "or fix the profile.")
        return True

    def generate(self, request):
        self._refuse_media(request)
        started = time.monotonic()
        body, request_id = self._post({
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content}
                         for m in request.messages],
            "max_tokens": request.max_output_tokens,
            "stream": False,
        }, request.timeout_s)
        choices = body.get("choices") or []
        if not choices:
            raise AdapterError(
                "malformed", "The runtime returned no choices.",
                request_id=request_id,
                raw_debug=redact(json.dumps(body)[:500], self._secrets))
        usage = body.get("usage", {})
        return CanonicalResponse(
            content=choices[0].get("message", {}).get("content", ""),
            finish_reason=FINISH_REASONS.get(choices[0].get("finish_reason"),
                                             "complete"),
            usage=Usage(input_tokens=usage.get("prompt_tokens", 0),
                        output_tokens=usage.get("completion_tokens", 0)),
            latency_s=time.monotonic() - started,
            request_id=body.get("id") or request_id or "local-unknown",
            raw_debug=redact(json.dumps(body)[:500], self._secrets),
        )

    def stream(self, request):
        self._refuse_media(request)
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content}
                         for m in request.messages],
            "max_tokens": request.max_output_tokens,
            "stream": True,
        }
        try:
            response = self._open(self._build(payload), timeout=request.timeout_s)
        except Exception as err:
            raise self._normalize(err) from None

        request_id = response.headers.get("X-Request-Id", "local-unknown")
        saw_done = False
        try:
            for raw in response:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data: "):
                    continue
                data = line[len("data: "):]
                if data == "[DONE]":
                    break
                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    raise AdapterError(
                        "malformed",
                        "The runtime sent a non-JSON stream event.",
                        request_id=request_id,
                        raw_debug=redact(line[:200], self._secrets))
                choice = (event.get("choices") or [{}])[0]
                if choice.get("finish_reason") is not None:
                    saw_done = True
                    usage = event.get("usage", {})
                    yield StreamEvent(
                        kind="done",
                        usage=Usage(
                            input_tokens=usage.get("prompt_tokens", 0),
                            output_tokens=usage.get("completion_tokens", 0)),
                        request_id=request_id)
                    break
                text = choice.get("delta", {}).get("content")
                if text:
                    yield StreamEvent(kind="delta", text=text)
        except socket.timeout:
            raise AdapterError("timeout", "The stream stalled past its budget.",
                               request_id=request_id) from None
        except urllib.error.URLError as err:
            raise self._normalize(err) from None
        except GeneratorExit:
            # The application canceled. Close the socket and leave quietly.
            response.close()
            return
        if not saw_done:
            raise AdapterError(
                "malformed",
                "The stream ended before its final event; output is partial.",
                request_id=request_id)

    # ---- translation zone ------------------------------------------------

    def _refuse_media(self, request):
        if request.media:
            raise AdapterError(
                "unsupported",
                "This connection declares image_input=False and the request "
                "carries media. Route it to a connection whose capabilities "
                "include image input.")

    def _build(self, payload):
        return urllib.request.Request(
            self.base_url + "/v1/chat/completions",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload).encode(),
        )

    def _post(self, payload, timeout_s):
        try:
            with self._open(self._build(payload), timeout=timeout_s) as response:
                return json.load(response), response.headers.get("X-Request-Id")
        except Exception as err:
            raise self._normalize(err) from None

    def _normalize(self, err):
        """Every runtime failure becomes one canonical category. The
        unsupported_feature check runs BEFORE the generic 400 mapping,
        because 'this connection cannot do that' and 'you sent nonsense'
        lead a caller to opposite decisions."""
        if isinstance(err, AdapterError):
            return err
        if isinstance(err, urllib.error.HTTPError):
            request_id = err.headers.get("X-Request-Id")
            try:
                body = json.load(err)
            except (json.JSONDecodeError, ValueError):
                return AdapterError("malformed",
                                    f"HTTP {err.code} with a non-JSON body.",
                                    request_id=request_id)
            error_body = body.get("error", {})
            message = error_body.get("message", f"HTTP {err.code}")
            debug = redact(json.dumps(body)[:500], self._secrets)
            if error_body.get("type") == "unsupported_feature":
                return AdapterError("unsupported", message,
                                    request_id=request_id, raw_debug=debug)
            if err.code == 404:
                return AdapterError("not_found", message,
                                    request_id=request_id, raw_debug=debug)
            if err.code == 401:
                return AdapterError("auth", message,
                                    request_id=request_id, raw_debug=debug)
            if err.code == 429:
                retry_after = err.headers.get("Retry-After")
                return AdapterError("rate_limit", message,
                                    retry_after=float(retry_after) if retry_after else None,
                                    request_id=request_id, raw_debug=debug)
            if 400 <= err.code < 500:
                return AdapterError("bad_input", message,
                                    request_id=request_id, raw_debug=debug)
            return AdapterError("server", message,
                                request_id=request_id, raw_debug=debug)
        if isinstance(err, socket.timeout):
            return AdapterError("timeout", "No response within the budget.")
        if isinstance(err, urllib.error.URLError):
            reason = getattr(err, "reason", err)
            if isinstance(reason, socket.timeout):
                return AdapterError("timeout", "No response within the budget.")
            return AdapterError(
                "network",
                f"Could not reach the local runtime at {self.base_url}: "
                f"{reason}. A stopped service and an unreachable service look "
                "identical from here, which is why the fallback path matters.")
        return AdapterError("server", f"Unexpected failure: {err!r}",
                            raw_debug=redact(repr(err), self._secrets))
