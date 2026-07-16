"""
Billing specialist. Looks up the invoice, decides whether a refund
is appropriate, and either:
  - resolves the issue (e.g., update payment method)
  - proposes a refund and waits for human approval (irreversible action)
"""

from __future__ import annotations

import re

from .state import SupportState, append_trace
from .tools import lookup_invoice, propose_refund, update_payment_method


_DUPLICATE_HINTS = ("twice", "double", "duplicate", "two times", "x2")
_PAYMENT_METHOD_HINTS = ("update card", "new card", "change card", "expired", "different card")


def billing_specialist(state: SupportState) -> SupportState:
    customer_data = state.get("customer_data") or {}
    customer_id = state.get("customer_id")
    ticket = state.get("user_input", "")
    text = ticket.lower()

    if not customer_id:
        return _no_customer(state)

    # Look up recent invoices to ground the response in real account data.
    invoices = lookup_invoice(customer_id)

    # Branch on the type of billing issue.
    if any(h in text for h in _DUPLICATE_HINTS):
        return _propose_refund_for_duplicate(state, invoices)

    if any(h in text for h in _PAYMENT_METHOD_HINTS):
        return _handle_payment_method(state, customer_id)

    return _generic_billing_followup(state, customer_data, invoices)


def _no_customer(state: SupportState) -> SupportState:
    response = (
        "I could not match this email to a customer record. "
        "Please confirm the email on file or provide your customer ID."
    )
    new_state = {**state, "specialist_response": response, "final_answer": response}
    return append_trace(new_state, agent="billing", action="missing_customer")


def _propose_refund_for_duplicate(state: SupportState, invoices: list[dict]) -> SupportState:
    """Duplicate-charge case: propose a refund; do NOT execute. Pending approval."""
    customer_id = state["customer_id"]
    if not invoices:
        return _generic_billing_followup(state, state.get("customer_data") or {}, invoices)

    inv = invoices[0]
    pending = propose_refund(
        customer_id=customer_id,
        charge_id=inv["invoice_id"],
        amount_cents=inv["amount_cents"],
        reason="customer reports duplicate charge",
    )
    response = (
        f"I see invoice {inv['invoice_id']} for ${inv['amount_cents'] / 100:.2f}. "
        "I have proposed a refund for review by our team; you will see it on your card within "
        "5-10 business days once approved."
    )
    new_state: SupportState = {
        **state,
        "specialist_response": response,
        "pending_action": pending,
        "final_answer": response,
    }
    return append_trace(
        new_state,
        agent="billing",
        action="proposed_refund_for_duplicate",
        invoice=inv["invoice_id"],
        amount_cents=inv["amount_cents"],
    )


def _handle_payment_method(state: SupportState, customer_id: str) -> SupportState:
    response = (
        "To update your payment method, please use the billing portal at "
        "https://example.com/account/billing — it lets you swap cards "
        "without exposing the number to support."
    )
    new_state = {**state, "specialist_response": response, "final_answer": response}
    return append_trace(new_state, agent="billing", action="directed_to_portal")


def _generic_billing_followup(
    state: SupportState, customer_data: dict, invoices: list[dict]
) -> SupportState:
    response_lines = [
        f"Looking at your account, you are on the {customer_data.get('plan', 'unknown')} plan, "
        f"status {customer_data.get('billing_status', 'unknown')}. ",
    ]
    if invoices:
        inv = invoices[0]
        response_lines.append(
            f"Your most recent invoice is {inv['invoice_id']} for "
            f"${inv['amount_cents'] / 100:.2f}, status {inv['status']}. "
        )
    response_lines.append(
        "Could you tell me a bit more about what is wrong with the charge or the plan? "
        "Specifics help me find the right resolution."
    )
    response = "".join(response_lines)
    new_state = {**state, "specialist_response": response, "final_answer": response}
    return append_trace(new_state, agent="billing", action="generic_followup")
