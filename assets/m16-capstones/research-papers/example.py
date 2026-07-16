"""
End-to-end example for the research-papers assistant capstone.

Wires data_layer -> agent -> eval_set. Runs without an API key (uses
the deterministic fallback in agent.py); set ANTHROPIC_API_KEY for the
real Anthropic Messages API tool-use loop.

Usage:
    python example.py                              # walkthrough
    python example.py --eval                       # run eval_set.yaml
    python example.py --query "what does the lit say about reranking?"
    python example.py --list                       # show indexed papers
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml

from agent import SynthesisResult, synthesize, validate_citations
from data_layer import (
    all_papers,
    build_store,
    known_paper_ids,
    search_library,
)


SAMPLE_QUESTIONS = [
    "What does the literature say about hybrid retrieval?",
    "Is reranking actually worth the cost?",
    "How should I chunk long technical documents?",
]


def _print_result(question: str, r: SynthesisResult) -> None:
    print(f">>> {question}")
    print()
    print(r.answer)
    print()
    if r.tool_calls:
        names = ", ".join(c["name"] for c in r.tool_calls)
        print(f"   [tools called: {names}]")
    if r.cited_paper_ids:
        print(f"   [cited: {', '.join(r.cited_paper_ids)}]")
    if r.validation_failures:
        print("   [VALIDATION FAILURES (would block publish):]")
        for f in r.validation_failures:
            print(f"     - {f}")
    print()


def _check_case(case: dict, conn) -> tuple[bool, list]:
    kind = case.get("kind", "retrieval")
    criteria = case.get("pass_criteria") or {}
    failures: list = []

    if kind == "retrieval":
        papers = search_library(conn, case["input"]["question"], top_k=5)
        retrieved_ids = {p.id for p in papers}
        expected_any = set(criteria.get("expected_paper_ids_any", []) or [])
        if expected_any and not (expected_any & retrieved_ids):
            failures.append(
                f"none of expected paper IDs surfaced: {sorted(expected_any)} (got {sorted(retrieved_ids)})"
            )
        return (len(failures) == 0, failures)

    if kind == "citation_validation":
        text = case["input"]["text"]
        result = validate_citations(text, known_paper_ids(conn))
        actual = bool(result)
        expected = criteria.get("expect_validation_failures", False)
        if actual != expected:
            failures.append(
                f"expected_validation_failures={expected}, got_validation_failures={actual} ({result})"
            )
        return (len(failures) == 0, failures)

    if kind == "end_to_end":
        result = synthesize(case["input"]["question"], conn)
        if "min_citations" in criteria and len(result.cited_paper_ids) < criteria["min_citations"]:
            failures.append(
                f"only {len(result.cited_paper_ids)} citations; need {criteria['min_citations']}"
            )
        if criteria.get("no_unknown_citations") and result.validation_failures:
            failures.append(f"validation_failures present: {result.validation_failures}")
        for s in criteria.get("answer_must_contain", []) or []:
            if s.lower() not in result.answer.lower():
                failures.append(f"answer missing required substring: {s!r}")
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
    parser = argparse.ArgumentParser(description="Research-papers capstone example")
    parser.add_argument("--eval", action="store_true")
    parser.add_argument("--query", type=str)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if args.eval:
        return run_eval(Path(__file__).resolve().parent / "eval_set.yaml")

    conn = build_store()
    if args.list:
        for p in all_papers(conn):
            authors = ", ".join(p.authors) if p.authors else "unknown"
            print(f"  ({p.id}) {p.title} — {authors} ({p.year}, {p.venue})")
        return 0

    if args.query:
        r = synthesize(args.query, conn)
        _print_result(args.query, r)
        return 1 if r.validation_failures else 0

    print("=== Research-papers assistant walkthrough ===")
    print("(set ANTHROPIC_API_KEY to run against the real model; otherwise fallback mode)")
    print()
    for q in SAMPLE_QUESTIONS:
        r = synthesize(q, conn)
        _print_result(q, r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
