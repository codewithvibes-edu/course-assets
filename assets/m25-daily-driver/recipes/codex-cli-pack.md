# DATED RECIPE PACK: Codex CLI

| Field | Value |
| --- | --- |
| Harness | Codex CLI (OpenAI) |
| Version tested | 0.144.1 |
| Last tested | 2026-07-24 |
| Reviewer | course staff |
| OS tested | macOS 15 (official support: macOS, Linux, Windows via WSL per current docs) |
| Docs (these win on any disagreement) | openai.com/codex and the CLI's own `codex --help` |
| Access prerequisite (fact, no walkthrough) | a ChatGPT subscription covers sessions within usage limits, or per-use API billing; the m17 recipe covered install and sign-in |

## Capability matrix (nine surfaces, tested against this version)

| Surface | Status | The current shape (verify against docs) |
| --- | --- | --- |
| Instruction scope | supported | `AGENTS.md` at repo root (project) and `~/.codex/AGENTS.md` (personal, all projects) |
| Reusable workflows | supported | custom prompts: markdown files under `~/.codex/prompts/` become invokable slash commands; a plugin surface also exists (`codex plugin`) |
| Plan / progress state | no dedicated surface | sessions persist and can be resumed or forked (`codex resume`, `codex fork`), which preserves conversation state; the plan/progress/handoff ARTIFACT files carry the durable state, exactly as the neutral contract intends |
| Subagents | no dedicated surface | there is no in-session dispatch tool at this version; the working pattern is parallel non-interactive runs (`codex exec`, one per work packet, each with its own `-C` scope), collected by their output files. Label results by packet; do not present this as in-session dispatch |
| Background tasks | supported (via pattern) | `codex exec` is the non-interactive runner; background it at the OS level (or via the fixture's lock wrapper); an experimental cloud-tasks surface exists (`codex cloud`) and is out of scope here |
| Worktree isolation | supported (via pattern) | no dedicated worktree command; standard `git worktree add` plus `codex -C <worktree-path>` scopes a session to the isolated tree |
| Hooks | partial | no pre-action user hook surface at this version: there is no supported way to run your own check that blocks an action before it executes. A completion notification hook exists (`notify` in `~/.codex/config.toml`, invoked with turn results). Enforcement therefore lives in the sandbox and approval settings, and the audit half of the hook contract uses the notify hook. Record the pre-action row as not supported; do not invent an equivalence |
| Permission profiles | supported | sandbox modes (`read-only`, `workspace-write`, `danger-full-access`) plus `approval_policy` (`untrusted`, `on-request`, `on-failure`, `never`) in `config.toml` with per-invocation overrides (`-s`, `-c`); profiles = named combinations you record in permission-profiles.md |
| Scheduling | supported (via OS scheduler) | cron or launchd invoking `codex exec` through the fixture's lock wrapper; same shape as any headless runner |

## Lesson-by-lesson translation (drills 1-8)

1. **Workflow:** create `~/.codex/prompts/daily-repo-check.md` restating
   your workflow-contract.md. Invoke it twice with different phrasings;
   both runs must produce the contracted report.
2. **Plan/handoff:** do stage one, write the state/ files, end the
   session, start fresh (or `codex resume` a NEW session deliberately
   NOT forked from the old one) and point it at handoff.md only. Score
   the recovery.
3. **Subagents:** two work packets, two parallel `codex exec` runs, each
   read-scoped by `-C` and its packet prompt, results to separate files;
   reconcile in the ledger. This is the pattern translation of dispatch;
   the packet discipline is identical.
4. **Background:** run `slow_task.py` under `codex exec` backgrounded at
   the OS level; inspect the heartbeat and checkpoint as evidence;
   interrupt; verify the clean stop; resume.
5. **Worktrees:** `git worktree add` twice, one bounded change per tree
   via `codex -C`; integrate one, discard one, verify main is clean.
6. **Permissions/hooks:** define supervised and unattended profiles as
   sandbox + approval combinations in config; run the allowed and denied
   cases (denied = the sandbox refusing an out-of-scope write). For the
   hook rows, wire the notify hook as the audit hook and record the
   pre-action row as not supported at this version.
7. **Scheduling:** cron fires the lock wrapper around `codex exec` on
   your cadence; force an overlap; simulate a miss.
8. **Notify/rollback:** schedule outcomes flow through `notify.py` (and
   optionally the notify hook); drill the disable, roll back prompt and
   config versions (git), resume from checkpoint, verify no duplicates.

## Stop, cancel, cleanup, undo

Interactive sessions interrupt with Esc/Ctrl+C; `codex exec` stops like
any process (the fixture's slow task checkpoints on SIGTERM). Cleanup:
worktrees removed explicitly; prompts and config.toml are plain files,
so undo is git plus a fresh session. `codex doctor` diagnoses a wedged
local install.

## Failure signatures observed while testing

A sandbox refusal reports the denied path or command; `exec` exits
nonzero on refusal rather than hanging; a custom prompt that does not
appear is usually a filename/location miss under `~/.codex/prompts/`.

## Telemetry / retention facts

Sessions persist locally under `~/.codex/` (resume/fork reads them);
treat transcripts as logs. Provider-side retention follows your account
settings; verify against the official docs current at your read date.
