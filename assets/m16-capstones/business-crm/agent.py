"""
Agent layer for the CRM intelligence assistant.

Single-agent + tool-use pattern (module 9): the model decides which
tools to call against the data layer to answer the question. Read-only
tools only at v1; write operations route through `propose_action` which
produces a pending-action payload for human review (module 14 pattern).

Falls back to a deterministic stub when ANTHROPIC_API_KEY is missing
so `python example.py` always runs end-to-end. Real usage requires
the key.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Make sibling modules importable regardless of cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_layer import (
    all_accounts,
    assemble_account_context,
    at_risk_accounts,
    get_account,
    renewals_within,
    search_accounts,
)


# Use a Sonnet-class model: routing + grounded Q&A doesn't need Opus,
# and Haiku will struggle with multi-tool sequencing. See module 3.
MODEL = os.environ.get("CRM_AGENT_MODEL", "claude-sonnet-4-7")
MAX_TOOL_ROUNDS = 5  # bounded loop; module 13 anti-pattern: unbounded agent loops


SYSTEM_PROMPT = """You are a CRM intelligence assistant for an internal sales / customer success team.

Your job is to answer questions about accounts using the provided tools. Rules:

1. Always ground your answer in tool output. If a tool returns no data, say so.
2. Every factual claim cites an account_id and the field it came from (e.g., "ACME (acc_acme) is on the enterprise plan").
3. You have READ-ONLY tools. If the user asks you to send an email, draft a message, change account data, or take any other write action, call `propose_action` instead of pretending to do it. A human reviews proposed actions.
4. Keep answers tight. No filler, no preamble, no "based on the information provided." Just the answer.
5. If a question is ambiguous about which account, ask one clarifying question. Do not guess across multiple accounts."""


# ---------- Tool schemas (Anthropic Messages API tool-use format) ----------

TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_accounts",
        "description": (
            "Find accounts by substring match on company name or owner email. "
            "Use when the user names a company or owner but you do not have the account_id."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Company name fragment or owner email fragment."},
                "limit": {"type": "integer", "description": "Max results to return.", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_account_context",
        "description": (
            "Fetch full context for one account: profile fields, recent notes, open tickets, renewal timing. "
            "Use this once you know the account_id."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "Account ID like 'acc_acme'."},
            },
            "required": ["account_id"],
        },
    },
    {
        "name": "list_renewals",
        "description": "List accounts with contracts ending within N days. Sorted by health (worst first).",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Window in days from today.", "default": 60},
            },
            "required": ["days"],
        },
    },
    {
        "name": "list_at_risk",
        "description": "List accounts whose health_score is below a threshold (default 60).",
        "input_schema": {
            "type": "object",
            "properties": {
                "health_threshold": {"type": "integer", "default": 60},
            },
        },
    },
    {
        "name": "propose_action",
        "description": (
            "Produce a pending-action payload for human review. Use for any non-read operation "
            "(sending email, updating account, creating a deal). Returns a payload; never executes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "enum": ["draft_email", "update_account", "create_task", "other"],
                },
                "target_account_id": {"type": "string"},
                "summary": {"type": "string", "description": "One-line description of what would happen."},
                "draft_content": {"type": "string", "description": "Full draft text if applicable."},
            },
            "required": ["action_type", "summary"],
        },
    },
]


# ---------- Tool dispatch ----------


def _tool_search_accounts(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    hits = search_accounts(conn, args["query"], limit=args.get("limit", 5))
    return {"accounts": [a.to_dict() for a in hits], "count": len(hits)}


def _tool_get_account_context(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    return assemble_account_context(conn, args["account_id"])


def _tool_list_renewals(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    hits = renewals_within(conn, args.get("days", 60))
    return {
        "days": args.get("days", 60),
        "accounts": [
            {
                "id": a.id,
                "name": a.name,
                "plan": a.plan,
                "mrr_cents": a.mrr_cents,
                "renewal_in_days": a.renewal_in_days(),
                "health_score": a.health_score,
            }
            for a in hits
        ],
    }


def _tool_list_at_risk(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    hits = at_risk_accounts(conn, args.get("health_threshold", 60))
    return {
        "threshold": args.get("health_threshold", 60),
        "accounts": [
            {
                "id": a.id,
                "name": a.name,
                "health_score": a.health_score,
                "mrr_cents": a.mrr_cents,
                "renewal_in_days": a.renewal_in_days(),
            }
            for a in hits
        ],
    }


def _tool_propose_action(_conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "pending_human_review",
        "action_type": args["action_type"],
        "target_account_id": args.get("target_account_id"),
        "summary": args["summary"],
        "draft_content": args.get("draft_content", ""),
        "note": "Nothing has been executed. A human must approve before this runs.",
    }


_DISPATCH = {
    "search_accounts": _tool_search_accounts,
    "get_account_context": _tool_get_account_context,
    "list_renewals": _tool_list_renewals,
    "list_at_risk": _tool_list_at_risk,
    "propose_action": _tool_propose_action,
}


# ---------- Agent loop ----------


@dataclass
class AgentResponse:
    answer: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    pending_actions: list[dict[str, Any]] = field(default_factory=list)
    raw_stop_reason: str = ""


def run_agent(question: str, conn: sqlite3.Connection) -> AgentResponse:
    """
    Anthropic Messages API tool-use loop. Returns a final AgentResponse
    once the model stops calling tools.
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        return _fallback_run(question, conn, reason="anthropic SDK not installed")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_run(question, conn, reason="ANTHROPIC_API_KEY not set")

    client = Anthropic(api_key=api_key)
    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
    tool_calls: list[dict[str, Any]] = []
    pending_actions: list[dict[str, Any]] = []

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        if response.stop_reason != "tool_use":
            text = _extract_text(response.content)
            return AgentResponse(
                answer=text,
                tool_calls=tool_calls,
                pending_actions=pending_actions,
                raw_stop_reason=response.stop_reason or "",
            )

        # Echo the assistant turn into the conversation.
        messages.append({"role": "assistant", "content": response.content})

        # Execute every tool call in this turn.
        tool_results: list[dict[str, Any]] = []
        for block in response.content:
            if getattr(block, "type", "") != "tool_use":
                continue
            tool_name = block.name
            tool_input = block.input or {}
            tool_calls.append({"name": tool_name, "input": tool_input})
            handler = _DISPATCH.get(tool_name)
            if handler is None:
                result = {"error": f"unknown tool {tool_name}"}
            else:
                result = handler(conn, tool_input)
                if tool_name == "propose_action":
                    pending_actions.append(result)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                }
            )
        messages.append({"role": "user", "content": tool_results})

    return AgentResponse(
        answer="Agent loop hit max rounds without converging.",
        tool_calls=tool_calls,
        pending_actions=pending_actions,
        raw_stop_reason="max_rounds",
    )


def _extract_text(content_blocks: list[Any]) -> str:
    return "".join(getattr(b, "text", "") for b in content_blocks if getattr(b, "type", "") == "text")


# ---------- Deterministic fallback (no API key) ----------


def _fallback_run(question: str, conn: sqlite3.Connection, reason: str) -> AgentResponse:
    """
    Heuristic answer path. Mirrors the tool-use intent so the example
    still produces an output a reader can verify. Marks the response
    so users understand they are not seeing the real agent.
    """
    q = question.lower()
    tool_calls: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []

    if any(k in q for k in ("draft", "send", "write", "email", "mark", "update", "change", "create")):
        action_type = "draft_email" if any(k in q for k in ("draft", "send", "write", "email")) else "update_account"
        result = _tool_propose_action(
            conn,
            {
                "action_type": action_type,
                "summary": f"would {action_type.replace('_', ' ')} in response to: {question!r}",
                "draft_content": "[fallback: real agent would compose based on account context]",
            },
        )
        pending.append(result)
        tool_calls.append({"name": "propose_action", "input": {"summary": "fallback"}})
        return AgentResponse(
            answer=f"[FALLBACK MODE — {reason}] Proposed action queued for human review.",
            tool_calls=tool_calls,
            pending_actions=pending,
            raw_stop_reason="fallback",
        )

    # Owner-portfolio: "show me bob's accounts" / "alice's portfolio"
    owners = {"alice", "bob", "carol"}
    matched_owner = next((o for o in owners if o in q), None)
    if matched_owner and any(k in q for k in ("account", "portfolio", "book", "deals", "show")):
        result = _tool_search_accounts(conn, {"query": matched_owner, "limit": 10})
        tool_calls.append({"name": "search_accounts", "input": {"query": matched_owner}})
        names = ", ".join(f"{a['name']} ({a['id']})" for a in result["accounts"]) or "none"
        return AgentResponse(
            answer=f"[FALLBACK MODE — {reason}] {matched_owner}'s accounts: {names}.",
            tool_calls=tool_calls,
            raw_stop_reason="fallback",
        )

    if "at risk" in q or "risk" in q:
        result = _tool_list_at_risk(conn, {})
        tool_calls.append({"name": "list_at_risk", "input": {}})
        names = ", ".join(f"{a['name']} ({a['id']}, health {a['health_score']})" for a in result["accounts"])
        return AgentResponse(
            answer=f"[FALLBACK MODE — {reason}] {len(result['accounts'])} accounts at risk: {names}.",
            tool_calls=tool_calls,
            raw_stop_reason="fallback",
        )

    if "renew" in q:
        days = 60
        for d in (30, 60, 90, 180):
            if str(d) in q:
                days = d
                break
        result = _tool_list_renewals(conn, {"days": days})
        tool_calls.append({"name": "list_renewals", "input": {"days": days}})
        names = ", ".join(
            f"{a['name']} ({a['id']}, in {a['renewal_in_days']}d, health {a['health_score']})"
            for a in result["accounts"]
        )
        return AgentResponse(
            answer=f"[FALLBACK MODE — {reason}] {len(result['accounts'])} accounts renew within {days}d: {names}.",
            tool_calls=tool_calls,
            raw_stop_reason="fallback",
        )

    # Account-lookup fallback: try each capitalized word individually as a
    # search hint; first hit wins. Skip leading contractions and very
    # short / common tokens (I, A, This, That).
    _STOP = {"i", "a", "this", "that", "the", "my", "your", "their"}
    candidates = [
        t.strip(",.?!:;'\"")
        for t in question.split()
        if t and t[0].isupper() and not t.lower().startswith("what")
    ]
    candidates = [c for c in candidates if len(c) >= 2 and c.lower() not in _STOP]
    search = {"accounts": []}
    hint = candidates[0] if candidates else question[:20]
    for c in candidates:
        result = _tool_search_accounts(conn, {"query": c, "limit": 1})
        if result["accounts"]:
            search = result
            hint = c
            break
    tool_calls.append({"name": "search_accounts", "input": {"query": hint}})
    # Ambiguous: vague pronoun reference like "that account" with no nouns.
    vague_markers = ("that account", "yesterday", "the one we", "earlier")
    if not search["accounts"] and any(m in q for m in vague_markers):
        return AgentResponse(
            answer=(
                f"[FALLBACK MODE — {reason}] Which account did you mean? "
                "Specify the company name or account id (e.g., acc_acme)."
            ),
            tool_calls=tool_calls,
            raw_stop_reason="fallback",
        )
    if not search["accounts"]:
        return AgentResponse(
            answer=f"[FALLBACK MODE — {reason}] No accounts matched {hint!r}. Try a more specific name.",
            tool_calls=tool_calls,
            raw_stop_reason="fallback",
        )
    acct = search["accounts"][0]
    ctx = _tool_get_account_context(conn, {"account_id": acct["id"]})
    tool_calls.append({"name": "get_account_context", "input": {"account_id": acct["id"]}})
    a = ctx["account"]
    latest_note = ctx["notes"][0]["body"] if ctx["notes"] else "no recent notes"
    return AgentResponse(
        answer=(
            f"[FALLBACK MODE — {reason}] {a['name']} ({a['id']}): {a['plan']} plan, "
            f"${a['mrr_cents'] / 100:.0f} MRR, renews in {ctx['renewal_in_days']}d, "
            f"health {a['health_score']}. Latest note: {latest_note}"
        ),
        tool_calls=tool_calls,
        raw_stop_reason="fallback",
    )
