"""
Agent layer for the CRM intelligence assistant. The supervisor pattern
from module 10 with three specialists scoped to read-only operations.

Replace the heuristic specialist bodies with real LLM calls + tool use
for production. The shape (supervisor classifies; specialists handle
narrow operations; nothing writes without human approval) stays the same.
"""

from __future__ import annotations

from dataclasses import dataclass
from . import data


@dataclass
class Response:
    answer: str
    citations: list[dict]
    pending_action: dict | None = None


def _classify(question: str) -> str:
    q = question.lower()
    if "renewal" in q or "renew" in q or "at risk" in q or "expiring" in q:
        return "portfolio"
    if "what" in q and ("latest" in q or "recent" in q or "summary" in q or "with" in q):
        return "account_lookup"
    if "draft" in q or "write" in q or "send" in q or "create" in q:
        return "action_proposer"
    return "account_lookup"


def account_lookup_specialist(question: str) -> Response:
    """Read-only Q&A about a single account."""
    accounts = data.search_accounts(_extract_account_hint(question))
    if not accounts:
        return Response(
            answer="I could not find an account that matches. Try the company name or owner email.",
            citations=[],
        )
    account = accounts[0]
    detail = data.get_account_detail(account.id)
    note_summary = ""
    if detail and detail.notes:
        latest = detail.notes[-1]
        note_summary = f" Most recent note ({latest['date']}, by {latest['author']}): \"{latest['body']}\""

    answer = (
        f"{account.name} ({account.id}): {account.plan} plan, "
        f"${account.mrr_cents / 100:.2f} MRR, renewal in {account.renewal_in_days()} days, "
        f"health score {account.health_score}. Owner: {account.owner}.{note_summary}"
    )
    citations = [
        {"account_id": account.id, "field": "plan"},
        {"account_id": account.id, "field": "mrr_cents"},
        {"account_id": account.id, "field": "contract_end"},
    ]
    return Response(answer=answer, citations=citations)


def portfolio_query_specialist(question: str) -> Response:
    """Cross-account aggregations."""
    q = question.lower()
    days = 60
    for d in (30, 60, 90, 180):
        if str(d) in q:
            days = d
            break

    if "at risk" in q:
        accounts = data.at_risk_accounts()
        answer_lines = [f"{len(accounts)} accounts under the health threshold:"]
        for a in accounts:
            answer_lines.append(
                f"  - {a.name} (health {a.health_score}, ${a.mrr_cents / 100:.0f} MRR, "
                f"renewal in {a.renewal_in_days()} days)"
            )
        return Response(
            answer="\n".join(answer_lines),
            citations=[{"account_id": a.id, "field": "health_score"} for a in accounts],
        )

    accounts = data.renewals_within(days)
    answer_lines = [f"{len(accounts)} accounts renewing in the next {days} days:"]
    for a in accounts:
        answer_lines.append(
            f"  - {a.name} (renewal in {a.renewal_in_days()} days, "
            f"health {a.health_score}, ${a.mrr_cents / 100:.0f} MRR)"
        )
    return Response(
        answer="\n".join(answer_lines),
        citations=[{"account_id": a.id, "field": "contract_end"} for a in accounts],
    )


def action_proposer(question: str) -> Response:
    """
    Proposes an action; never executes. The pending_action payload is
    what the human reviewer sees before approving.
    """
    return Response(
        answer=(
            "I have drafted a proposed action; nothing has been sent or written yet. "
            "Review the pending_action payload and approve before submission."
        ),
        citations=[],
        pending_action={
            "type": "draft_only",
            "intent": "documented; needs human approval",
            "request": question,
        },
    )


def respond(question: str) -> Response:
    classification = _classify(question)
    if classification == "portfolio":
        return portfolio_query_specialist(question)
    if classification == "action_proposer":
        return action_proposer(question)
    return account_lookup_specialist(question)


def _extract_account_hint(question: str) -> str:
    """
    Naive: take the longest noun-ish token. Real implementation would
    parse account name with NER or use the LLM with a tool.
    """
    candidates = [t for t in question.replace("?", "").replace(".", "").split() if t.istitle()]
    if candidates:
        return " ".join(candidates)
    return question[:40]
