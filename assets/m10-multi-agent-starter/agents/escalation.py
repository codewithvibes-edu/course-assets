"""
Escalation specialist. Drafts a summary and posts it to a human queue.
NEVER autonomously resolves. Returns a final_answer to the user
acknowledging that a human will take over.
"""

from __future__ import annotations

from .state import SupportState, append_trace
from .tools import summarize_for_human


def _build_summary(state: SupportState) -> str:
    customer = state.get("customer_data") or {}
    parts = [
        f"Inbound ticket: {state.get('user_input', '')[:500]}",
        f"Classification: {state.get('classification')} "
        f"(confidence {state.get('classification_confidence', 0):.2f})",
    ]
    if customer:
        parts.append(
            f"Customer: {customer.get('name')} ({customer.get('customer_id')}) — "
            f"{customer.get('plan')} plan, {customer.get('billing_status')}"
        )
    return "\n".join(parts)


def escalation_specialist(state: SupportState) -> SupportState:
    summary = _build_summary(state)
    receipt = summarize_for_human(summary)

    response = (
        "I've flagged this for a human teammate. They will reach out shortly with the right "
        "next steps. I do not have the authority to handle this kind of issue myself, "
        "so I am stepping out of the way rather than guessing."
    )
    new_state: SupportState = {
        **state,
        "specialist_response": response,
        "final_answer": response,
        "pending_action": {
            "type": "escalation_posted",
            "queue_receipt": receipt,
        },
    }
    return append_trace(
        new_state,
        agent="escalation",
        action="posted_to_human_queue",
        ticket_ref=receipt["ticket_ref"],
    )
