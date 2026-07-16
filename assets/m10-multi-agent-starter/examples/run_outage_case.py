"""
Worked example: a technical outage ticket. The supervisor classifies as
technical, routes to the technical specialist, which checks service
status and surfaces the matching runbook.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents import (
    SupportState,
    classify_and_route,
    technical_specialist,
)


def main():
    initial: SupportState = {
        "user_input": "I'm getting 502 errors on the web app every few requests.",
        "customer_email": "bob@example.com",
        "trace": [],
    }

    after_supervisor = classify_and_route(initial)
    final = technical_specialist(after_supervisor)

    print("=== Classification ===")
    print(f"  {final.get('classification')} (confidence {final.get('classification_confidence', 0):.2f})")

    print("\n=== Final answer ===")
    print(final.get("final_answer"))

    print("\n=== Trace ===")
    for entry in final.get("trace", []):
        print(f"  [{entry['agent']}] {entry['action']}")


if __name__ == "__main__":
    main()
