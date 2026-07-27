# Workflow contract: daily-repo-check

Product-neutral contract for the reusable workflow. The dated recipe
translates this into your harness's skill / reusable-command surface.

| Field | Value |
| --- | --- |
| Name | daily-repo-check |
| Job (one sentence) | run the fixture's repo check and report findings with evidence |
| Inputs | run ID (stable, caller-supplied) |
| Output schema | report path + finding count + outcome (clean/findings) + one-line summary per finding |
| Allowed tools/actions | read repo files; run scripts/repo_check.py; write under reports/ only |
| Forbidden | edits to data/ or scripts/; network; anything outside the repo |
| Side effects | exactly one report file per run ID |
| Stop conditions | check script exit >1 (real failure, not findings); missing data file |
| Invocation phrasings it must survive | "run the daily repo check", "check the orchard for problems" |
