"""Tests for supervisor classification + customer lookup."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.state import SupportState
from agents.supervisor import classify_and_route


def _initial(text: str, email: str | None = None) -> SupportState:
    return {"user_input": text, "customer_email": email, "trace": []}


def test_classifies_billing_keywords():
    out = classify_and_route(_initial("My card was charged twice this week."))
    assert out["classification"] == "billing"
    assert out["classification_confidence"] > 0


def test_classifies_technical_keywords():
    out = classify_and_route(_initial("I'm getting 502 errors and timeouts."))
    assert out["classification"] == "technical"


def test_escalation_takes_priority():
    out = classify_and_route(
        _initial("I'm being charged wrong and I'm calling my lawyer about this fraud.")
    )
    assert out["classification"] == "escalation"


def test_general_when_no_keywords():
    out = classify_and_route(_initial("Hi, just checking in."))
    assert out["classification"] == "general"


def test_resolves_customer_when_email_known():
    out = classify_and_route(_initial("Question about plan", email="alice@example.com"))
    assert out["customer_id"] == "c_alice_123"
    assert out["customer_data"]["name"] == "Alice"


def test_unknown_customer_email_returns_none():
    out = classify_and_route(_initial("Hi", email="ghost@example.com"))
    assert out["customer_id"] is None
    assert out["customer_data"] is None


def test_no_email_means_no_customer_lookup():
    out = classify_and_route(_initial("Hi"))
    assert out.get("customer_id") is None


def test_classification_appends_trace():
    out = classify_and_route(_initial("Refund for double charge", email="alice@example.com"))
    assert len(out["trace"]) == 1
    entry = out["trace"][0]
    assert entry["agent"] == "supervisor"
    assert entry["action"] == "classify_and_route"
    assert entry["classification"] == "billing"
