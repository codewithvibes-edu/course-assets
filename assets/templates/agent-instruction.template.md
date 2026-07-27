# Agent-Instruction Template

This is the standing instruction set an agent reads before every run. A prompt is
one task. This is the job description. Fill every section, then check it against
`agent-instruction-rubric.md`.

```md
# Agent Role

You are responsible for: [job]
You are not responsible for: [boundaries]

# Operating Loop

1. Read the task.
2. Load required context.
3. Decide whether tools are needed.
4. Use tools only for their stated purpose.
5. Produce the output.
6. Log what changed.

# Tools

- Tool:
  - Use when:
  - Do not use when:
  - Required inputs:
  - Failure behavior:

# Memory

Always read:
Retrieve when needed:
Write logs to:

# Approval Rules

Can do without approval:
Must ask before:
Never do:

# Output Contract

Return:
Include:
Exclude:
If blocked:
```

## Notes

- **Role** has a "not responsible for" line because scope creep is how agents
  start touching things they should not.
- **Tools** each get a non-use and a failure behavior. An agent that does not know
  when to stop using a tool will use it wrong, confidently, in a loop.
- **Memory** separates always-read (small, cheap) from retrieve-when-needed
  (large, on demand). See `memory-file.template.md` and the m12 knowledge-base kit.
- **Approval Rules** is the safety gate. Irreversible, money, and public actions
  belong under "Must ask before" or "Never do."
