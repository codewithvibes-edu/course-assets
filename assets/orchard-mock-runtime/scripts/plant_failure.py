#!/usr/bin/env python3
"""Plant a known failure so you can practice the recovery with the answer
already in your pocket.

A real stale artifact lock shows up at the worst possible time: mid-pull,
on a slow connection, on a machine you were about to stop using. Practicing
recovery then is expensive. Practicing it here costs nothing, and the
recovery command is identical.

    python3 scripts/plant_failure.py stale-artifact-lock \\
        --state-dir .orchard-runtime --model orchard-3b-instruct

Then run the pull twice: once to watch it refuse, once with
--recover-stale-lock to watch it recover.

Everything here is a mock fixture. No real process is signaled, no real
artifact exists, and no weights are involved.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def dead_pid():
    """A process ID that is definitely not running: start a trivial child,
    wait for it to exit, then confirm the ID is gone before handing it back.
    Guessing a high number and hoping would be the kind of shortcut this
    course keeps telling you not to take."""
    for _ in range(20):
        process = subprocess.Popen([sys.executable, "-c", "pass"])
        process.wait()
        if not _alive(process.pid):
            return process.pid
    raise SystemExit("MOCK ERROR mock_plant_failed could not obtain a dead "
                     "fixture pid on this machine")


def _alive(pid):
    try:
        os.kill(int(pid), 0)
    except (OSError, ValueError):
        return False
    return True


def plant_stale_artifact_lock(state_dir, model):
    target = Path(state_dir) / "artifacts" / model
    target.mkdir(parents=True, exist_ok=True)
    pid = dead_pid()
    lock = target / ".lock"
    lock.write_text(json.dumps({
        "mock": True,
        "model": model,
        "pid": pid,
        "planted": True,
        "note": "Planted stale mock lock. The named pid has already exited.",
    }, indent=2) + "\n")
    print(f"MOCK planted stale-artifact-lock model={model} pid={pid} pid_alive=false")
    print(f"MOCK lock={state_dir}/artifacts/{model}/.lock")
    print("MOCK next: run the pull, watch it refuse with exit code 5, then "
          "pull again with --recover-stale-lock")


def main():
    parser = argparse.ArgumentParser(prog="plant_failure.py")
    parser.add_argument("failure", choices=["stale-artifact-lock"])
    parser.add_argument("--state-dir", default=".orchard-runtime")
    parser.add_argument("--model", default="orchard-3b-instruct")
    args = parser.parse_args()
    if args.failure == "stale-artifact-lock":
        plant_stale_artifact_lock(args.state_dir, args.model)
    return 0


if __name__ == "__main__":
    sys.exit(main())
