# The review checklist

One pass per change, before you commit. Keep this next to your terminal
until the habits stick. The standard: if you cannot say what a change
does and why it is safe, you do not commit it.

## Read

- [ ] Read the whole diff. Names, files touched, anything deleted.
- [ ] Deletions get double scrutiny. Especially deleted tests.
- [ ] Change too big to hold in your head? It was too big. Split it.

## Interrogate

- [ ] Ask the agent to explain the change in plain English.
- [ ] Check the explanation against the diff, both directions:
      nothing claimed that the diff does not do, nothing in the diff
      the explanation skips.
- [ ] If a test changed: does the check get stronger, or does the
      check now just agree with the code? The second is not a fix.

## Run

- [ ] Run it yourself, on a case where you know the right answer.
- [ ] Break it once on purpose (empty file, missing field, weird date).
      Failure behavior tells you more than success behavior.

## The boring dangerous things (every time)

- [ ] No secrets in code, output, or logs.
- [ ] No real API calls where fixtures belong.
- [ ] Nothing staged that git was supposed to ignore.

## Commit

- [ ] One change, one commit, message says what changed.
- [ ] Can you describe the change in one sentence? Then commit it.
