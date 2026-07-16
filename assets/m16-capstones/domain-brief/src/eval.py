"""
Eval set for the brief generator. Two flavors of check:
  - structural: every brief contains the required sections
  - linter: claims-linter sweep on synthetic adversarial inputs

The linter harness runs the validator against drafts that try to slip
unsupported claims past it; we expect the validator to catch them.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from .agents import generate_daily_brief, validate_brief
from .data import load_today_context


REQUIRED_SECTIONS = [
    "What got filed",
    "Projects that moved",
    "Projects that stalled",
    "Similar stretches",
    "What to watch",
    "Data gaps",
]


@dataclass
class LinterCase:
    name: str
    text: str
    expect_failures: bool


LINTER_CASES: list[LinterCase] = [
    LinterCase(
        name="clean_brief_passes",
        text=(
            "Meridian Commons Development LLC filed a six-story mixed-use "
            "under P-2026-01184 in Riverfront. "
            "Data gaps: none today; the permit feed loaded in full."
        ),
        expect_failures=False,
    ),
    LinterCase(
        name="superlative_blocked",
        text=(
            "A record-breaking week for Riverfront filings, per P-2026-01184. "
            "Data gaps: none today."
        ),
        expect_failures=True,
    ),
    LinterCase(
        name="uncited_business_blocked",
        text=(
            "Ridgeline Builders Inc broke ground on the Airport Corridor hotel. "
            "Data gaps: none today."
        ),
        expect_failures=True,
    ),
    LinterCase(
        name="missing_gap_disclosure_blocked",
        text="Quiet day. Two small tenant-improvement filings downtown (P-2026-01190).",
        expect_failures=True,
    ),
    LinterCase(
        name="largest_claim_blocked",
        text=(
            "P-2026-01184 is the largest filing this metro has ever seen. "
            "Data gaps: none today."
        ),
        expect_failures=True,
    ),
]


def run_eval(verbose: bool = False) -> dict:
    failures: list[str] = []

    # Structural: today's generated brief contains every required section.
    ctx = load_today_context()
    brief = generate_daily_brief(ctx)
    for section in REQUIRED_SECTIONS:
        if section.lower() not in brief.body.lower():
            failures.append(f"structural: missing section '{section}'")
        elif verbose:
            print(f"  [PASS] structural: '{section}' present")

    # Linter: validator behavior on adversarial inputs.
    for case in LINTER_CASES:
        actual = validate_brief(case.text)
        had_failures = bool(actual)
        if had_failures != case.expect_failures:
            failures.append(
                f"linter: {case.name} expected_failures={case.expect_failures}, "
                f"got_failures={had_failures}"
            )
        elif verbose:
            print(f"  [PASS] linter: {case.name}")

    total = len(REQUIRED_SECTIONS) + len(LINTER_CASES)
    return {
        "total": total,
        "passed": total - len(failures),
        "failures": failures,
    }


if __name__ == "__main__":
    result = run_eval(verbose=True)
    print()
    print(f"Pass rate: {result['passed']}/{result['total']}")
    if result["failures"]:
        for f in result["failures"]:
            print(f"  - {f}")
        sys.exit(1)
