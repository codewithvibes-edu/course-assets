"""The prepared long-running fixture: a 10-step job that checkpoints
after every step, heartbeats while alive, dies politely, and resumes
from where it stopped. Everything the background and recovery lessons
need to be TESTABLE lives in this one file.

    python3 scripts/slow_task.py --run-id bg-001                # fresh run
    python3 scripts/slow_task.py --run-id bg-001 --resume       # continue
    python3 scripts/slow_task.py --run-id bg-001 --fail-after 6 # planted failure

Behavior contract (the module quizzes you on reading this):
- Each step takes ~2 seconds. Progress checkpoints to state/<run-id>.checkpoint.json
  AFTER each completed step, atomically (write temp, rename).
- A heartbeat line lands in state/<run-id>.heartbeat every step, so an
  outside observer can tell alive from hung without guessing.
- SIGINT / SIGTERM between steps = clean stop at the last checkpoint.
  No orphan temp files, no half-written output.
- --resume continues from the checkpoint instead of restarting. Completed
  steps are never redone: side effects (one output line per step in
  output/<run-id>.log) do not duplicate. That is the idempotency proof.
- --fail-after N raises after step N checkpoints, simulating a crash for
  the retry-from-checkpoint drill.
"""

import argparse
import json
import os
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
TOTAL_STEPS = 10
STEP_SECONDS = 2

_stop_requested = False


def request_stop(signum, frame):
    global _stop_requested
    _stop_requested = True
    print(f"[slow-task] stop requested (signal {signum}); "
          "finishing current step, then checkpointing.", flush=True)


def checkpoint_path(run_id):
    return ROOT / "state" / f"{run_id}.checkpoint.json"


def load_checkpoint(run_id):
    path = checkpoint_path(run_id)
    if path.exists():
        return json.loads(path.read_text())
    return {"run_id": run_id, "completed_steps": 0, "status": "fresh"}


def save_checkpoint(run_id, completed, status):
    ROOT.joinpath("state").mkdir(exist_ok=True)
    path = checkpoint_path(run_id)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(
        {"run_id": run_id, "completed_steps": completed, "status": status,
         "total_steps": TOTAL_STEPS}, indent=2) + "\n")
    tmp.rename(path)  # atomic: a reader never sees a half-written checkpoint


def heartbeat(run_id, step):
    ROOT.joinpath("state").mkdir(exist_ok=True)
    with open(ROOT / "state" / f"{run_id}.heartbeat", "a") as f:
        f.write(f"step={step} pid={os.getpid()} t={time.strftime('%H:%M:%S')}\n")


def do_step(run_id, step):
    """The 'work': one appended output line per step. Append-once per step
    number is what --resume must preserve."""
    ROOT.joinpath("output").mkdir(exist_ok=True)
    with open(ROOT / "output" / f"{run_id}.log", "a") as f:
        f.write(f"step {step:02d}/{TOTAL_STEPS}: processed batch {step}\n")
    time.sleep(STEP_SECONDS)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--fail-after", type=int, default=None)
    args = parser.parse_args()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    state = load_checkpoint(args.run_id)
    start_from = state["completed_steps"] if args.resume else 0
    if not args.resume and state["completed_steps"] > 0:
        print(f"[slow-task] checkpoint exists at step {state['completed_steps']}; "
              "pass --resume to continue it, or use a new --run-id. Refusing "
              "to silently redo completed side effects.")
        return 2

    print(f"[slow-task {args.run_id}] starting at step {start_from + 1}/{TOTAL_STEPS} "
          f"(pid {os.getpid()})", flush=True)

    for step in range(start_from + 1, TOTAL_STEPS + 1):
        do_step(args.run_id, step)
        save_checkpoint(args.run_id, step, "running")
        heartbeat(args.run_id, step)
        print(f"[slow-task {args.run_id}] checkpointed step {step}", flush=True)

        if args.fail_after is not None and step >= args.fail_after:
            save_checkpoint(args.run_id, step, "failed")
            print(f"[slow-task {args.run_id}] planted failure after step {step}. "
                  "Retry with --resume; completed steps will not redo.", flush=True)
            return 1

        if _stop_requested:
            save_checkpoint(args.run_id, step, "stopped")
            print(f"[slow-task {args.run_id}] clean stop at step {step}. "
                  "Resume with --resume.", flush=True)
            return 0

    save_checkpoint(args.run_id, TOTAL_STEPS, "complete")
    print(f"[slow-task {args.run_id}] complete: {TOTAL_STEPS}/{TOTAL_STEPS} steps.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
