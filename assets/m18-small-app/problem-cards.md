# Three problem cards

Proven first-app shapes. Each obeys the module's four-part definition: one
user, one repeated job, one visible result, non-goals that hold the fence.
Pick one, or bring your own idea that passes the same test. Whatever you
pick, the two-minute demo rule applies: if showing every requirement takes
longer than two minutes, cut requirements.

None of these call a model, generate media, or touch the network. That is
the point of this module. Version two can dream.

---

## Card 1: The folder janitor

**User:** anyone whose Downloads folder is a crime scene (you).
**Job:** every week, sort accumulated files into folders by type and age.
**Visible result:** run one command, watch a messy folder become organized
folders, read a one-screen summary of what moved where.

**Suggested requirements territory:** rules live in a small config file the
user edits (which extensions go where); files older than a chosen age go to
an archive folder; a dry-run flag prints what WOULD move without moving it.

**The ugly cases live here:** a file with no extension, a name collision in
the destination, a file that is open in another program.

**Non-goals to write down:** no watching folders in real time, no
undo-history database, no GUI, no cloud anything.

---

## Card 2: The report tamer

**User:** anyone handed the same ugly CSV every week (a coworker counts).
**Job:** turn the raw export into a readable summary someone could paste
into an email.

**Visible result:** point the command at a CSV, get a clean text or markdown
summary file: totals, the top five whatever-matters, the rows that failed
validation listed at the bottom.

**Suggested requirements territory:** column names come from a config, not
hardcoded; bad rows get reported, never silently dropped; output lands in a
dated file so last week's report survives this week's run.

**The ugly cases live here:** a missing column, a duplicated header row, a
number column with "N/A" in it, an empty file.

**Non-goals to write down:** no charts, no Excel writing, no email sending,
no database.

---

## Card 3: The terminal taskkeeper

**User:** anyone who lives in a terminal and keeps losing sticky notes (yes,
you again).
**Job:** capture, list, and finish small tasks without leaving the shell.

**Visible result:** `add`, `list`, `done` commands against a plain local
file; `list` shows open tasks with age; `done` moves a task to a completed
log instead of deleting it.

**Suggested requirements territory:** tasks survive restarts (plain JSON or
text file); each task shows how many days old it is; a `--all` flag shows
finished tasks too.

**The ugly cases live here:** marking done a task number that does not
exist, an empty task text, a corrupted data file (someone edited it by hand,
because someone always does).

**Non-goals to write down:** no due dates, no priorities, no sync, no
recurring tasks, no colors until version two.

---

## Bringing your own idea

Allowed and encouraged. Hold it against the same frame before you commit:

1. One user you can name. "Everyone" is zero users wearing a trench coat.
2. One repeated job. If the job happens once, a script beats an app.
3. One visible result you can point at on a screen during the demo.
4. Three or more non-goals, written down, that you will actually honor.
5. No model calls, no generated media, no network. Local files in, local
   files out. The networked version of your idea is two modules away.
