# Prompt Template

Copy this, fill every section, then score it against `prompt-quality-rubric.md`.
Empty sections are where prompts fail. If a section does not apply, write "none"
on purpose instead of leaving it blank.

```md
# Task

Do: [specific job]
Do not: [explicit exclusions]

# Context

Audience:
Goal:
Current situation:

# Inputs

[input_1]: ...
[input_2]: ...

# Output

Format:
Length:
Fields:
Destination:

# Quality Bar

A good answer:

- ...
- ...
- ...

# Constraints

Never:
Always:
If unsure:
```

## Notes

- **Task** is two lines on purpose. "Do not" is where you kill the failure mode
  you already know is coming.
- **Inputs** are labeled and separated so the model never confuses your data with
  your instructions.
- **Output** ends with Destination because most outputs need to land somewhere in
  a specific shape, not just appear in chat.
- **If unsure** tells the model what to do when it is blocked. Without it, the
  model guesses confidently. With it, the model asks or flags.
