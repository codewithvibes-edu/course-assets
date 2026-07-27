# Plan: [app name]

A staged plan is step size decided in advance, while you are calm. Every
stage ends with the repo runnable, one visible improvement, and a small test
you can run. A stage that would produce a diff too big to read gets split
before the build, not after.

## Stages

| # | Stage | Visible improvement when done | Smallest test to run | Done? |
| --- | --- | --- | --- | --- |
| 1 | [e.g. skeleton: CLI parses commands, does nothing] | `--help` prints real commands | run it, read the help | |
| 2 | [e.g. core job works on the happy path] | [what you can see] | [exact command] | |
| 3 | [e.g. the ugly case from AC-U.1 handled] | [what you can see] | [exact command] | |
| 4 | [e.g. summary output / polish within scope] | [what you can see] | [exact command] | |

## Assumptions that need proof

A guess wearing a plan's clothes gets a check before anything builds on it.

| Assumption | How it gets proven (test, check, or question) | Proven? |
| --- | --- | --- |
| [e.g. "the CSV always has headers"] | [e.g. AC-U.1 test feeds a headerless file] | |

## Risks and stop points

| Risk | Stop point (what makes you pause and re-plan) |
| --- | --- |
| [e.g. "file moving might clobber on name collision"] | [e.g. "any stage where a destructive operation runs without a dry-run test first"] |

## The retreat rule (required, verbatim, before the build)

If a stage fails its smallest test twice after one honest evidence-first
debugging pass, stop. `git restore` to the last known-good commit and
re-plan the stage smaller. Forward is not the only direction, and mid-spiral
is the most expensive place to decide that.
