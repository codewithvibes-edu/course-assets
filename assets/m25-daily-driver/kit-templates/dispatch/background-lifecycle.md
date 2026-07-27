# Background lifecycle: [run-id]

Recorded BEFORE moving anything to the background.

| Field | Value |
| --- | --- |
| Task ID / run ID | |
| Owner | |
| Start state (commit, inputs) | |
| Output location | |
| Timeout | |
| Heartbeat / status signal (how an outsider tells alive from hung) | |
| Stop method (exact) | |
| Resume-or-restart policy and why that is safe | |

Evidence attached: status output, stop output, cleanup proof (no orphan
process, no half-written output), recovered result.
