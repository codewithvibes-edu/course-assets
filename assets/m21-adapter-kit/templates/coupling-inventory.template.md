# Coupling inventory (lesson 1)

Every place your hosted application knows which provider it talks to.
Search honestly: URLs, model names, SDK imports, message shapes, event
names, error types, finish reasons, usage field names. The Module 20
decision note started this list; now it gets finished and dated.

| # | File and line | What it knows | Kind (URL / model ID / import / shape / event / error / field name) | Moves behind the adapter? |
| --- | --- | --- | --- | --- |
| 1 | | | | |
| 2 | | | | |

**Total count:** ___ (write it down; you will enjoy the after number)

## The capability probe (measured, not copied)

For the connection you actually use, test each capability and record what
HAPPENED, with a date. A marketing matrix is a hypothesis; this table is
evidence.

| Capability | Probe you ran | Result | Date |
| --- | --- | --- | --- |
| text | | | |
| streaming | | | |
| structured output | | | |
| tools | | | |
| image input | | | |

## Two words kept apart

Connection capability is what THIS connection did under test today.
Provider identity is a brand name. Compatibility labels ("works with X")
are hypotheses that this table either confirms or kills. Route on
measured capability, never on the logo.
