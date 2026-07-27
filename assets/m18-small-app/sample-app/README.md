# snip

Keep terminal one-liners you keep forgetting. Save a command with tags the
moment it finally works; find it later with `search` or `list --tag`
instead of re-googling it. Local JSON file, standard library only.

## Install

Nothing to install. Python 3.10+ and this folder.

## Run it

```sh
python3 snippets.py add "lsof -i :8123" --tags ports,debug
python3 snippets.py list
python3 snippets.py search ports
python3 snippets.py delete 1
```

## Test it

```sh
python3 -m unittest discover -s tests -v
```

Seven tests, all mapped to requirement IDs in test-map.md.

## Stop it

Run-and-exit. Nothing stays resident.

## What it does not do (known limitations)

- No sync, no encryption, no shell-history integration (non-goals, see
  problem.md).
- Hand-editing snippets.json into invalid JSON makes snip refuse to run
  until you fix or remove the file. That refusal is deliberate: it will
  not silently replace your data.

## Back up your data

Everything lives in one file next to the script: `snippets.json`.
Copy it anywhere: `cp snippets.json ~/backups/snippets-$(date +%F).json`.

## Roll back

This folder ships as a worked example at its release state. If you have
been experimenting on it inside a git repo of your own making:

```sh
git restore .
```

returns it to your last commit. This app is also the target for the two
prepared exercises in ../exercises/; each briefing includes its own
cleanup steps.
