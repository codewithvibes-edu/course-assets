# Orchard Mock Runtime

The mock runtime does not think. It proves the operations: pull, serve,
bind, measure, stop, restart, recover, swap, promote, and roll back.

This is the course's fallback lane for a machine that cannot run the
pinned real small model. Every operation you perform here is real: a
real artifact with a real checksum, a real out-of-process HTTP server on
a real port, real state files, real failure recovery. Every piece of
CONTENT is a labeled course fixture. Nothing here downloads weights,
runs inference, allocates fake gigabytes, opens a non-loopback client
connection, shells out, or reads a credential. Standard-library Python
only, offline, text only.

## The Orchard namespace is reserved and fake

Every model name starting with `orchard` is a pretend course fixture.
The namespace matches no real repository, vendor, or license. There is
no hub URL to fetch from and no license to accept, because there is
nothing real to license. If you ever see an `orchard` model referenced
outside this course asset, someone is confused.

## What a mock run can and cannot prove

Can prove: pull and verification mechanics, service lifecycle, loopback
and exposure binds, port conflicts, stale-state recovery, adapter and
swap mechanics, comparison and promotion PLUMBING.

Cannot prove: model quality, quantization behavior, real context limits,
real memory use, accelerator residency, driver health, thermals, or
throughput on your hardware. Those claims need the real lane or the
course's recorded real-recipe read-alongs. Your route record for this
lane says `exercise-only mock route`, and it must never recommend Orchard
for real work.

Honest labels are load-bearing everywhere: reported memory says
`scenario-not-measurement`, timing says `scenario-not-benchmark`, usage
counts whitespace words and says so, and every generated content line
begins `[COURSE MOCK, NOT MODEL OUTPUT]`.

## Quick start

```sh
python3 orchard_runtime.py pull orchard-3b-instruct --state-dir .orchard-runtime
python3 orchard_runtime.py serve orchard-3b-instruct --state-dir .orchard-runtime --run-id local-001
python3 orchard_runtime.py ps --state-dir .orchard-runtime
python3 orchard_runtime.py stop --state-dir .orchard-runtime --run-id local-001
```

On Windows, use `python` instead of `python3`. The full per-OS walkthroughs
with expected output, stop, undo, and common errors live in `recipes/`.

Exit codes: 0 clean, 2 invalid command or model or request or port
conflict, 3 run not found, 4 planted mock out-of-memory, 5 artifact lock
needs recovery.

## Layout

```text
orchard_runtime.py      the whole runtime: CLI, HTTP and SSE server, atomic state
catalog.json            the fake model catalog and fixture strings
fixtures/eval-cases.json  ten fixed triage cases with planted failures
fixtures/golden/        byte-exact response and stream goldens
scripts/plant_failure.py  plants a stale artifact lock with a genuinely dead PID
scripts/make_goldens.py   regenerates goldens after an INTENTIONAL change
scripts/validate_recipes.py  stdlib recipe-schema validator
integration/            the m21 adapter, connection profile, swap proof, evidence template
recipes/                three OS fallback recipe records
tests/                  the whole test suite; python3 -m unittest discover -s tests
```

## Tests

```sh
python3 -m unittest discover -s tests -v
```

The suite runs offline with provider and model environment variables
unset. `tests/test_m21_contract.py` and everything under `integration/`
expect the Module 21 adapter kit next to this asset (or `CWV_M21_SRC`
pointing at its `src/`); every other test is self-contained.

## The adapter and the swap

`integration/adapter_local.py` imports the canonical types from the
Module 21 kit and passes the kit's shared contract suite unmodified. The
HTTP surface is a compatible-SHAPED subset of three routes, kept off the
Module 19 lab protocol on purpose, so the adapter lesson stays a real
lesson. `integration/swap_proof.py` merges the connection profile into
the m21 registry in-process, runs the kit's UNCHANGED `app_swap_demo.py`,
and saves checksum evidence that the application-code diff is empty.

## Deviations from the 06c asset tree, on purpose

- `tests/support.py`: shared test harness for starting and stopping real
  serve processes; not in the doc's tree.
- `scripts/validate_recipes.py`: gates 6 and 7 need schema validation and
  the jsonschema package is not standard library.
- `scripts/make_goldens.py`: gate 4 needs a reproducible way to
  regenerate goldens after an intentional fixture change.
- `integration/swap_proof.py`: the doc's literal swap command presumes
  your own m21 project; this script produces the same evidence
  reproducibly against the shipped kit.

## Accessibility

Plain ASCII, one fact per line, no color, no cursor tricks, no
animation. Progress prints as discrete lines, and `pull --quiet` drops
them entirely. Tables keep stable columns that only grow.
