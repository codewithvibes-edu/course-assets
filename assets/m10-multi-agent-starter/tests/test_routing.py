"""Tests for the conditional-edge router + end-to-end node chaining."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents import (
    SupportState,
    billing_specialist,
    classify_and_route,
    escalation_specialist,
    general_specialist,
    technical_specialist,
)
from agents.supervisor import route_after_supervisor


def _initial(text: str, email: str | None = None) -> SupportState:
    return {"user_input": text, "customer_email": email, "trace": []}


def test_router_returns_billing():
    state = classify_and_route(_initial("Refund for charge"))
    assert route_after_supervisor(state) == "billing_specialist"


def test_router_returns_technical():
    state = classify_and_route(_initial("502 error every minute"))
    assert route_after_supervisor(state) == "technical_specialist"


def test_router_returns_escalation():
    state = classify_and_route(_initial("I'm calling a lawyer about this fraud"))
    assert route_after_supervisor(state) == "escalation_specialist"


def test_router_returns_general():
    state = classify_and_route(_initial("Hi, just checking in."))
    assert route_after_supervisor(state) == "general_specialist"


def test_billing_duplicate_proposes_refund():
    state = classify_and_route(_initial("My card was charged twice", email="alice@example.com"))
    final = billing_specialist(state)
    assert final.get("pending_action", {}).get("type") == "refund"
    assert final.get("pending_action", {}).get("requires_approval") is True


def test_billing_payment_method_directs_to_portal():
    state = classify_and_route(
        _initial("I need to update my card with a new card", email="alice@example.com")
    )
    final = billing_specialist(state)
    assert "billing portal" in final.get("final_answer", "").lower()


def test_technical_returns_runbook_advice():
    state = classify_and_route(_initial("502 errors on the web app"))
    final = technical_specialist(state)
    assert final.get("final_answer")
    # Should reference runbook advice
    assert "runbook" in final["final_answer"].lower() or "fix" in final["final_answer"].lower()


def test_escalation_posts_to_human_queue():
    state = classify_and_route(
        _initial("I'm calling my lawyer about this", email="alice@example.com")
    )
    final = escalation_specialist(state)
    assert final.get("pending_action", {}).get("type") == "escalation_posted"
    assert "human" in final.get("final_answer", "").lower()


def test_general_asks_clarifier():
    state = classify_and_route(_initial("Hi"))
    final = general_specialist(state)
    assert "billing" in final["final_answer"].lower() or "technical" in final["final_answer"].lower()


def test_full_chain_appends_traces():
    state = classify_and_route(_initial("My card was charged twice", email="alice@example.com"))
    final = billing_specialist(state)
    # Two entries: supervisor + billing
    assert len(final["trace"]) == 2
    assert final["trace"][0]["agent"] == "supervisor"
    assert final["trace"][1]["agent"] == "billing"
