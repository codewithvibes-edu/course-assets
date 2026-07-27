"""The local notification sink. Real deployments notify a phone or a
channel; this fixture appends structured lines to notifications.log so
the notification CONTRACT is testable without any account or network.

    python3 scripts/notify.py --run-id sched-001 --outcome findings \
        --evidence reports/sched-001.json --next "review findings"

Contract enforced here (the module's rule, in code): a notification
carries run ID, outcome, evidence location, and next action. It never
carries secrets or a transcript, and this script has no argument that
would let one in by accident.
"""

import argparse
import json
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUTCOMES = ["clean", "findings", "degraded", "missed", "retry_exhausted", "disabled", "recovered"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--outcome", choices=OUTCOMES, required=True)
    parser.add_argument("--evidence", required=True,
                        help="path to the artifact backing this notification")
    parser.add_argument("--next", dest="next_action", required=True,
                        help="what the human should do, one clause")
    args = parser.parse_args()

    line = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "run_id": args.run_id,
        "outcome": args.outcome,
        "evidence": args.evidence,
        "next_action": args.next_action,
    }
    log = ROOT / "notifications.log"
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
    print(f"[notify] {args.outcome}: {args.run_id} -> {log.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
