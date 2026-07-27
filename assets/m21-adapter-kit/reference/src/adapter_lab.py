"""Adapter for the course lab service (the Module 19 mock protocol).

This file is the translation zone: lab-protocol shapes come in, canonical
shapes go out, and nothing lab-shaped leaks past it. Reading it next to
adapter_mock.py shows the deal every adapter signs: same interface, same
contract suite, wildly different insides.
"""

import json
import socket
import time
import urllib.error
import urllib.request

from canonical import (
    AdapterError, CanonicalResponse, Capabilities, StreamEvent, Usage, redact,
)


class LabAdapter:
    """test(), generate(), stream(), capabilities(): the whole protocol."""

    def __init__(self, base_url, api_key, model, opener=None):
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.model = model
        self._open = opener or urllib.request.urlopen

    # ---- protocol -----------------------------------------------------

    def capabilities(self):
        return Capabilities(
            text=True, streaming=True, structured_output=False,
            tools=False, image_input=False, last_tested="2026-07-24",
        )

    def test(self):
        """One cheap call that proves address + credential together."""
        self.generate_payload({"model": self.model, "input": "ping"}, timeout_s=5)
        return True

    def generate(self, request):
        started = time.monotonic()
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content}
                         for m in request.messages],
        }
        if request.media:
            raise AdapterError(
                "unsupported",
                "This connection declares image_input=False; the request "
                "carries media. Route it to a connection whose capabilities "
                "include image input.",
            )
        body, request_id = self.generate_payload(payload, request.timeout_s)
        return CanonicalResponse(
            content=body.get("output", ""),
            finish_reason="complete",
            usage=Usage(**body.get("usage", {})),
            latency_s=time.monotonic() - started,
            request_id=request_id or "lab-unknown",
            raw_debug=redact(json.dumps(body)[:500], [self._api_key]),
        )

    def stream(self, request):
        if request.media:
            raise AdapterError("unsupported", "image_input is False for this connection.")
        req = self._build("/v1/stream", {
            "model": self.model,
            "input": " ".join(m.content for m in request.messages),
        })
        try:
            response = self._open(req, timeout=request.timeout_s)
        except Exception as err:              # normalized below, one place
            raise self._normalize(err) from None

        request_id = response.headers.get("X-Request-Id", "lab-unknown")
        saw_done = False
        try:
            for raw in response:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data: "):
                    continue
                try:
                    event = json.loads(line[len("data: "):])
                except json.JSONDecodeError:
                    raise AdapterError(
                        "malformed", "Provider sent a non-JSON stream event.",
                        request_id=request_id,
                        raw_debug=redact(line[:200], [self._api_key]))
                if event.get("done"):
                    saw_done = True
                    yield StreamEvent(kind="done",
                                      usage=Usage(**event.get("usage", {})),
                                      request_id=request_id)
                    break
                if "delta" in event:
                    yield StreamEvent(kind="delta", text=event["delta"])
        except socket.timeout:
            raise AdapterError("timeout", "Stream stalled past its budget.",
                               request_id=request_id) from None
        except GeneratorExit:
            # The application canceled us. Clean close, no exception out.
            return
        if not saw_done:
            raise AdapterError("malformed",
                               "Stream ended before its done event; output is partial.",
                               request_id=request_id)

    # ---- lab-protocol plumbing ------------------------------------------

    def _build(self, path, payload):
        return urllib.request.Request(
            self.base_url + path,
            method="POST",
            headers={"Authorization": f"Bearer {self._api_key}",
                     "Content-Type": "application/json"},
            data=json.dumps(payload).encode(),
        )

    def generate_payload(self, payload, timeout_s):
        req = self._build("/v1/echo", payload)
        try:
            with self._open(req, timeout=timeout_s) as response:
                return json.load(response), response.headers.get("X-Request-Id")
        except Exception as err:
            raise self._normalize(err) from None

    def _normalize(self, err):
        """Every provider failure becomes one canonical category, with the
        raw evidence kept, redacted, instead of erased."""
        if isinstance(err, AdapterError):
            return err
        if isinstance(err, urllib.error.HTTPError):
            request_id = err.headers.get("X-Request-Id")
            try:
                body = json.load(err)
                message = body.get("error", {}).get("message", f"HTTP {err.code}")
                debug = redact(json.dumps(body)[:500], [self._api_key])
            except json.JSONDecodeError:
                return AdapterError("malformed", f"HTTP {err.code} with a non-JSON body.",
                                    request_id=request_id)
            if err.code == 401:
                return AdapterError("auth", message, request_id=request_id, raw_debug=debug)
            if err.code == 429:
                retry_after = err.headers.get("Retry-After")
                return AdapterError("rate_limit", message,
                                    retry_after=float(retry_after) if retry_after else None,
                                    request_id=request_id, raw_debug=debug)
            if err.code == 404:
                return AdapterError("not_found", message, request_id=request_id, raw_debug=debug)
            if 400 <= err.code < 500:
                return AdapterError("bad_input", message, request_id=request_id, raw_debug=debug)
            return AdapterError("server", message, request_id=request_id, raw_debug=debug)
        if isinstance(err, socket.timeout):
            return AdapterError("timeout", "No response within the budget.")
        if isinstance(err, urllib.error.URLError):
            reason = getattr(err, "reason", err)
            if isinstance(reason, socket.timeout):
                return AdapterError("timeout", "No response within the budget.")
            return AdapterError("network", f"Could not reach {self.base_url}: {reason}")
        return AdapterError("server", f"Unexpected failure: {err!r}",
                            raw_debug=redact(repr(err), [self._api_key]))
