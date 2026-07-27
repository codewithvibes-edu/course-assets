# mock_service.py -- the API lab for Module 19. Runs on your machine, costs nothing.
#
# Start it:   python3 mock_service.py     (Windows: python mock_service.py)
# Stop it:    Ctrl+C in this terminal.
#
# This is the Module 0 mock server's bigger sibling. That one proved the pipe.
# This one teaches the weather: every status class, a streamed response, and
# an endpoint slow enough to force a timeout. Standard library only.
#
# It listens on port 8124 on purpose: the Module 0 mock owns 8123, and both
# can run at once. If 8124 is busy, you know how to diagnose that (m0-11).

import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 8124
MOCK_KEY = "mock-key-local-only"

STREAM_WORDS = (
    "A streamed response arrives as many small events instead of one complete body, "
    "and a partial stream is not a finished answer."
).split()

# The canned failure exhibits for lesson 5. Status, headers, body: the whole
# lesson is reading these like evidence, so each one carries the fields a
# well-behaved service would send.
ERROR_EXHIBITS = {
    "bad-input": (
        400,
        {},
        {
            "error": {
                "type": "invalid_request",
                "message": "Field 'input' must be a string, got number.",
                "param": "input",
            }
        },
    ),
    "auth": (
        401,
        {},
        {
            "error": {
                "type": "authentication_error",
                "message": "Invalid or missing API key.",
            }
        },
    ),
    "forbidden": (
        403,
        {},
        {
            "error": {
                "type": "permission_error",
                "message": "This key is valid but has no access to model 'mock-pro'. "
                "Your credential works; your permissions do not.",
            }
        },
    ),
    "missing": (
        404,
        {},
        {
            "error": {
                "type": "not_found",
                "message": "No such model 'mok-1'. Check the spelling against the model list.",
            }
        },
    ),
    "rate-limit": (
        429,
        {"Retry-After": "12"},
        {
            "error": {
                "type": "rate_limit_error",
                "message": "Too many requests. Retry after 12 seconds. "
                "Your request was fine; your timing was not.",
            }
        },
    ),
    "server": (
        500,
        {},
        {
            "error": {
                "type": "server_error",
                "message": "Internal error. Nothing you sent caused this. "
                "Quote the request ID when you report it.",
            }
        },
    ),
}


class MockService(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    # ---- plumbing -------------------------------------------------------

    def request_id(self):
        if not hasattr(self, "_request_id"):
            self._request_id = "req_" + uuid.uuid4().hex[:12]
        return self._request_id

    def send_json(self, status, payload, extra_headers=None):
        data = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Request-Id", self.request_id())
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        return self.headers.get("Authorization") == f"Bearer {MOCK_KEY}"

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        try:
            return json.loads(raw or b"{}"), None
        except json.JSONDecodeError as err:
            return None, str(err)

    def log_message(self, fmt, *args):
        # One line per request. At this scale, this terminal IS the server log.
        print(f"[mock {self.request_id()}] {self.address_string()} {fmt % args}", flush=True)

    # ---- routes ---------------------------------------------------------

    def do_GET(self):
        if self.path.startswith("/v1/error/"):
            return self.handle_error_exhibit()
        self.send_json(404, {
            "error": {"type": "not_found", "message": f"Unknown path {self.path}."}
        })

    def do_POST(self):
        if self.path.startswith("/v1/error/"):
            return self.handle_error_exhibit()
        if self.path == "/v1/echo":
            return self.handle_echo()
        if self.path == "/v1/stream":
            return self.handle_stream()
        if self.path == "/v1/slow":
            return self.handle_slow()
        self.send_json(404, {
            "error": {"type": "not_found", "message": f"Unknown path {self.path}. "
                      "Try /v1/echo, /v1/stream, /v1/slow, or /v1/error/<kind>."}
        })

    def handle_error_exhibit(self):
        # The exhibits answer regardless of auth: they ARE the lesson.
        kind = self.path.rsplit("/", 1)[-1]
        if kind not in ERROR_EXHIBITS:
            self.send_json(404, {
                "error": {"type": "not_found",
                          "message": f"Unknown exhibit '{kind}'. "
                          f"Kinds: {', '.join(sorted(ERROR_EXHIBITS))}."}
            })
            return
        status, extra, body = ERROR_EXHIBITS[kind]
        self.send_json(status, body, extra_headers=extra)

    def handle_echo(self):
        if not self.authorized():
            self.send_json(401, ERROR_EXHIBITS["auth"][2])
            return
        body, parse_error = self.read_body()
        if parse_error is not None:
            self.send_json(400, {
                "error": {"type": "invalid_request",
                          "message": f"Request body is not valid JSON: {parse_error}"}
            })
            return
        # Reflect the anatomy back, so what you sent is what you study.
        self.send_json(200, {
            "received": {
                "method": self.command,
                "path": self.path,
                "content_type": self.headers.get("Content-Type"),
                "body": body,
            },
            "output": "Echo complete. Every field above came from your request.",
            "usage": {"input_tokens": len(json.dumps(body).split()), "output_tokens": 9},
        })

    def handle_stream(self):
        if not self.authorized():
            self.send_json(401, ERROR_EXHIBITS["auth"][2])
            return
        self.read_body()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Request-Id", self.request_id())
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

        def chunk(text):
            data = text.encode()
            self.wfile.write(f"{len(data):X}\r\n".encode() + data + b"\r\n")
            self.wfile.flush()

        try:
            for word in STREAM_WORDS:
                chunk(f'data: {json.dumps({"delta": word + " "})}\n\n')
                time.sleep(0.25)
            chunk('data: {"done": true, "usage": {"output_tokens": %d}}\n\n' % len(STREAM_WORDS))
            self.wfile.write(b"0\r\n\r\n")
        except (BrokenPipeError, ConnectionResetError):
            # The client hung up mid-stream (Ctrl+C on curl). That is not an
            # error; canceling a stream is one of the lesson's exercises.
            print(f"[mock {self.request_id()}] client canceled the stream", flush=True)

    def handle_slow(self):
        if not self.authorized():
            self.send_json(401, ERROR_EXHIBITS["auth"][2])
            return
        self.read_body()
        # Deliberately slower than any sane client timeout. Your --max-time
        # fires long before this returns, which is the point.
        time.sleep(8)
        self.send_json(200, {
            "output": "If you are reading this, you waited the full eight seconds.",
            "usage": {"input_tokens": 1, "output_tokens": 12},
        })


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), MockService)
    print(f"API lab listening on http://{HOST}:{PORT}  (Ctrl+C to stop)", flush=True)
    print("Endpoints: POST /v1/echo /v1/stream /v1/slow, GET /v1/error/<kind>", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAPI lab stopped.")
