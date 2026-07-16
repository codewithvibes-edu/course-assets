"""
Tool implementations. Placeholder shapes so the example graph runs
without a real backend. Replace each function with a real CRM /
service-status / runbook integration before treating this as anything
other than a teaching demo.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone


# ---- Customer / billing tools ----


_FAKE_CUSTOMERS = {
    "alice@example.com": {
        "customer_id": "c_alice_123",
        "name": "Alice",
        "plan": "pro",
        "billing_status": "past_due",
        "last_payment": "2026-04-01",
    },
    "bob@example.com": {
        "customer_id": "c_bob_456",
        "name": "Bob",
        "plan": "starter",
        "billing_status": "active",
        "last_payment": "2026-04-15",
    },
}


def lookup_customer(email: str) -> dict | None:
    """Find a customer by email. Returns None if not found."""
    return _FAKE_CUSTOMERS.get(email.lower())


def lookup_invoice(customer_id: str, invoice_id: str | None = None) -> list[dict]:
    """Return recent invoices for a customer."""
    return [
        {
            "invoice_id": invoice_id or "inv_2026_04",
            "customer_id": customer_id,
            "amount_cents": 4900,
            "status": "paid",
            "issued_at": "2026-04-01",
        }
    ]


def propose_refund(customer_id: str, charge_id: str, amount_cents: int, reason: str) -> dict:
    """
    Propose a refund. DOES NOT execute. Returns a pending_action
    payload for the human-approval gate.
    """
    return {
        "type": "refund",
        "customer_id": customer_id,
        "charge_id": charge_id,
        "amount_cents": amount_cents,
        "reason": reason,
        "proposed_at": datetime.now(timezone.utc).isoformat(),
        "requires_approval": True,
    }


def update_payment_method(customer_id: str, new_method_token: str) -> dict:
    """Idempotent: same token applied twice has the same result."""
    return {
        "customer_id": customer_id,
        "method_token": new_method_token,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


# ---- Technical tools ----


_FAKE_RUNBOOKS = [
    {
        "id": "rb-1",
        "title": "Resolving 502s on the web tier",
        "service": "web",
        "body": "Check upstream connection counts. Restart workers in batches of 3 with 30s between to avoid thundering herd.",
    },
    {
        "id": "rb-2",
        "title": "Billing webhook delivery failures",
        "service": "billing",
        "body": "Verify the webhook signing secret matches dashboard. Replay missed events from the Stripe dashboard.",
    },
    {
        "id": "rb-3",
        "title": "Database connection saturation",
        "service": "data",
        "body": "Reduce pool size on slow consumers. Add a read replica. Investigate long-running transactions in pg_stat_activity.",
    },
]


def search_runbooks(query: str, service_filter: str | None = None) -> list[dict]:
    q = query.lower()
    hits = []
    for rb in _FAKE_RUNBOOKS:
        if service_filter and rb["service"] != service_filter:
            continue
        if q in rb["title"].lower() or q in rb["body"].lower():
            hits.append(rb)
    return hits[:5]


def check_service_status(service_name: str) -> dict:
    """Returns up/down + last incident. Faked here."""
    return {
        "service": service_name,
        "status": "up" if random.random() > 0.05 else "degraded",
        "last_incident": None,
        "metrics_summary": {"latency_ms_p50": 150, "error_rate": 0.001},
    }


def create_bug_report(title: str, severity: str, service: str, description: str) -> dict:
    """Creates a bug. Idempotency is the caller's concern; we generate a fresh ID."""
    return {
        "ticket_id": f"BUG-{uuid.uuid4().hex[:8]}",
        "title": title,
        "severity": severity,
        "service": service,
        "description": description,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


# ---- Escalation tools ----


def summarize_for_human(state_summary: str, queue: str = "support_humans") -> dict:
    """
    Post a summary to a human queue. Does not autonomously resolve.
    Returns the queue receipt.
    """
    return {
        "queue": queue,
        "ticket_ref": f"HUMAN-{uuid.uuid4().hex[:8]}",
        "summary": state_summary,
        "posted_at": datetime.now(timezone.utc).isoformat(),
    }
