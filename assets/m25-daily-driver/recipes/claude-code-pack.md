# DATED RECIPE PACK: Claude Code

| Field | Value |
| --- | --- |
| Harness | Claude Code (Anthropic) |
| Version tested | 2.1.219 |
| Last tested | 2026-07-24 |
| Reviewer | course staff |
| OS tested | macOS 15 (official support: macOS, Linux, Windows) |
| Docs (these win on any disagreement) | code.claude.com/docs |
| Access prerequisite (fact, no walkthrough) | a claude.ai subscription covers sessions within usage limits, or per-use API billing; the m17 recipe covered install and sign-in |

## Capability matrix (nine surfaces, tested against this version)

| Surface | Status | The current shape (verify against docs) |
| --- | --- | --- |
| Instruction scope | supported | `CLAUDE.md` at repo root (project), `~/.claude/CLAUDE.md` (personal, all projects), `CLAUDE.local.md` (personal, this repo, gitignored) |
| Reusable workflows | supported | skills: a folder with `SKILL.md` under `.claude/skills/` (repo) or `~/.claude/skills/` (personal); invoke by `/name` or by asking for the task it declares |
| Plan / progress state | supported | native plan mode (propose-before-touching), plus plain plan/progress files, which are the transferable part |
| Subagents | supported | native dispatch: ask for a bounded task to run as a subagent; custom agent types via `.claude/agents/*.md`; results return as reports |
| Background tasks | supported | long commands can run in background with status and output inspection from the session; headless `claude -p "<prompt>"` runs non-interactively for OS-level backgrounding |
| Worktree isolation | supported | native worktree entry (ask to work in a worktree), or standard `git worktree add` and pointing a session at the path |
| Hooks | supported | `hooks` in `.claude/settings.json`: pre-tool-use hooks can block actions (exit code + stderr become the refusal), post/stop hooks audit; hook failures surface in-session |
| Permission profiles | supported | permission modes plus allow/deny rules in `settings.json` (project and personal scopes); deny rules override; rules match tools and command patterns |
| Scheduling | supported (via OS scheduler) | no always-on daemon in the CLI itself: cron or launchd invoking headless `claude -p` is the tested local path; run it through the fixture's lock wrapper |

## Lesson-by-lesson translation (drills 1-8)

1. **Workflow:** create `.claude/skills/daily-repo-check/SKILL.md` whose
   instructions restate your workflow-contract.md (allowed actions,
   output schema, stop conditions). Invoke with two different phrasings;
   both runs must produce the contracted report.
2. **Plan/handoff:** do stage one, write the state/ files, exit the
   session fully, start a fresh one, and say only "resume from
   handoff.md". Score what it recovered.
3. **Subagents:** dispatch two bounded read-only questions about the
   fixture as parallel subagent tasks, one work packet each. Collect the
   two result reports into the ledger.
4. **Background:** have the harness run `slow_task.py` in the background,
   check its status by evidence (heartbeat file, checkpoint), interrupt
   it, verify the clean stop, resume it.
5. **Worktrees:** two worktrees, one bounded change each, integrate one
   through the normal diff-and-test gate, discard the other, verify the
   main tree is clean.
6. **Permissions/hooks:** write the two profiles as settings.json rules;
   add a pre-action hook that blocks writes outside allowed roots and an
   audit hook that logs completions. Run the allowed, denied, and
   hook-failure cases.
7. **Scheduling:** cron (or launchd) fires the lock wrapper around
   headless mode on your cadence; force an overlap; simulate a miss.
8. **Notify/rollback:** wire the schedule's outcomes through
   `notify.py`; drill the disable, rollback to the previous skill and
   profile versions (git), resume from checkpoint, verify no duplicates.

## Stop, cancel, cleanup, undo

Esc interrupts the current action in an interactive session; a
background task stops from the session that owns it; headless runs stop
like any process (the fixture's slow task checkpoints on SIGTERM).
Cleanup: worktrees are removed explicitly; skills and settings are plain
files, so undo is git. Rollback of harness-side config = revert the
settings/skill files and start a fresh session.

## Failure signatures observed while testing

Permission denials name the rule that fired; a blocking hook's stderr
appears as the refusal reason; a skill that does not load is usually a
malformed SKILL.md frontmatter; headless runs exit nonzero on refused
permissions rather than hanging.

## Telemetry / retention facts

Session transcripts persist locally under `~/.claude/`; treat them like
logs (the m17 secrets rule applies). Provider-side retention follows
your account's data settings; verify against the official docs page
current at your read date.
