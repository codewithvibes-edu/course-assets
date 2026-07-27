# Release card: [app name] v[0.1]

Small ceremony, disproportionate payoff. This card is the difference
between "it worked at some point" and "this exact state works, and here is
how to get back to it."

| Field | Value |
| --- | --- |
| App name | |
| Version | v0.1 |
| Release date | |
| Known-good commit | [full hash, from `git rev-parse HEAD` at the release commit] |
| Dependency lock state | [lockfile committed at that hash, or "stdlib only"] |
| Start command | |
| Test command (last run: passing) | |
| Stop behavior | |
| Data location (what to back up) | |
| Rollback command | [e.g. `git checkout <known-good-commit>` or the restore steps from the README] |
| Rollback drill performed | [date + where the terminal evidence is saved] |
| Demo recorded | [date + filename. Under two minutes: core job, one ugly input, one limitation said out loud.] |

## Known limitations at release

- [Same list as the README. If the lists drift, one of them is lying.]

## Version two ideas (parked, on purpose)

- [Everything that tried to sneak into version one during the build.]
