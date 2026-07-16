"""
Technical specialist. Searches runbooks, checks service status, and
optionally creates a bug report. Does not autonomously change
production state; the worst it does is file a bug ticket.
"""

from __future__ import annotations

from .state import SupportState, append_trace
from .tools import check_service_status, create_bug_report, search_runbooks


_SERVICE_HINTS = {
    "billing": ("billing", "invoice", "checkout", "stripe"),
    "web": ("web", "page", "site", "frontend", "ui"),
    "data": ("database", "db", "data", "query", "report"),
}


def _guess_service(text: str) -> str | None:
    lower = text.lower()
    for service, hints in _SERVICE_HINTS.items():
        if any(h in lower for h in hints):
            return service
    return None


def technical_specialist(state: SupportState) -> SupportState:
    ticket = state.get("user_input", "")
    service_guess = _guess_service(ticket)

    # Check service status first; that's the cheapest path to a definitive
    # answer ("the service is up — your issue is local-side").
    status = check_service_status(service_guess) if service_guess else None

    # Search for matching runbooks.
    runbooks = search_runbooks(ticket, service_filter=service_guess)

    response_parts: list[str] = []

    if status and status["status"] != "up":
        response_parts.append(
            f"Heads up: the {status['service']} service is currently {status['status']}. "
            "We are aware and working on it. "
        )

    if runbooks:
        rb = runbooks[0]
        response_parts.append(
            f"Based on what you described, this matches our runbook '{rb['title']}'. "
            f"Suggested fix: {rb['body']} "
            "If that does not resolve the issue, reply and I will create a bug ticket."
        )
    else:
        response_parts.append(
            "I do not have a matching runbook for this. To make sure it gets the right "
            "attention, can you confirm: (a) when did this start, (b) what URL or feature "
            "are you on, and (c) any error messages you can copy verbatim?"
        )

    response = "".join(response_parts)
    new_state: SupportState = {
        **state,
        "specialist_response": response,
        "final_answer": response,
    }

    return append_trace(
        new_state,
        agent="technical",
        action="diagnosed_with_runbooks",
        service_guess=service_guess,
        runbook_count=len(runbooks),
        service_status=status["status"] if status else None,
    )
