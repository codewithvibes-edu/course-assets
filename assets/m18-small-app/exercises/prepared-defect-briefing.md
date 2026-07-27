# Prepared defect drill (lesson 5)

A debugging rep on a codebase where the defect is KNOWN, so you can grade
your process against the answer instead of wondering if you got lucky. Do
the whole drill before opening `answers/prepared-defect.answer.md`.

## The setup story

An agent was asked to "keep the store file compact" and made a small change
to how snippets get saved. The diff looked reasonable. It got committed
without the ugly-case tests running. That is the whole story, and it is a
Tuesday.

## Setup

```sh
cd sample-app

# make the folder its own tiny repo so rollback is one command
git init
git add .
git commit -m "sample app at release state"

# run the suite once BEFORE the patch, so you know clean looks like
python3 -m unittest discover -s tests

# apply the defect
git apply ../exercises/prepared-defect.patch
```

## The drill: evidence first, in this order

1. **Reproduce.** Run the suite. Several tests go red at once. Before
   touching anything, notice that, and ask whether they share one cause.
2. **Capture the exact error.** Copy the actual traceback text somewhere.
   The error type and the line it points at are evidence; "the tests are
   failing" is a mood.
3. **Find the triggering input.** Reproduce it from the CLI without the
   test suite. Two commands are enough. Which kind of snippet breaks it?
   Which kind survives?
4. **State what you expected instead**, in one sentence, out loud if
   nobody is around to judge you.
5. **Isolate one variable.** Read the diff you applied
   (`git diff`). One hunk changed. What data shape can exist after
   the change that could not exist before?
6. **Change one thing and rerun the smallest test.** Fix it however you
   judge best, run the single test that was closest to the failure, then
   the whole suite.

## Cleanup

Your call, and both paths are the lesson:

```sh
git restore .        # roll the patch and your fix off, back to release
# or
git add . && git commit -m "fix: <what you found>"   # keep your fix
```

Then check the answer key. If your fix differs from the one in the key but
the suite passes and your fix handles both data shapes, that counts. There
is more than one correct repair; there is only one correct process.
