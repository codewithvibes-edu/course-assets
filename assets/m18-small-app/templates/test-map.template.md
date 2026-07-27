# Test map: [app name]

Every acceptance criterion maps to evidence. Unit test, integration test,
and "I ran it and watched" are all legitimate evidence; a criterion mapped
to nothing is a promise nobody is keeping, and a test mapped to no
criterion is decoration.

| Criterion ID | What it promises (short) | Evidence type | Where the evidence lives | Passing? |
| --- | --- | --- | --- | --- |
| AC-1.1 | | unit / integration / manual | [test file::test name, or the exact manual command + what you saw] | |
| AC-1.2 | | | | |
| AC-2.1 | | | | |
| AC-3.1 | | | | |
| AC-U.1 | | | | |

## Orphan check (run at the end of lesson 5)

Tests that do not map to any criterion above:

| Test | Verdict |
| --- | --- |
| [name] | delete, or write the missing criterion (in that order of likelihood) |

## Manual evidence log

For every "manual" row: the exact command you ran, the input you fed it,
and what you watched happen. "It worked" is not evidence. "Ran
`python3 app.py report bad.csv`, got the two bad rows listed at the bottom
with line numbers" is.
