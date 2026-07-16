"""
CLI for the domain intelligence daily brief generator.

Usage:
    python -m src.main             # generate today's brief
    python -m src.main --validate  # generate then run the claims linter
"""

from __future__ import annotations

import argparse
import sys

from .agents import generate_daily_brief
from .data import load_today_context


def main() -> int:
    parser = argparse.ArgumentParser(description="Domain intelligence daily brief generator")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Print claims-linter failures (superlatives, uncited businesses, missing gap disclosure)",
    )
    args = parser.parse_args()

    ctx = load_today_context()
    brief = generate_daily_brief(ctx)

    print(f"# {brief.title}")
    print()
    print(brief.body)
    print()
    print(f"_Confidence: {brief.confidence:.2f}; needs_human_review: {brief.needs_human_review}_")

    if args.validate:
        print()
        if brief.validation_failures:
            print("LINTER FAILURES:")
            for f in brief.validation_failures:
                print(f"  - {f}")
            return 1
        print("Linter: passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
