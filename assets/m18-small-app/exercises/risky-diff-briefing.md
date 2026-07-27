# Risky diff review (lesson 6)

**Read-only exercise. Never apply this patch.** The artifact is your
written findings, not a changed repo.

## The setup story

You asked the agent to "add a backup feature" to snip. It came back with
this diff: a backup script, a couple of helper packages, an update check,
"nothing unusual." The diff is `risky-diff.patch` in this folder. It is the
kind of afternoon output that looks fine at commit time and gets expensive
later.

## The drill

1. Open `risky-diff.patch` in your editor and read every hunk, the way
   lesson 6 taught: new dependencies, new files, anything touching
   credentials, and the body of every script, because a script's name is a
   claim, never a fact.
2. For each hunk, write a verdict in your own findings file: **accept**,
   **replace**, or **remove**, with one sentence of reasoning.
3. Use the five dependency questions from
   `templates/dependency-review.template.md` on every package the diff
   adds.
4. There are at least three problems planted in this diff, the three
   shapes that account for most real supply-chain pain. Find them before
   the answer key names them.

Some questions worth asking while you read: what does this app now do on
EVERY run that it never did before? Where does the token live, and where
does it end up? What does the "rotate older files out" loop actually match?
Did anything in the requirements ask for any of this?

## When you are done

Check `answers/risky-diff.answer.md`. Score yourself honestly. Missing one
here costs nothing; the shape of what you missed is what you will scan for
on your own diffs from now on.
