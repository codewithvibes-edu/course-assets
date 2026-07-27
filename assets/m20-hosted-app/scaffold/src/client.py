"""The ONLY file that talks to the provider. Everything provider-shaped
lives here on purpose: when Module 21 builds the adapter, this file is the
coupling you will measure and move. If you find yourself importing urllib
anywhere else in src/, stop and come back here.

Speaks the course lab protocol (the Module 19 mock service). Pointing it
at a real provider means changing THIS file per a dated recipe, and the
mild pain of doing that is a lesson with a module number: 21.
"""

import json
import socket
import urllib.error
import urllib.request


class ClientError(Exception):
    """One normalized failure, so the app never parses provider errors."""

    def __init__(self, kind, message, retry_after=None, request_id=None):
        super().__init__(message)
        self.kind = kind          # auth | rate_limit | bad_input | server | timeout | network | malformed
        self.retry_after = retry_after
        self.request_id = request_id


def _classify(status, body, headers):
    error = (body or {}).get("error", {})
    message = error.get("message", f"HTTP {status}")
    request_id = headers.get("X-Request-Id")
    if status == 401:
        return ClientError("auth", message, request_id=request_id)
    if status == 429:
        retry_after = headers.get("Retry-After")
        return ClientError("rate_limit", message,
                           retry_after=float(retry_after) if retry_after else None,
                           request_id=request_id)
    if 400 <= status < 500:
        return ClientError("bad_input", message, request_id=request_id)
    return ClientError("server", message, request_id=request_id)


def stream_generate(base_url, api_key, model, text, timeout_s, opener=None):
    """Yield ("delta", str) events as they arrive, then one ("done", usage
    dict, request_id) event. Raises ClientError for every failure shape.

    `opener` exists so tests can inject a double; leave it None to use the
    network. That injection seam is what makes the failure tests free.
    """
    open_fn = opener or urllib.request.urlopen
    request = urllib.request.Request(
        base_url.rstrip("/") + "/v1/stream",
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps({"model": model, "input": text}).encode(),
    )
    try:
        response = open_fn(request, timeout=timeout_s)
    except urllib.error.HTTPError as err:
        try:
            body = json.load(err)
        except json.JSONDecodeError:
            body = None
        raise _classify(err.code, body, err.headers) from None
    except socket.timeout:
        raise ClientError("timeout", f"No response within {timeout_s}s.") from None
    except urllib.error.URLError as err:
        reason = getattr(err, "reason", err)
        if isinstance(reason, socket.timeout):
            raise ClientError("timeout", f"No response within {timeout_s}s.") from None
        raise ClientError("network", f"Could not reach {base_url}: {reason}") from None

    request_id = response.headers.get("X-Request-Id")
    saw_done = False
    try:
        for raw in response:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data: "):
                continue
            try:
                event = json.loads(line[len("data: "):])
            except json.JSONDecodeError:
                raise ClientError("malformed",
                                  f"Provider sent an event that is not valid JSON: {line[:80]}",
                                  request_id=request_id) from None
            if event.get("done"):
                saw_done = True
                yield ("done", event.get("usage", {}), request_id)
                break
            if "delta" in event:
                yield ("delta", event["delta"])
    except socket.timeout:
        raise ClientError("timeout",
                          f"Stream stalled past the {timeout_s}s budget.",
                          request_id=request_id) from None
    if not saw_done:
        # The stream ended without the done event: an incomplete answer,
        # never a short complete one. The app must not pretend otherwise.
        raise ClientError("malformed",
                          "Stream ended before the done event; output is partial.",
                          request_id=request_id)


def echo_request(base_url, api_key, payload, timeout_s, opener=None):
    """One non-streamed request; returns (parsed body, request_id).
    Used by the chat loop to show exactly what state was sent."""
    open_fn = opener or urllib.request.urlopen
    request = urllib.request.Request(
        base_url.rstrip("/") + "/v1/echo",
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload).encode(),
    )
    try:
        with open_fn(request, timeout=timeout_s) as response:
            body = json.load(response)
            return body, response.headers.get("X-Request-Id")
    except urllib.error.HTTPError as err:
        try:
            parsed = json.load(err)
        except json.JSONDecodeError:
            raise ClientError("malformed",
                              f"HTTP {err.code} with a non-JSON body.") from None
        raise _classify(err.code, parsed, err.headers) from None
    except socket.timeout:
        raise ClientError("timeout", f"No response within {timeout_s}s.") from None
    except urllib.error.URLError as err:
        raise ClientError("network", f"Could not reach {base_url}: {err.reason}") from None
    except json.JSONDecodeError:
        raise ClientError("malformed", "Response body is not valid JSON.") from None
