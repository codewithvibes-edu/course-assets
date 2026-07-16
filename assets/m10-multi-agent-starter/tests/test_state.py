"""Tests for the SupportState contract + append_trace helper."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.state import SupportState, append_trace


def test_append_trace_creates_list_when_missing():
    state: SupportState = {"user_input": "hi"}
    new_state = append_trace(state, agent="x", action="did_thing", k="v")
    assert "trace" in new_state
    assert len(new_state["trace"]) == 1
    assert new_state["trace"][0]["agent"] == "x"
    assert new_state["trace"][0]["action"] == "did_thing"
    assert new_state["trace"][0]["k"] == "v"
    assert "ts" in new_state["trace"][0]


def test_append_trace_appends_to_existing():
    state: SupportState = {"user_input": "hi", "trace": [{"prior": True}]}
    new_state = append_trace(state, agent="x", action="step")
    assert len(new_state["trace"]) == 2
    assert new_state["trace"][0] == {"prior": True}


def test_append_trace_does_not_mutate_input():
    state: SupportState = {"user_input": "hi", "trace": []}
    original_trace = state["trace"]
    new_state = append_trace(state, agent="x", action="step")
    # Original trace is untouched
    assert original_trace == []
    # New state has the entry
    assert len(new_state["trace"]) == 1


def test_append_trace_carries_other_fields():
    state: SupportState = {
        "user_input": "hi",
        "classification": "billing",
        "customer_id": "c_1",
    }
    new_state = append_trace(state, agent="x", action="step")
    assert new_state["classification"] == "billing"
    assert new_state["customer_id"] == "c_1"
