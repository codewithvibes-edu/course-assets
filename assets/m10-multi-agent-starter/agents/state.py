"""
Shared state contract for the multi-agent support system.

Every node reads SupportState; only specific nodes write specific
fields. This file is the contract; if a field is added here, the
graph in graph.py and the specialists below all see it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypedDict


class SupportState(TypedDict, total=False):
    # Inputs
    user_input: str
    customer_email: str | None

    # Set by the supervisor
    customer_id: str | None
    customer_data: dict[str, Any] | None
    classification: str | None        # 'billing' | 'technical' | 'escalation' | 'general'
    classification_confidence: float | None

    # Set by specialists
    specialist_response: str | None

    # Set when an action requires human approval
    pending_action: dict[str, Any] | None

    # Final output
    final_answer: str | None

    # Per-step audit trail; specialists append to it
    trace: list[dict[str, Any]]


def append_trace(state: SupportState, *, agent: str, action: str, **details: Any) -> SupportState:
    """Append a structured trace entry. Returns a new state dict."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "action": action,
        **details,
    }
    trace = list(state.get("trace") or [])
    trace.append(entry)
    return {**state, "trace": trace}
