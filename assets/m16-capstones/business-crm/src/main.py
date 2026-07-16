"""
CLI entry point for the CRM intelligence assistant.

Usage:
    python -m src.main "what's the latest with ACME"
    python -m src.main --renewals 60
    python -m src.main --at-risk
"""

from __future__ import annotations

import argparse
import json
import sys

from . import data
from .agents import respond


def main() -> int:
    parser = argparse.ArgumentParser(description="CRM intelligence assistant")
    parser.add_argument("question", nargs="?", default=None)
    parser.add_argument(
        "--renewals",
        type=int,
        help="Shortcut: list accounts renewing within N days",
    )
    parser.add_argument(
        "--at-risk",
        action="store_true",
        help="Shortcut: list accounts with health score below threshold",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Print structured response as JSON instead of plain text",
    )
    args = parser.parse_args()

    # Shortcuts run the portfolio specialist directly.
    if args.renewals is not None:
        question = f"Which accounts renew within {args.renewals} days?"
    elif args.at_risk:
        question = "Which accounts are at risk?"
    elif args.question:
        question = args.question
    else:
        parser.print_help()
        return 2

    response = respond(question)
    if args.as_json:
        print(
            json.dumps(
                {
                    "answer": response.answer,
                    "citations": response.citations,
                    "pending_action": response.pending_action,
                },
                indent=2,
            )
        )
    else:
        print(response.answer)
        if response.citations:
            print()
            print(f"Citations: {len(response.citations)} field(s) referenced.")
        if response.pending_action:
            print()
            print("Pending action (HUMAN APPROVAL REQUIRED):")
            print(json.dumps(response.pending_action, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
