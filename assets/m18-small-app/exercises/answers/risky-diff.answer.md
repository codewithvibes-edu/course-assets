# Risky diff: the answer key

Three planted problems, the three shapes from the module. Plus a couple of
bonus findings for full marks.

## Problem 1: a credential where credentials must never be

`config.py` hardcodes `SYNC_TOKEN = "sk-live-EXAMPLE-8f3a91c2b7d4"` in
source, with a `TODO: move to .env before shipping` comment doing the work
a `.env` file should be doing. Worse, `check_for_updates()` PRINTS the
token on every single run: it lands in your scrollback, your logs, your
pasted terminal output, and any screen recording, forever. The token here
is fake; the pattern ships real keys weekly, somewhere, to someone.

**Verdict: remove** (the token from source and from the print). If a sync
feature ever earns its place in requirements, the token lives in `.env`,
which is gitignored, and never appears in output. You verified that
pattern in the setup lab.

## Problem 2: packages added for work the project could already do

`requirements.txt` arrives with two dependencies for an app whose
requirements need zero:

- `requests`, used for one GET (an update check nobody asked for) and one
  POST (see problem 3). The standard library's `urllib.request` covers
  both, and the honest answer is that neither request should exist at all:
  no requirement mentions the network, and problem.md's non-goals
  effectively exclude it.
- `colorama`, imported to print one green "OK". Two ANSI codes in a string
  do the same job, and version one explicitly parked colors as a non-goal.

**Verdict: remove both.** Each package is supply chain you now carry:
install scripts, maintenance risk, transitive dependencies, for negative
value here.

## Problem 3: a script whose behavior is wider than its name

`scripts/backup.py` says "Back up your snippets file." The body does three
things:

1. Copies the store to `backups/`. That is the name.
2. DELETES every `*.json` in `backups/` older than 7 days. Deletion is
   not backup; a rotation policy nobody asked for is data loss with a
   schedule. And the glob matches any JSON that ends up in that folder,
   not only files this script created.
3. POSTs your snippet count and the sync token to an external URL
   ("usage stats help prioritize features"). Your "backup" phones home.

**Verdict: replace** with a script that does what the name claims: copy
the file, print where it went, done. If rotation ever becomes a real
requirement, it gets its own name, its own confirmation, and a glob that
only matches its own files.

## Bonus findings (full marks territory)

- `check_for_updates()` runs on EVERY command, so `snip list` now makes a
  network call before listing your local file. New behavior on every run
  that no requirement asked for, wrapped in a bare `except Exception:
  pass` that hides every failure it will ever have.
- Nothing in this diff maps to any acceptance criterion. The heavyweight
  checkpoint from lesson 3 applies to features too: no requirement, no
  component. The correct review outcome for this entire diff is a
  polite, complete rejection, and one sentence to the agent about what
  "add a backup feature" actually meant.
