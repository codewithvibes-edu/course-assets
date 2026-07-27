# Permission profiles

Action classes: read-only / repo write / process execution / network /
secret access / irreversible external effect.

## Supervised profile (daily driving)

| Field | Value |
| --- | --- |
| Allowed roots | |
| Allowed commands or action classes | |
| Network destinations | |
| Secret exclusions | |
| Escalation points (what always asks) | |
| When enforcement cannot decide | ask, always |

## Unattended profile (narrower, for scheduled runs)

| Field | Value |
| --- | --- |
| Allowed roots | |
| Allowed action classes | |
| Network | none unless a destination is listed |
| Secrets | none |
| On any undecidable action | fail closed + notify |
