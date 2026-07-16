"""
Data layer for the CRM intelligence assistant.

Replace the placeholder client with a real CRM SDK (Salesforce,
HubSpot, Attio, custom REST) before treating this as anything other
than a teaching demo. The agent layer in src/agents.py talks to this
module via stable function signatures, so you can swap the backend
without touching agent code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any


@dataclass
class Account:
    id: str
    name: str
    plan: str
    mrr_cents: int
    contract_start: str
    contract_end: str
    owner: str
    health_score: int   # 0-100; placeholder for real risk modeling
    notes: list[dict[str, Any]] = field(default_factory=list)
    open_tickets: int = 0
    last_active_at: str = ""

    def renewal_in_days(self) -> int:
        end = datetime.fromisoformat(self.contract_end).replace(tzinfo=timezone.utc)
        return max(0, (end - datetime.now(timezone.utc)).days)


# Placeholder data. Replace with a real CRM client at production time.
_FAKE_ACCOUNTS: list[Account] = [
    Account(
        id="acc_acme",
        name="ACME Corp",
        plan="enterprise",
        mrr_cents=250_000,
        contract_start="2024-08-01",
        contract_end="2026-07-31",
        owner="alice@yourco.com",
        health_score=82,
        notes=[
            {"date": "2026-04-22", "author": "alice", "body": "Renewal call went well; CFO aligned."},
            {"date": "2026-05-01", "author": "alice", "body": "ACME asked about SSO upgrade."},
        ],
        open_tickets=1,
        last_active_at="2026-05-05",
    ),
    Account(
        id="acc_nimble",
        name="Nimble Industries",
        plan="growth",
        mrr_cents=80_000,
        contract_start="2025-06-01",
        contract_end="2026-05-31",
        owner="bob@yourco.com",
        health_score=44,
        notes=[
            {"date": "2026-04-15", "author": "bob", "body": "Champion left the company."},
            {"date": "2026-04-30", "author": "bob", "body": "No one responded to outreach this week."},
        ],
        open_tickets=4,
        last_active_at="2026-04-25",
    ),
    Account(
        id="acc_vortex",
        name="Vortex Labs",
        plan="starter",
        mrr_cents=15_000,
        contract_start="2025-12-01",
        contract_end="2026-11-30",
        owner="alice@yourco.com",
        health_score=71,
        notes=[
            {"date": "2026-04-10", "author": "alice", "body": "Asked about API rate limits."},
        ],
        open_tickets=0,
        last_active_at="2026-05-06",
    ),
]


def search_accounts(query: str, limit: int = 10) -> list[Account]:
    """Substring match on name + owner. Returns up to `limit` results."""
    q = query.lower()
    hits = [a for a in _FAKE_ACCOUNTS if q in a.name.lower() or q in a.owner.lower()]
    return hits[:limit]


def get_account_detail(account_id: str) -> Account | None:
    for a in _FAKE_ACCOUNTS:
        if a.id == account_id:
            return a
    return None


def renewals_within(days: int) -> list[Account]:
    """Accounts whose contract ends within N days. Sorted by health (worst first)."""
    upcoming = [a for a in _FAKE_ACCOUNTS if a.renewal_in_days() <= days]
    upcoming.sort(key=lambda a: a.health_score)
    return upcoming


def at_risk_accounts(health_threshold: int = 60) -> list[Account]:
    """Accounts below a health-score threshold."""
    return [a for a in _FAKE_ACCOUNTS if a.health_score < health_threshold]
