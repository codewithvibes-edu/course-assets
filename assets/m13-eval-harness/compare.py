"""
Compare a current eval run against a baseline. Exits non-zero if the
regression exceeds a threshold so this can gate CI merges.

Usage:
    python compare.py --baseline baseline.json --current results.json
    python compare.py --baseline ... --current ... --max-regression 0.05
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two eval runs.")
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--current", required=True, type=Path)
    parser.add_argument(
        "--max-regression",
        type=float,
        default=0.05,
        help="Maximum allowed pass-rate drop before exiting non-zero (default 5%%).",
    )
    args = parser.parse_args()

    for path in (args.baseline, args.current):
        if not path.exists():
            print(f"Missing: {path}", file=sys.stderr)
            return 2

    baseline = json.loads(args.baseline.read_text())
    current = json.loads(args.current.read_text())

    base_rate = baseline.get("pass_rate", 0.0)
    cur_rate = current.get("pass_rate", 0.0)
    delta = cur_rate - base_rate

    print(f"Baseline pass rate: {base_rate:.0%}")
    print(f"Current pass rate:  {cur_rate:.0%}")
    print(f"Delta:              {delta:+.1%}")
    print()

    # Per-case diff
    base_results = {r["case_id"]: r for r in baseline.get("results", [])}
    cur_results = {r["case_id"]: r for r in current.get("results", [])}

    regressions: list[str] = []
    fixes: list[str] = []
    for case_id in sorted(set(base_results) | set(cur_results)):
        b = base_results.get(case_id)
        c = cur_results.get(case_id)
        if b and c:
            if b["passed"] and not c["passed"]:
                regressions.append(case_id)
            elif not b["passed"] and c["passed"]:
                fixes.append(case_id)

    if regressions:
        print(f"Regressions ({len(regressions)}):")
        for case_id in regressions:
            print(f"  - {case_id}")
    if fixes:
        print(f"Newly passing ({len(fixes)}):")
        for case_id in fixes:
            print(f"  + {case_id}")

    if -delta > args.max_regression:
        print(
            f"\nFAIL: pass rate dropped by {-delta:.1%} > "
            f"max_regression={args.max_regression:.1%}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
