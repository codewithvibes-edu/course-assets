# Orchard: the m25 fixture repo

A tiny, deterministic inventory repo that exists to be OPERATED ON. You
will wrap its check job as a reusable workflow, plan and hand off work
against it, dispatch subagents to answer questions about it, run and
interrupt its slow task, isolate changes to it in worktrees, fence it
with permissions, schedule it, break it on purpose, and recover it.
Standard library only, no network, no accounts, and "today" is frozen
inside the checker so the findings never drift.

## Setup

Copy this folder somewhere workable and make it a repo (rollback drills
need git):

```sh
cp -r fixture-repo ~/orchard && cd ~/orchard
git init && git add . && git commit -m "orchard at known-good"
```

## The moving parts

| Piece | What it is | Used by lesson |
| --- | --- | --- |
| `data/*.csv` | 5 inventory items, 3 suppliers, 4 orders, with four planted findings (a stale count, a zero stock, a missing contact, an unknown SKU) | all of them |
| `scripts/repo_check.py --run-id X` | the daily-repo-check job: deterministic findings, `reports/X.json`, exit 1 on findings | 1, 7, 8 |
| `scripts/slow_task.py --run-id X` | 10 checkpointed steps, ~2s each; SIGTERM-safe; `--resume` never redoes side effects; `--fail-after N` plants a crash | 4, 7, 8 |
| `scripts/run_with_lock.py --policy skip\|queue -- <cmd>` | the overlap lock; skip exits 3 with the holder named; stale locks break with a notice | 7 |
| `scripts/notify.py` | the local notification sink: run ID, outcome, evidence, next action into `notifications.log`; no field for secrets on purpose | 8 |

## Verify the fixture before trusting it

```sh
python3 scripts/repo_check.py --run-id smoke-1   # expect: 4 findings, exit 1
python3 scripts/slow_task.py --run-id smoke-2 &  # then Ctrl+C it mid-run
python3 scripts/slow_task.py --run-id smoke-2 --resume
sort output/smoke-2.log | uniq -d                # expect: empty (no duplicates)
```

Generated artifacts (`reports/`, `state/`, `output/`, `notifications.log`)
are gitignored: runs produce evidence, commits record decisions.
