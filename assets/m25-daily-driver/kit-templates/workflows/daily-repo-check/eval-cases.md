# Eval cases: daily-repo-check

Two minimum. A workflow without eval cases is a vibe with a name.

| # | Given | When invoked | Then |
| --- | --- | --- | --- |
| 1 | fixture data as shipped | any accepted phrasing | report exists at reports/<run-id>.json; exactly 4 findings: stale_count, zero_stock, missing_contact, unknown_sku; outcome "findings" |
| 2 | ORC-003 last_counted set to 2026-07-23 (then reverted) | any accepted phrasing | exactly 3 findings; stale_count absent; outcome "findings" |

Record each run: date, phrasing used, pass/fail, and what you revised
when one failed. The revision after a failed eval IS the lesson.
