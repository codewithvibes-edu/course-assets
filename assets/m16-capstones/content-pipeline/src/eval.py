"""
Eval set for the clip scorer. Each case has a segment + an expected
score range. The scorer should fall inside the range. Captures the
intent ("this should score high") without forcing a single integer.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from .agents import clip_scorer
from .data import SAMPLE_SEGMENTS, Segment


@dataclass
class EvalCase:
    segment: Segment
    min_score: int
    max_score: int
    note: str


CASES: list[EvalCase] = [
    EvalCase(
        segment=SAMPLE_SEGMENTS[0],  # tight + on-thesis
        min_score=7,
        max_score=10,
        note="opening hook; tight delivery",
    ),
    EvalCase(
        segment=SAMPLE_SEGMENTS[1],  # data-layer thesis
        min_score=7,
        max_score=10,
        note="strong on-thesis claim",
    ),
    EvalCase(
        segment=SAMPLE_SEGMENTS[2],  # diagnostic test
        min_score=6,
        max_score=10,
        note="practical test the reader can apply",
    ),
    EvalCase(
        segment=SAMPLE_SEGMENTS[3],  # filler
        min_score=1,
        max_score=4,
        note="filler-heavy; should be flagged",
    ),
]


def run_eval(verbose: bool = False) -> dict:
    passed = 0
    failures: list[dict] = []
    for case in CASES:
        score = clip_scorer(case.segment).score
        if case.min_score <= score <= case.max_score:
            passed += 1
            if verbose:
                print(f"  [PASS] {case.segment.id} scored {score} ({case.note})")
        else:
            failures.append(
                {
                    "segment_id": case.segment.id,
                    "expected_range": [case.min_score, case.max_score],
                    "got": score,
                    "note": case.note,
                }
            )
            if verbose:
                print(
                    f"  [FAIL] {case.segment.id} scored {score} "
                    f"(expected {case.min_score}-{case.max_score})"
                )

    return {"total": len(CASES), "passed": passed, "failures": failures}


if __name__ == "__main__":
    result = run_eval(verbose=True)
    print()
    print(f"Pass rate: {result['passed']}/{result['total']}")
    sys.exit(0 if result["passed"] == result["total"] else 1)
