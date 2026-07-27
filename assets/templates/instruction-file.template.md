# Instruction-File Template (AGENTS.md / CLAUDE.md)

Why this exists: this is the file a coding agent reads first in a repo. It decides
whether the agent acts correctly in the first five minutes or guesses. Fill every
section with repo-specific facts, then check it against `instruction-file-rubric.md`.

```md
# AGENTS.md / CLAUDE.md

## Project Purpose

[What this repo/system does.]

## How To Work Here

- Read these files first:
- Run these commands before changes:
- Use these conventions:

## Commands

- Install:
- Test:
- Lint:
- Dev server:
- Build:

## Code Style

- Language/framework:
- Patterns to follow:
- Patterns to avoid:

## Safety Rules

- Never edit:
- Never commit secrets:
- Ask before:

## Domain Rules

- Important business logic:
- Terms with special meaning:
- User-facing promises:

## Testing Expectations

- For small changes:
- For shared behavior:
- For user-facing workflows:

## Logging And Debugging

- Logs live:
- Traces live:
- Common failure modes:

## Memory Rules

- Update this file when:
- Do not add:
- Last reviewed:
```

## Notes

- **Commands** must actually run. The fastest way to lose an agent's trust in this
  file is one command that errors. Paste commands you have run yourself.
- **Code Style** names patterns to follow AND to avoid. The avoid list stops the
  agent from "improving" things in ways you will revert.
- **Safety Rules** is the firewall. "Never edit" and "Ask before" prevent the
  expensive mistakes.
- **Memory Rules** keeps the file from rotting. State when to update it and what
  not to dump into it.
