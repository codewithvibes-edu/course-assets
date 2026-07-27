# Templates and rubrics

Reusable, brand-neutral tools that cut across modules. A template is a
file you copy and fill in. A rubric is a scoring sheet you run an
artifact against before you trust it. Use the rubric to grade, the
template to build.

## What's in here

```
templates/
├── README.md
├── prompt.template.md              # structure for a reusable prompt
├── prompt-quality-rubric.md        # score a prompt 0-2 per criterion
├── agent-instruction.template.md   # the contract for an agent
├── agent-instruction-rubric.md     # pass/fail tests for that contract
├── memory-file.template.md         # an always-on memory file
├── anti-bloat-rubric.md            # what to delete or consolidate
├── clean-doc-rubric.md             # what makes a markdown doc clean
├── instruction-file.template.md    # CLAUDE.md / AGENTS.md skeleton
└── instruction-file-rubric.md      # is your instruction file any good
```

## How they map to the course

- **Prompt** template + rubric: Module 2 (prompt quality), and the
  no-code spec work in 102.
- **Agent instruction** template + rubric: Modules 9-11 (tools, agents,
  MCP), and the 102 approval-gate lesson.
- **Memory file** template + **anti-bloat** rubric: Module 12, and the
  102 memory-doc lesson. The richer knowledge-base kit lives in
  `assets/m12-knowledge-base/`.
- **Clean-doc** rubric: any markdown an agent has to read.
- **Instruction file** template + rubric: every repo you point an agent
  at.

## How to use a rubric

Score the artifact, write the number down, fix the lowest criteria, and
re-score. The point is not the number. The point is that "looks good"
becomes a checklist you can fail on purpose and then fix.
