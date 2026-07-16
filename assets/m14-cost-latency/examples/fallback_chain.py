"""
Worked example: a 3-provider fallback chain. The primary deliberately
fails the first call to demonstrate the secondary kicking in.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tracking.fallback import AllFallbacksFailed, FallbackChain


class FakeTimeout(Exception):
    pass


class FakeAuthError(Exception):
    pass


_call_count = {"primary": 0, "secondary": 0, "tertiary": 0}


def primary(prompt: str) -> str:
    _call_count["primary"] += 1
    # First call fails with a retryable error.
    if _call_count["primary"] == 1:
        raise FakeTimeout("primary timed out")
    return f"[primary] {prompt}"


def secondary(prompt: str) -> str:
    _call_count["secondary"] += 1
    return f"[secondary] {prompt}"


def tertiary(prompt: str) -> str:
    _call_count["tertiary"] += 1
    return f"[tertiary] {prompt}"


def main():
    chain = FallbackChain(
        providers=[
            {"name": "primary", "fn": primary},
            {"name": "secondary", "fn": secondary},
            {"name": "tertiary", "fn": tertiary},
        ]
    )

    print("Call 1 (primary fails -> falls to secondary):")
    result1 = chain.run("hello")
    print(f"  used={result1.provider_name} level={result1.fallback_level} value={result1.value}")
    print(f"  errors_before={[type(e).__name__ for e in result1.errors_before]}")

    print("\nCall 2 (primary works):")
    result2 = chain.run("hello again")
    print(f"  used={result2.provider_name} level={result2.fallback_level} value={result2.value}")

    print("\nCall counts:", _call_count)


if __name__ == "__main__":
    main()
