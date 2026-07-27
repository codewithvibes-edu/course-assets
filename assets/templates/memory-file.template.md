# Memory-File Template

Why this exists: an agent with no durable memory re-asks what you already
answered and acts on decisions you reversed. This is the always-on core it reads
every session. Keep it small. Detail lives in linked notes, not here.

```md
# Memory: [Domain]

Last reviewed: YYYY-MM-DD

## One-Line Index

- Identity:
- Preferences:
- Standing decisions:
- Current projects:
- Open questions:

## Identity

Who I am:
What I do:
Who I serve:

## Preferences

Voice:
Formats:
Banned phrases:
Default tools:

## Standing Decisions

- YYYY-MM-DD: Decision, reason, still current.

## Current Projects

- Project:
  - Goal:
  - Status:
  - Next action:
  - Links:

## Open Questions

- Question:
  - Owner:
  - Needed by:

## Change Log

- YYYY-MM-DD: What changed.
```

## Notes

- **One-Line Index** at the top lets the agent scan and jump instead of reading
  the whole file to find one fact. Keep it honest; a stale index routes the agent
  confidently to the wrong place.
- **Last reviewed** is a forcing function. If the date is old, the file is
  probably rotting. Run it against `anti-bloat-rubric.md`.
- **Standing Decisions** carry a "still current" flag so a reversed decision gets
  deleted, not left as a lie the agent acts on.
- This file should fit on one screen. When it does not, push detail into linked
  notes (see the m12 knowledge-base kit) and keep only pointers here.
