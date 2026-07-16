"""End-to-end walkthrough of the CRM intelligence assistant."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents import respond


SAMPLE_QUESTIONS = [
    "what's the latest with ACME",
    "give me a summary on Nimble",
    "which accounts renew within 60 days",
    "which accounts are at risk right now",
    "draft a renewal email to ACME",
]


def main():
    for q in SAMPLE_QUESTIONS:
        print(f">>> {q}")
        response = respond(q)
        print(response.answer)
        if response.pending_action:
            print(f"   [pending_action] {json.dumps(response.pending_action)}")
        print()


if __name__ == "__main__":
    main()
