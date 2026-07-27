# Notification contract

Task output is not the notification. The notification is the operational
signal: run ID, outcome, evidence location, next action. Never secrets,
never the transcript.

| State | Who gets told | Via | Carries |
| --- | --- | --- | --- |
| success/clean | | | run ID + evidence path |
| findings/degraded | | | + next action |
| missed | | | + why + policy applied |
| retry exhausted | | | + stop condition hit |
| disabled | | | + who disabled + why |
