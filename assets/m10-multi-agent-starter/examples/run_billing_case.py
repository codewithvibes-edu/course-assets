"""
Worked example: a billing duplicate-charge ticket. The supervisor
classifies it as billing, routes to the billing specialist, which
proposes a refund and waits for human approval.

Runs without LangGraph installed by calling the node functions directly.
For the LangGraph-compiled version, see graph.run().
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents import (
    SupportState,
    billing_specialist,
    classify_and_route,
)


def main():
    initial: SupportState = {
        "user_input": "My card was charged twice for the same plan this month.",
        "customer_email": "alice@example.com",
        "trace": [],
    }

    after_supervisor = classify_and_route(initial)
    final = billing_specialist(after_supervisor)

    print("=== Final state ===")
    print(json.dumps(
        {k: v for k, v in final.items() if k != "trace"},
        default=str,
        indent=2,
    ))

    print("\n=== Trace ===")
    for entry in final.get("trace", []):
        print(f"  [{entry['agent']}] {entry['action']}: {{ {', '.join(f'{k}={v}' for k, v in entry.items() if k not in ('ts', 'agent', 'action'))} }}")

    if final.get("pending_action"):
        print("\n=== Pending action (HUMAN APPROVAL REQUIRED) ===")
        print(json.dumps(final["pending_action"], indent=2, default=str))


if __name__ == "__main__":
    main()
