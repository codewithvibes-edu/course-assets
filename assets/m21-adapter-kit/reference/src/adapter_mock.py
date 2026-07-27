"""The deterministic adapter. No network, no key, no cost, and the same
contract suite as every other adapter, which is the whole point: this file
proves the second connection does not need a second paid account, and it
doubles as the fallback and testing connection every later module wants.

Deterministic means deterministic: the same request produces the same
response, byte for byte, every time. That property is what Module 13's
evals will love about it.
"""

import hashlib
import time

from canonical import (
    AdapterError, CanonicalResponse, Capabilities, StreamEvent, Usage,
)


def _digest(request):
    text = "|".join(f"{m.role}:{m.content}" for m in request.messages)
    return hashlib.sha256(text.encode()).hexdigest()[:8]


class MockAdapter:
    def __init__(self, model="mock-deterministic-1"):
        self.model = model
        self._counter = 0

    def capabilities(self):
        return Capabilities(
            text=True, streaming=True, structured_output=False,
            tools=False, image_input=False, last_tested="2026-07-24",
        )

    def test(self):
        return True

    def _content(self, request):
        last = request.messages[-1].content if request.messages else ""
        words = len(last.split())
        return (f"[deterministic {_digest(request)}] Received {len(request.messages)} "
                f"message(s); the last one carries {words} word(s).")

    def _request_id(self):
        self._counter += 1
        return f"local-{self._counter:04d}"

    def generate(self, request):
        if request.media:
            raise AdapterError("unsupported",
                               "image_input is False for this connection.")
        started = time.monotonic()
        content = self._content(request)
        return CanonicalResponse(
            content=content,
            finish_reason="complete",
            usage=Usage(input_tokens=sum(len(m.content.split())
                                         for m in request.messages),
                        output_tokens=len(content.split())),
            latency_s=time.monotonic() - started,
            request_id=self._request_id(),
            raw_debug="mock adapter; nothing left the machine",
        )

    def stream(self, request):
        if request.media:
            raise AdapterError("unsupported",
                               "image_input is False for this connection.")
        content = self._content(request)
        words = content.split(" ")
        try:
            for word in words:
                yield StreamEvent(kind="delta", text=word + " ")
            yield StreamEvent(
                kind="done",
                usage=Usage(output_tokens=len(words)),
                request_id=self._request_id(),
            )
        except GeneratorExit:
            # Canceled by the application. Clean close is the contract.
            return
