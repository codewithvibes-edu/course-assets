"""
End-to-end example for the domain intelligence daily brief generator.

Wires data_layer -> agent -> eval_set. Runs without an API key (uses
the deterministic fallback in agent.py); set ANTHROPIC_API_KEY for the
real Anthropic Messages API calls.

Usage:
    python example.py            # generate today's brief
    python example.py --eval     # run eval_set.yaml
    python example.py --validate # exit nonzero on claims-linter failures

This is educational reference code for the running example: commercial
construction permits in one metro area.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml

from agent import (
    Brief,
    generate_daily_brief,
    validate_brief,
)
from data_layer import build_store, known_permit_ids, load_today_context


def _print_brief(brief: Brief) -> None:
    print(f"# {brief.title}")
    print()
    print(brief.body)
    print()
    print(f"_Confidence: {brief.confidence:.2f}; needs_human_review: {brief.needs_human_review}_")
    if brief.validation_failures:
        print()
        print("LINTER FAILURES (would block publish):")
        for f in brief.validation_failures:
            print(f"  - {f}")


def _check_case(case: dict, conn) -> tuple[bool, list]:
    criteria = case.get("pass_criteria") or {}
    kind = case.get("kind", "structural")
    failures: list = []

    if kind == "structural":
        ctx = load_today_context(conn)
        brief = generate_daily_brief(ctx)
        body = brief.body
        for s in criteria.get("brief_must_contain_all", []) or []:
            if s.lower() not in body.lower():
                failures.append(f"missing required section text: {s!r}")
        for w in criteria.get("brief_must_not_contain_words", []) or []:
            if w.lower() in body.lower():
                failures.append(f"contains forbidden phrasing: {w!r}")
        count_check = criteria.get("brief_must_contain_min_count")
        if count_check:
            actual = body.lower().count(count_check["substring"].lower())
            if actual < count_check["count"]:
                failures.append(
                    f"substring {count_check['substring']!r} appears {actual}x, need {count_check['count']}"
                )
        if "needs_human_review" in criteria and brief.needs_human_review != criteria["needs_human_review"]:
            failures.append(
                f"needs_human_review={brief.needs_human_review}, expected {criteria['needs_human_review']}"
            )
        return (len(failures) == 0, failures)

    if kind == "linter":
        text = case["input"]
        validation = validate_brief(text, known_permit_ids(conn))
        expected = criteria.get("expect_validation_failures", False)
        actual = bool(validation)
        if actual != expected:
            failures.append(
                f"expected_validation_failures={expected}, got_validation_failures={actual} ({validation})"
            )
        return (len(failures) == 0, failures)

    return False, [f"unknown case kind: {kind}"]


def run_eval(path: Path) -> int:
    suite = yaml.safe_load(path.read_text(encoding="utf-8"))
    print(f"=== Eval suite: {suite.get('suite', 'unknown')} ===")
    conn = build_store()
    cases = suite.get("cases", []) or []
    passed = 0
    failed: list = []
    for case in cases:
        ok, failures = _check_case(case, conn)
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {case['id']}")
        if ok:
            passed += 1
        else:
            failed.append({"id": case["id"], "failures": failures})
            for f in failures:
                print(f"      - {f}")
    print()
    print(f"Pass rate: {passed}/{len(cases)}")
    return 0 if not failed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Domain brief capstone example")
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    if args.eval:
        return run_eval(Path(__file__).resolve().parent / "eval_set.yaml")

    conn = build_store()
    ctx = load_today_context(conn)
    brief = generate_daily_brief(ctx)

    print("=== Daily brief generator walkthrough ===")
    print("(set ANTHROPIC_API_KEY to run against the real model; otherwise fallback mode)")
    print()
    _print_brief(brief)

    if args.validate and brief.validation_failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
