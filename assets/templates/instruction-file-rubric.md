# Instruction-File Rubric

Why this exists: checks an AGENTS.md / CLAUDE.md before you trust an agent to work
in the repo from it. Each line is a pass/fail test.

## A good instruction file

- Helps the agent act correctly in the first five minutes.
- Contains commands that actually run.
- Names repo-specific patterns, not generic advice.
- Separates hard rules from preferences.
- Includes testing expectations by risk level.
- Avoids stale setup instructions.
- Avoids giant pasted docs.
- Has a last-reviewed date.
- Says what not to touch.

## How to use it

1. Open the repo fresh, read only this file, try to make a trivial change.
2. Every place you had to guess or search outside the file is a failing line.
3. Run one command from the Commands section. If it errors, the file is lying.
4. Confirm there is a "what not to touch" line. Its absence is the most common
   and most expensive gap.

The test that matters most: a competent agent who has never seen the repo should
make a correct first change from this file alone. If it cannot, the file is not
done.
