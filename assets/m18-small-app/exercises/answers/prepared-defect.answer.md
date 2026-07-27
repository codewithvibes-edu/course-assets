# Prepared defect: the answer

Do not read this before doing the drill. Seriously. The drill is the value.

## The defect

The patch changed `add_snippet` to only include a `"tags"` key when the
tag list is non-empty ("keep the store compact"). Every reader of the
store still assumes the key exists: `format_entry` does `entry["tags"]`,
`list_snippets` filters with `tag in entry["tags"]`, and `search_snippets`
loops over `entry["tags"]`. The writer changed the data shape; the readers
never got the memo.

## The evidence trail, step by step

1. **Reproduce:** `python3 -m unittest discover -s tests` fails with
   3 errors. All three tracebacks end the same way: `KeyError: 'tags'`.
   Three red tests, one shared cause. Noticing that saved you two thirds
   of the work.
2. **Exact error:** `KeyError: 'tags'`, pointing into `format_entry` (and
   `search_snippets`, depending on the test).
3. **Triggering input:** from the CLI,
   `python3 snippets.py add "git restore ."` (no `--tags`) saves fine,
   then `python3 snippets.py list` crashes. A snippet saved WITH tags
   lists fine. The difference between those two runs is the whole
   diagnosis.
4. **Expected instead:** an untagged snippet lists cleanly (that is
   requirement AC-1.2, on paper, in requirements.md).
5. **Isolate:** `git diff` shows one hunk in `add_snippet`. After the
   change, a stored entry can exist WITHOUT a `"tags"` key. Before, it
   could not.
6. **The fix.** Two honest options:
   - Put the invariant back: always store `"tags": tags`. Smallest
     change, restores the old data shape.
   - Keep the compact store and make every reader tolerant:
     `entry.get("tags", [])` in the three reader functions. More edits,
     and now BOTH data shapes are legal forever, including in files
     already written while the defect was live.

   The first is the better version-one fix: one writer invariant beats
   three defensive readers, and no already-written data needs migrating
   in this app because the drill is self-contained. If you picked the
   second and all seven tests pass, you still pass the drill.

## The transferable lesson

The agent's change was locally reasonable and globally wrong: it optimized
the writer while every reader kept an unwritten assumption. That is the
most common shape of agent-introduced bug you will meet, and no diff line
looks wrong in isolation. The defense is exactly what you drilled: the
ugly-case test existed because requirements.md demanded it (AC-1.2), and
it went red the moment the assumption broke.
