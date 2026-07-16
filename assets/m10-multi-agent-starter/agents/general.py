"""
General specialist. Catch-all for tickets the supervisor cannot
classify confidently. Asks a clarifying question rather than guessing.
"""

from __future__ import annotations

from .state import SupportState, append_trace


def general_specialist(state: SupportState) -> SupportState:
    customer = state.get("customer_data") or {}
    name = customer.get("name", "")
    greeting = f"Hi {name}, " if name else "Hi, "

    response = (
        f"{greeting}thanks for reaching out. I want to make sure I route this to the "
        "right place. Is this about your billing or subscription, a technical issue with "
        "the product, or something else? A one-line clarification helps me get the right "
        "specialist on it instead of guessing."
    )
    new_state: SupportState = {
        **state,
        "specialist_response": response,
        "final_answer": response,
    }
    return append_trace(new_state, agent="general", action="asked_clarifier")
