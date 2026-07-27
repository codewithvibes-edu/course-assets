# Prompt-Quality Rubric

Why this exists: a prompt is the spec you hand a model. A vague spec gets a vague
result and you blame the model. Score the prompt before you blame anything.

Score each criterion 0, 1, or 2.

| Criterion   | 0                | 1                | 2                                        |
| ----------- | ---------------- | ---------------- | ---------------------------------------- |
| Task        | Vague ask        | Task named       | Task is specific and bounded             |
| Context     | Missing          | Some context     | Only relevant context included           |
| Output      | "Helpful answer" | Loose format     | Exact shape, length, fields, constraints |
| Inputs      | Unclear          | Inputs named     | Inputs labeled and separated             |
| Standards   | Subjective       | Some preferences | Checkable quality bar                    |
| Boundaries  | None             | Some warnings    | Clear exclusions and failure behavior    |
| Testability | Cannot score     | Can eyeball      | Can run against examples                 |

Max score: 14.

## Pass bars

- **10/14** before you reuse a prompt.
- **12/14** before you let it run unattended (automation).

If a prompt scores under 10, do not tune the model. Rewrite the prompt against
the criterion that scored lowest. Most "the model is dumb" complaints are a 0 in
Output or Boundaries.

## How to use it

1. Write the prompt.
2. Score all seven rows honestly.
3. Fix the lowest row first.
4. Re-score. Repeat until you clear the bar for how you plan to use it.

Pair this with `prompt.template.md`, which is already shaped to score 2s.
