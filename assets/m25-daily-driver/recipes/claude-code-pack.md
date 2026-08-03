# DATED RECIPE PACK: Claude Code

| Field                                      | Value                                                                                                                            |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| Harness                                    | Claude Code (Anthropic)                                                                                                          |
| CLI version/help checked                   | 2.1.220 (`claude --version` and top-level `claude --help`, 2026-08-02)                                                           |
| Documentation verified                     | 2026-08-02 (capability claims below were read in current official docs; the drills were not rerun)                               |
| Reviewer                                   | course staff                                                                                                                     |
| OS in original test                        | macOS 15 (official support: macOS, Linux, Windows)                                                                               |
| Docs (these win on any disagreement)       | code.claude.com/docs                                                                                                             |
| Access prerequisite (fact, no walkthrough) | a claude.ai subscription covers sessions within usage limits, or per-use API billing; the m17 recipe covered install and sign-in |

## Capability matrix (nine surfaces, documentation verified for this revision)

| Surface               | Status    | The current shape (verify against docs)                                                                                                                                                                                                                                                                            |
| --------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Instruction scope     | supported | `CLAUDE.md` at repo root (project), `~/.claude/CLAUDE.md` (personal, all projects), `CLAUDE.local.md` (personal, this repo, gitignored)                                                                                                                                                                            |
| Reusable workflows    | supported | skills: a folder with `SKILL.md` under `.claude/skills/` (repo) or `~/.claude/skills/` (personal); invoke by `/name` or by asking for the task it declares                                                                                                                                                         |
| Plan / progress state | supported | native plan mode (propose-before-touching) and `/goal` for a persistent task target, plus plain plan/progress files, which are the transferable part                                                                                                                                                               |
| Subagents             | supported | native dispatch: ask for a bounded task or explicitly mention a custom agent; custom agent types via `.claude/agents/*.md`; foreground or background results return to the parent session                                                                                                                          |
| Background tasks      | supported | long commands and subagents can run in the background; `/tasks` inspects current-session work. `/bg` or `claude --bg "<prompt>"` backgrounds a session, and `claude agents` dispatches and monitors background sessions                                                                                            |
| Worktree isolation    | supported | `claude --worktree <name>` (`-w`) creates and enters an isolated worktree, or ask Claude to use its `EnterWorktree` tool; standard `git worktree add` remains available for manual control                                                                                                                         |
| Hooks                 | supported | `hooks` in `.claude/settings.json`: pre-tool-use hooks can block actions (exit code + stderr become the refusal), post/stop hooks audit; hook failures surface in-session                                                                                                                                          |
| Permission profiles   | supported | permission modes plus allow/deny rules in `settings.json` (project and personal scopes); deny rules override; rules match tools and command patterns                                                                                                                                                               |
| Scheduling            | supported | `/loop` and the `CronCreate`, `CronList`, and `CronDelete` tools schedule session-scoped prompts; they require a running session, recurring tasks expire after seven days, and missed fires do not catch up. Use a durable scheduler around headless `claude -p` when work must survive independently of a session |

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
   check `/tasks` plus the heartbeat and checkpoint, then use `/bg` and
   `claude agents` to verify the owning session continues; stop it,
   verify the clean stop, resume it.
5. **Worktrees:** start two `claude --worktree <name>` sessions, one
   bounded change each, integrate one
   through the normal diff-and-test gate, discard the other, verify the
   main tree is clean.
6. **Permissions/hooks:** write the two profiles as settings.json rules;
   add a pre-action hook that blocks writes outside allowed roots and an
   audit hook that logs completions. Run the allowed, denied, and
   hook-failure cases.
7. **Scheduling:** use `/loop` to schedule a session-scoped check and
   verify the documented no-catch-up behavior; then have cron (or launchd)
   fire the lock wrapper around headless mode for the durable local case;
   force an overlap and simulate a miss.
8. **Notify/rollback:** wire the schedule's outcomes through
   `notify.py`; drill the disable, rollback to the previous skill and
   profile versions (git), resume from checkpoint, verify no duplicates.

## Stop, cancel, cleanup, undo

Esc or Ctrl+C interrupts the current action in an interactive session;
`/tasks` manages work owned by that session, while `claude agents`
manages background sessions; headless runs stop like any process (the
fixture's slow task checkpoints on SIGTERM).
Cleanup: worktrees are removed explicitly; skills and settings are plain
files, so undo is git. Rollback of harness-side config = revert the
settings/skill files and start a fresh session.

## Failure signatures to inspect

A blocking `PreToolUse` hook must exit with code 2 or return a blocking
JSON decision; exit code 1 is non-blocking. If a skill does not load,
inspect its `SKILL.md` and scope. A `--worktree` run exits with an error
when workspace trust has not yet been accepted for that directory.

## Telemetry / retention facts

Session transcripts persist locally under `~/.claude/`; treat them like
logs (the m17 secrets rule applies). Provider-side retention follows
your account's data settings; verify against the official docs page
current at your read date.
