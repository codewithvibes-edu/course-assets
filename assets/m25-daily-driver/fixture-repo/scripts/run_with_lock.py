"""Overlap-lock wrapper. Runs a command under a lockfile so a second
trigger during a live run does what the POLICY says instead of what
chaos prefers.

    python3 scripts/run_with_lock.py --policy skip -- python3 scripts/repo_check.py --run-id sched-001

Policies:
- skip: if the lock is held, exit immediately with a skipped notice
  (exit 3). Right for jobs where a fresh run supersedes a queued one.
- queue: wait for the lock, then run. Right for jobs where every trigger
  must eventually execute exactly once.

The lockfile records the holder's pid and start time, and a stale lock
(holder no longer running) is broken with a notice: a crashed run must
not deadlock tomorrow's schedule.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
LOCK = ROOT / "state" / "repo-check.lock"


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False
    except OSError:
        return False


def try_acquire():
    LOCK.parent.mkdir(exist_ok=True)
    try:
        # O_EXCL: creation is the atomic test-and-set. No check-then-create race.
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        holder = json.loads(LOCK.read_text()) if LOCK.exists() else {}
        if holder and not pid_alive(holder.get("pid", -1)):
            print(f"[lock] stale lock from dead pid {holder.get('pid')}; breaking it.")
            LOCK.unlink(missing_ok=True)
            return try_acquire()
        return None
    with os.fdopen(fd, "w") as f:
        json.dump({"pid": os.getpid(), "started": time.strftime("%H:%M:%S")}, f)
    return LOCK


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", choices=["skip", "queue"], required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="-- then the command to run under the lock")
    args = parser.parse_args()
    command = [c for c in args.command if c != "--"]
    if not command:
        print("usage: run_with_lock.py --policy skip|queue -- <command...>")
        return 2

    acquired = try_acquire()
    if acquired is None:
        if args.policy == "skip":
            holder = json.loads(LOCK.read_text())
            print(f"[lock] held by pid {holder['pid']} since {holder['started']}; "
                  "policy=skip, exiting without running. This is the policy "
                  "working, not a failure.")
            return 3
        print("[lock] held; policy=queue, waiting...")
        while acquired is None:
            time.sleep(0.5)
            acquired = try_acquire()
        print("[lock] acquired after wait.")

    try:
        return subprocess.run(command).returncode
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
