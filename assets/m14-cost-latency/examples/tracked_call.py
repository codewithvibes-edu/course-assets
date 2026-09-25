"""
Worked example: wrap a fake LLM call with @tracked so each invocation
writes a TraceSpan. Runs without API keys; replace fake_call with your
real client.
"""

from __future__ import annotations

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tracking import Tracer, tracked


class FakeUsage:
    def __init__(self, input_tokens: int, output_tokens: int):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class FakeResponse:
    def __init__(self, text: str, usage: FakeUsage):
        self.text = text
        self.usage = usage


def fake_call(prompt: str) -> FakeResponse:
    time.sleep(random.uniform(0.05, 0.2))
    in_t = max(20, len(prompt.split()))
    out_t = random.randint(50, 200)
    return FakeResponse("response text...", FakeUsage(in_t, out_t))


def extract_usage(resp: FakeResponse) -> tuple[int, int]:
    return resp.usage.input_tokens, resp.usage.output_tokens


def main():
    tracer = Tracer(db_path="traces.db")

    @tracked(
        tracer,
        agent="demo_responder",
        model="claude-sonnet-5",
        extract_usage=extract_usage,
    )
    def respond(prompt: str) -> FakeResponse:
        return fake_call(prompt)

    for i in range(5):
        respond(f"Sample prompt {i}: explain the concept of reciprocal rank fusion")

    rows = tracer.query("SELECT span_id, agent, duration_ms, cost_cents FROM traces ORDER BY started_at DESC LIMIT 10")
    print(f"Wrote {len(rows)} traces:")
    for row in rows:
        print(f"  {row['span_id']}  {row['agent']}  {row['duration_ms']}ms  {row['cost_cents']:.4f}c")


if __name__ == "__main__":
    main()
