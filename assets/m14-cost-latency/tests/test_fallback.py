"""Tests for tracking.fallback."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tracking.fallback import AllFallbacksFailed, FallbackChain


def test_primary_succeeds():
    chain = FallbackChain(
        providers=[
            {"name": "primary", "fn": lambda x: f"a:{x}"},
            {"name": "secondary", "fn": lambda x: f"b:{x}"},
        ]
    )
    result = chain.run("hello")
    assert result.provider_name == "primary"
    assert result.fallback_level == 0
    assert result.value == "a:hello"
    assert result.errors_before == []


def test_fallback_to_secondary():
    def primary(x):
        raise TimeoutError("primary down")

    chain = FallbackChain(
        providers=[
            {"name": "primary", "fn": primary},
            {"name": "secondary", "fn": lambda x: f"b:{x}"},
        ]
    )
    result = chain.run("hello")
    assert result.provider_name == "secondary"
    assert result.fallback_level == 1
    assert len(result.errors_before) == 1
    assert isinstance(result.errors_before[0], TimeoutError)


def test_all_fail_raises():
    def boom(x):
        raise ConnectionError("down")

    chain = FallbackChain(
        providers=[
            {"name": "a", "fn": boom},
            {"name": "b", "fn": boom},
        ]
    )
    with pytest.raises(AllFallbacksFailed) as exc_info:
        chain.run("anything")
    assert len(exc_info.value.errors) == 2


def test_empty_chain_raises():
    chain = FallbackChain(providers=[])
    with pytest.raises(AllFallbacksFailed):
        chain.run("x")


def test_passes_args_through():
    chain = FallbackChain(
        providers=[
            {"name": "p", "fn": lambda a, b, c=0: a + b + c},
        ]
    )
    result = chain.run(1, 2, c=3)
    assert result.value == 6
