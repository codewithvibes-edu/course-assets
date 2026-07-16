"""
End-to-end example for the CRM intelligence assistant.

Wires data_layer -> agent -> eval_set. Runs without an API key (uses
the deterministic fallback in agent.py); set ANTHROPIC_API_KEY to
exercise the real Anthropic Messages API tool-use loop.

Usage:
    python example.py             # run sample questions
    python example.py --eval      # run eval_set.yaml
    python example.py --query "..."  # ask a one-off question
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make sibling modules importable when running `python example.py` from
# anywhere or via `python -m`.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml

from agent import AgentResponse, run_agent
from data_layer import build_store


SAMPLE_QUESTIONS = [
    "What's the latest with ACME?",
    "Which accounts renew within 60 days?",
    "Which accounts are at risk right now?",
    "Draft a renewal check-in email to Juniper",
]


def _print_response(question: str, response: AgentResponse) -> None:
    print(f">>> {question}")
    print(response.answer)
    if response.tool_calls:
        names = ", ".join(c["name"] for c in response.tool_calls)
        print(f"   [tools called: {names}]")
    for pa in response.pending_actions:
        print(f"   [PENDING ACTION — needs human review] {pa['action_type']}: {pa['summary']}")
    print()


def _check_case(case: dict, response: AgentResponse) -> tuple[bool, list[str]]:
    """Apply pass_criteria from a single eval case. Returns (passed, failures)."""
    criteria = case.get("pass_criteria") or {}
    failures: list[str] = []
    answer_lower = response.answer.lower()
    called = {c["name"] for c in response.tool_calls}

    for needle in criteria.get("must_contain_all", []) or []:
        if needle.lower() not in answer_lower:
            failures.append(f"missing required substring: {needle!r}")

    must_any = criteria.get("must_contain_any") or []
    if must_any and not any(n.lower() in answer_lower for n in must_any):
        failures.append(f"none of any-of substrings present: {must_any!r}")

    must_phrases = criteria.get("must_contain_any_phrases") or []
    if must_phrases and not any(p.lower() in answer_lower for p in must_phrases):
        failures.append(f"none of phrases present: {must_phrases!r}")

    tools_any = criteria.get("tools_called_any") or []
    if tools_any and not (set(tools_any) & called):
        failures.append(f"none of expected tools called: {tools_any!r} (called: {sorted(called)})")

    pending_min = criteria.get("pending_actions_min")
    if pending_min is not None and len(response.pending_actions) < pending_min:
        failures.append(f"expected at least {pending_min} pending actions; got {len(response.pending_actions)}")

    return (len(failures) == 0, failures)


def run_eval(eval_path: Path) -> int:
    suite = yaml.safe_load(eval_path.read_text(encoding="utf-8"))
    print(f"=== Eval suite: {suite.get('suite', 'unknown')} ===")
    conn = build_store()
    passed = 0
    failed_cases: list[dict] = []
    cases = suite.get("cases", []) or []
    for case in cases:
        response = run_agent(case["input"], conn)
        ok, failures = _check_case(case, response)
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {case['id']}")
        if ok:
            passed += 1
        else:
            failed_cases.append({"id": case["id"], "failures": failures, "answer": response.answer[:200]})
            for f in failures:
                print(f"      - {f}")
    print()
    print(f"Pass rate: {passed}/{len(cases)}")
    if failed_cases:
        print()
        print("Failure detail:")
        for fc in failed_cases:
            print(f"  - {fc['id']}: {fc['failures']}")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CRM intelligence capstone example")
    parser.add_argument("--eval", action="store_true", help="Run the YAML eval set")
    parser.add_argument("--query", type=str, help="Ask a single question")
    parser.add_argument(
        "--json", dest="as_json", action="store_true", help="Emit JSON instead of plain text"
    )
    args = parser.parse_args()

    if args.eval:
        return run_eval(Path(__file__).resolve().parent / "eval_set.yaml")

    conn = build_store()

    if args.query:
        response = run_agent(args.query, conn)
        if args.as_json:
            print(
                json.dumps(
                    {
                        "answer": response.answer,
                        "tool_calls": response.tool_calls,
                        "pending_actions": response.pending_actions,
                    },
                    indent=2,
                )
            )
        else:
            _print_response(args.query, response)
        return 0

    # Default: walk through the sample questions.
    print("=== CRM intelligence assistant walkthrough ===")
    print("(set ANTHROPIC_API_KEY to run against the real model; otherwise fallback mode)")
    print()
    for q in SAMPLE_QUESTIONS:
        response = run_agent(q, conn)
        _print_response(q, response)
    return 0


if __name__ == "__main__":
    sys.exit(main())
