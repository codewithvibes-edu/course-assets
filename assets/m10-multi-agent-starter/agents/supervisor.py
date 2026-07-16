"""
Supervisor agent. Classifies the inbound ticket and identifies the
customer. Does NOT resolve; just sets state["classification"] and
state["customer_id"] / state["customer_data"], then the graph routes.
"""

from __future__ import annotations

from .state import SupportState, append_trace
from .tools import lookup_customer


# Classification keywords. Real implementations call an LLM with
# the ticket + few-shot examples. The keyword fallback is here so
# the graph runs without API access for testing.
_BILLING_HINTS = (
    "charge",
    "charged",
    "refund",
    "billing",
    "invoice",
    "payment",
    "subscription",
    "plan",
    "card",
    "receipt",
)
_TECHNICAL_HINTS = (
    "bug",
    "error",
    "broken",
    "not working",
    "outage",
    "down",
    "500",
    "502",
    "timeout",
    "slow",
    "crash",
)
_ESCALATION_HINTS = (
    "lawyer",
    "legal",
    "press",
    "media",
    "complaint",
    "fraud",
    "security",
    "breach",
    "data leak",
    "this is unacceptable",
)


def _classify(ticket: str) -> tuple[str, float]:
    """
    Heuristic classifier with confidence. In production, replace with an
    LLM call (Claude Haiku at temperature 0 is sized right for this).
    """
    text = ticket.lower()

    def hits(words: tuple[str, ...]) -> int:
        return sum(1 for w in words if w in text)

    counts = {
        "billing": hits(_BILLING_HINTS),
        "technical": hits(_TECHNICAL_HINTS),
        "escalation": hits(_ESCALATION_HINTS),
    }
    if all(v == 0 for v in counts.values()):
        return "general", 0.5

    label = max(counts, key=lambda k: counts[k])
    total = sum(counts.values()) or 1
    confidence = counts[label] / total
    # Escalation has priority if there's any signal
    if counts["escalation"] > 0:
        return "escalation", max(confidence, 0.7)
    return label, confidence


def classify_and_route(state: SupportState) -> SupportState:
    """
    Supervisor node. Reads user_input + customer_email, sets
    classification + customer fields, returns the merged state.
    """
    ticket = state.get("user_input", "")
    email = state.get("customer_email")
    label, confidence = _classify(ticket)

    customer_data = lookup_customer(email) if email else None

    new_state: SupportState = {
        **state,
        "classification": label,
        "classification_confidence": confidence,
        "customer_id": customer_data["customer_id"] if customer_data else None,
        "customer_data": customer_data,
    }
    return append_trace(
        new_state,
        agent="supervisor",
        action="classify_and_route",
        classification=label,
        confidence=confidence,
        customer_resolved=customer_data is not None,
    )


def route_after_supervisor(state: SupportState) -> str:
    """
    LangGraph conditional-edge function. Returns the name of the next
    node based on the classification.
    """
    label = state.get("classification", "general")
    if label == "billing":
        return "billing_specialist"
    if label == "technical":
        return "technical_specialist"
    if label == "escalation":
        return "escalation_specialist"
    return "general_specialist"
