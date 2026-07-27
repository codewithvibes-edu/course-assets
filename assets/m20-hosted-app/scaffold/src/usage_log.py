"""Usage logging with a privacy default: the log records that a request
happened and what it cost, never what it said. Prompt and output content
stay out unless the application contract explicitly reclassifies them,
in writing, with a reason. Grep this log for 'content' and find nothing:
that is the test, and tests/test_contract.py runs it.
"""

import json
import time
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"


def record(route, model, latency_s, usage, request_id, outcome,
           estimated_cost=None, log_dir=None):
    """Append one JSON line to logs/usage.jsonl. Fields only; no content."""
    directory = Path(log_dir) if log_dir else LOG_DIR
    directory.mkdir(exist_ok=True)
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "route": route,
        "model": model,
        "latency_s": round(latency_s, 3),
        "usage": usage or {},
        "estimated_cost": estimated_cost,  # None when no price sheet is configured
        "request_id": request_id,
        "outcome": outcome,  # ok | auth | rate_limit | bad_input | server | timeout | network | malformed | canceled
    }
    path = directory / "usage.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry
