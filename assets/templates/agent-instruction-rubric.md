# Agent-Instruction Rubric

Why this exists: a prompt rubric checks one task. This checks the standing
instructions an agent runs on every task. Each row is a pass/fail test, not a
score. An instruction set ships only when every row passes.

| Criterion         | Pass test                                                |
| ----------------- | -------------------------------------------------------- |
| Role clarity      | A new reader can say what the agent owns                 |
| Boundaries        | The instruction names what the agent must not do         |
| Tool discipline   | Each tool has use, non-use, inputs, and failure behavior |
| Memory discipline | Always-on context is small, retrievable context is named |
| Approval gate     | Irreversible, money, and public actions require yes      |
| Output contract   | The final response shape is fixed                        |
| Failure behavior  | The agent knows when to stop and ask                     |

## How to use it

1. Hand the instruction file to someone who has never seen the project.
2. Ask them to answer each pass test from the file alone.
3. Any test they cannot answer is a hole. Fix the file, not the person.

The two rows most often failed: **Approval gate** (no explicit "must ask before"
list) and **Failure behavior** (no "if blocked, stop and ask" line, so the agent
improvises). Fix those first.
