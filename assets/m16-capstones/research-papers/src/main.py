"""
CLI for the research-papers assistant.

Usage:
    python -m src.main "what does the literature say about hybrid retrieval"
    python -m src.main --list  # show all indexed papers
"""

from __future__ import annotations

import argparse
import sys

from .agents import synthesize
from .data import load_library


def main() -> int:
    parser = argparse.ArgumentParser(description="Research-papers assistant")
    parser.add_argument("question", nargs="?", default=None)
    parser.add_argument("--list", action="store_true", help="List all indexed papers")
    args = parser.parse_args()

    if args.list:
        for p in load_library():
            print(f"  ({p.id}) {p.title} — {', '.join(p.authors)} ({p.year}, {p.venue})")
        return 0

    if not args.question:
        parser.print_help()
        return 2

    result = synthesize(args.question)
    print(result.answer)

    if result.validation_failures:
        print()
        print("VALIDATION FAILURES (citation problems):")
        for f in result.validation_failures:
            print(f"  - {f}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
