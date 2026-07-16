"""
FastAPI webhook handler with HMAC signature verification and idempotency.
The handler enqueues work and returns 200 fast; processing happens async
via the queue worker.
"""

from __future__ import annotations

import hmac
import hashlib
from dataclasses import dataclass
from typing import Awaitable, Callable

from fastapi import FastAPI, HTTPException, Request, Response


@dataclass
class WebhookConfig:
    """One config per inbound webhook source."""

    name: str                      # e.g., 'stripe', 'github', 'newsapi'
    secret: str                    # the shared secret for HMAC verification
    signature_header: str = "X-Signature"
    timestamp_header: str | None = None  # if the source requires timestamped signatures
    max_skew_seconds: int = 300


def verify_hmac_sha256(payload: bytes, signature_header_value: str, secret: str) -> bool:
    """
    Compare-by-constant-time HMAC verification. signature_header_value is
    the raw header value; we strip common prefixes ('sha256=', 't=...').
    """
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    given = signature_header_value.split("=", 1)[-1].strip().lower()
    return hmac.compare_digest(expected, given)


def build_app(
    config: WebhookConfig,
    enqueue: Callable[[bytes, dict], Awaitable[str] | str],
    extract_event_id: Callable[[bytes, dict], str],
) -> FastAPI:
    """
    Build a FastAPI app exposing POST /webhook/{name} that:
      1. Verifies signature.
      2. Extracts the event ID for idempotency (caller-supplied function).
      3. Calls enqueue(body, headers) so the work happens async.
      4. Returns 200 fast.

    The enqueue callable is responsible for idempotency (it can use
    IdempotencyStore from idempotency.py).
    """
    app = FastAPI(title=f"{config.name}-webhook")

    @app.post(f"/webhook/{config.name}")
    async def receive(request: Request) -> Response:
        body = await request.body()
        headers = {k.lower(): v for k, v in request.headers.items()}

        signature = headers.get(config.signature_header.lower())
        if not signature:
            raise HTTPException(status_code=400, detail="missing signature")

        if not verify_hmac_sha256(body, signature, config.secret):
            raise HTTPException(status_code=401, detail="signature invalid")

        try:
            event_id = extract_event_id(body, headers)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"could not extract event id: {exc}") from exc

        result = enqueue(body, headers)
        if hasattr(result, "__await__"):
            await result  # type: ignore[func-returns-value]

        return Response(content=f'{{"received": "{event_id}"}}', media_type="application/json")

    return app
