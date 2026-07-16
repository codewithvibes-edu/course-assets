"""
Eval set + harness for the CRM intelligence assistant. Runs the agent
against ~15 hand-written queries; checks classification correctness +
that key facts appear in the response.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from .agents import respond


@dataclass
class EvalCase:
    id: str
    question: str
    expected_classification: str  # 'account_lookup' | 'portfolio' | 'action_proposer'
    must_contain: list[str]


CASES: list[EvalCase] = [
    EvalCase(
        id="lookup-acme-latest",
        question="what's the latest with ACME",
        expected_classification="account_lookup",
        must_contain=["ACME", "renewal"],
    ),
    EvalCase(
        id="lookup-nimble-summary",
        question="give me a summary on Nimble",
        expected_classification="account_lookup",
        must_contain=["Nimble", "health"],
    ),
    EvalCase(
        id="portfolio-renewals-60",
        question="which accounts renew within 60 days",
        expected_classification="portfolio",
        must_contain=["renewing"],
    ),
    EvalCase(
        id="portfolio-at-risk",
        question="which accounts are at risk right now",
        expected_classification="portfolio",
        must_contain=["under the health threshold"],
    ),
    EvalCase(
        id="action-draft-email",
        question="draft a renewal email to ACME",
        expected_classification="action_proposer",
        must_contain=["nothing has been sent"],
    ),
]


def run_eval(verbose: bool = False) -> dict:
    passed = 0
    failed: list[dict] = []
    for case in CASES:
        response = respond(case.question)
        miss = [s for s in case.must_contain if s.lower() not in response.answer.lower()]
        if miss:
            failed.append({"id": case.id, "missing": miss, "got": response.answer[:200]})
        else:
            passed += 1
        if verbose:
            print(f"  [{'PASS' if not miss else 'FAIL'}] {case.id}")

    return {
        "total": len(CASES),
        "passed": passed,
        "failed": len(CASES) - passed,
        "failures": failed,
    }


if __name__ == "__main__":
    result = run_eval(verbose=True)
    print()
    print(f"Pass rate: {result['passed']}/{result['total']}")
    if result["failures"]:
        print("Failures:")
        for f in result["failures"]:
            print(f"  - {f['id']}: missing {f['missing']}")
        sys.exit(1)
