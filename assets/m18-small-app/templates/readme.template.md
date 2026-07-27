# [app name]

[One paragraph: the user, the job, the visible result. Straight from
problem.md. A stranger reading only this paragraph knows whether the app is
for them.]

## Install

```sh
[exact commands, replayed in a fresh clone before release. Include the
Python version floor and how dependencies get installed, or say "standard
library only, nothing to install."]
```

## Run it

```sh
[the core job, as one or two commands with real example arguments]
```

## Test it

```sh
[the exact command that runs the test suite, and the manual smoke check
if the test map includes one]
```

## Stop it

[How to stop it cleanly, if it runs longer than a command. If it is
run-and-exit, say so.]

## What it does not do (known limitations)

- [Name the non-goals that a user might expect anyway.]
- [Name the ugly cases it handles by refusing, so the refusal reads as
  deliberate.]

## Back up your data

[Where the app's data lives (the exact file or folder), and the one
command that copies it somewhere safe.]

## Roll back

```sh
[The exact commands to return to the release commit recorded on the
release card. You proved these work during the rollback drill; paste the
verified commands, not your memory of them.]
```
