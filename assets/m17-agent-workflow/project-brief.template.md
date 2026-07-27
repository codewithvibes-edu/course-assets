# Project brief (CLAUDE.md, AGENTS.md, or your harness equivalent)

<!--
Copy this file to your repo root and name it whatever your harness reads
automatically at the start of a session: CLAUDE.md for Claude Code,
AGENTS.md for Codex, or whatever your harness docs name. Then fill it in.
Write it like first-day instructions for a competent contractor:
constraints, not narration. Update it every time you catch the
agent doing something you had to correct.
One boundary: this file guides the agent; it does not enforce anything.
A rule that truly must never break also needs a harness permission rule.
-->

## What this is

<!-- Two or three sentences. What the project does, who it is for,
and whether it runs attended or unattended. The agent can read the
code; it cannot read your intent. -->

## Conventions

<!-- The rules that are not obvious from the code. Examples: -->

- Language + package manager, and how to run things (e.g. "Python via uv;
  run everything as: uv run python <file>").
- Where secrets live and the handling rule (e.g. ".env via python-dotenv.
  NEVER print, log, or commit secrets. .env stays gitignored.").
- Shared helpers the agent must route through instead of reinventing
  (e.g. "all HTTP goes through fetch_with_retry() in util.py").

## Things that look wrong but are intentional

<!-- The traps. Anything a well-meaning contractor would "fix" and break.
Rate-limit sleeps, weird schema choices, deliberately duplicated code. -->

## Never

<!-- Hard rules. Keep this list short and absolute. Examples: -->

- Never call real external APIs in tests; use fixtures/.
- Never edit existing migrations; append a new one.
- Do only what is asked. Propose extras; do not implement them unasked.
- Ask before adding any new dependency.
