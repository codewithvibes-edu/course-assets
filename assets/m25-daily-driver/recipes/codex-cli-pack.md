# DATED RECIPE PACK: Codex CLI

| Field                                      | Value                                                                                                                                     |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Harness                                    | Codex CLI (OpenAI)                                                                                                                        |
| CLI version/help checked                   | 0.144.1 (`codex --version` and top-level `codex --help`, 2026-08-02)                                                                      |
| Documentation verified                     | 2026-08-02 (capability claims below were read in current official docs; the drills were not rerun)                                        |
| Reviewer                                   | course staff                                                                                                                              |
| OS in original test                        | macOS 15 (current docs also support macOS, Linux, native Windows, and Windows via WSL)                                                    |
| Docs (these win on any disagreement)       | developers.openai.com/codex and the CLI's own `codex --help`                                                                              |
| Access prerequisite (fact, no walkthrough) | ChatGPT plan access covers sessions within usage limits, or an API key uses per-token billing; the m17 recipe covered install and sign-in |

## Capability matrix (nine surfaces, documentation verified for this revision)

| Surface               | Status                       | The current shape (verify against docs)                                                                                                                                                                                                                                                                                                                                                          |
| --------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Instruction scope     | supported                    | Codex reads global guidance from `$CODEX_HOME/AGENTS.override.md` or `AGENTS.md` (`$CODEX_HOME` defaults to `~/.codex`), then one `AGENTS.override.md` or `AGENTS.md` per directory from project root to the working directory; closer files take precedence                                                                                                                                     |
| Reusable workflows    | supported                    | skills are the current authoring surface: a folder with `SKILL.md` under `.agents/skills/` in a repo or `$HOME/.agents/skills/` for personal use; invoke with `/skills` or a `$skill-name` mention, or let its description match implicitly. Custom prompts under `~/.codex/prompts/` are deprecated. Plugins distribute skills and connectors and are managed with `codex plugin` or `/plugins` |
| Plan / progress state | supported                    | `/plan` enters native plan mode; `/goal` sets and manages a persistent task target; sessions can be resumed or forked (`/resume`, `/fork`, `codex resume`, `codex fork`). The plan/progress/handoff artifact files remain the transferable durable state                                                                                                                                         |
| Subagents             | supported                    | ask Codex in an interactive CLI session to delegate bounded work; `/agent` or `/subagents` inspects and switches agent threads while they run, and the main thread collects results. Custom agent TOML files live under `.codex/agents/` (project) or `~/.codex/agents/` (personal)                                                                                                              |
| Background tasks      | supported                    | when unified exec is active, long commands can run in background terminals; `/ps` inspects their status and recent output, and `/stop` stops them. `codex exec` remains the non-interactive runner for OS-level background and scheduled jobs                                                                                                                                                    |
| Worktree isolation    | supported (via pattern)      | native managed worktrees are documented for the ChatGPT desktop app, not the CLI; in the CLI use standard `git worktree add` plus `codex -C <worktree-path>` to scope a session to the isolated tree                                                                                                                                                                                             |
| Hooks                 | supported                    | hooks live in `hooks.json` or inline `[hooks]` tables beside active `config.toml` layers; `PreToolUse` can block or rewrite supported Bash, `apply_patch`, MCP, and other local function-tool calls, while `PostToolUse` and lifecycle hooks provide audit points. Use `/hooks` to inspect and trust non-managed hooks                                                                           |
| Permission profiles   | supported (beta)             | named `[permissions.<name>]` profiles define filesystem and network boundaries and are selected with `default_permissions` or the permissions UI; use them with approval policies. Do not combine them with the older `sandbox_mode` system. The legacy CLI flags still expose sandbox modes plus approval policies `untrusted`, `on-request`, and `never`; `on-failure` is not current          |
| Scheduling            | supported (via OS scheduler) | cron or launchd invoking `codex exec` through the fixture's lock wrapper; official non-interactive docs list scheduled jobs as a `codex exec` use case                                                                                                                                                                                                                                           |

## Lesson-by-lesson translation (drills 1-8)

1. **Workflow:** create `.agents/skills/daily-repo-check/SKILL.md` restating
   your workflow-contract.md. Invoke `$daily-repo-check`, then use a
   matching natural-language request;
   both runs must produce the contracted report.
2. **Plan/handoff:** enter `/plan`, set the task target with `/goal`, do
   stage one, write the state/ files, end the session, start fresh (or
   deliberately resume), and point it at handoff.md only. Score the
   recovery; the files, not native session state, are the transfer test.
3. **Subagents:** dispatch two bounded read-only work packets as parallel
   subagent tasks. Use `/agent` to inspect their threads; collect the two
   result reports into the ledger and reconcile them in the main thread.
4. **Background:** have Codex run `slow_task.py` in a background terminal;
   inspect it with `/ps` plus the heartbeat and checkpoint as evidence;
   stop it with `/stop`, verify the clean stop, then resume it.
5. **Worktrees:** `git worktree add` twice, one bounded change per tree
   via `codex -C`; integrate one, discard one, verify main is clean.
6. **Permissions/hooks:** define supervised and unattended named
   `[permissions.<name>]` filesystem/network boundaries and pair them
   with approval policies; do not mix them with `sandbox_mode`. Add a
   `PreToolUse` hook that blocks out-of-scope writes and a `PostToolUse`
   audit hook; run the allowed, denied, and hook-failure cases.
7. **Scheduling:** cron fires the lock wrapper around `codex exec` on
   your cadence; force an overlap; simulate a miss.
8. **Notify/rollback:** schedule outcomes flow through `notify.py` (and
   optionally a lifecycle hook); drill the disable, roll back skill and
   config versions (git), resume from checkpoint, verify no duplicates.

## Stop, cancel, cleanup, undo

`Ctrl+C` or `/exit` closes an interactive session; `/stop` stops all
background terminals owned by the current session. `codex exec` stops
like any process (the fixture's slow task checkpoints on SIGTERM).
Cleanup: worktrees are removed explicitly; repo skills, hooks, and config
are plain files, so undo is git plus a fresh session. `codex doctor`
diagnoses a wedged local install.

## Failure signatures to inspect

After a refusal, use `/status` or `/permissions` to inspect the active
boundary. Use `/hooks` to inspect configured handlers and trust state.
If a skill is absent, use `/skills` to check its name, description, and
location; Codex detects skill changes automatically, but restart if an
update does not appear.

## Telemetry / retention facts

Sessions persist locally under `~/.codex/` (resume/fork reads them);
treat transcripts as logs. Provider-side retention follows your account
settings; verify against the official docs current at your read date.
