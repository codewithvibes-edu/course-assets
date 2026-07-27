# Dependency review: [app name]

Every dependency in the lockfile is code you now ship, written by someone
you have never met. One row per DIRECT dependency the build added. Five
questions, one verdict each: accept, replace, or remove.

| Dependency | Where it comes from (registry page read?) | Lockfile delta (how many packages arrived with it?) | Install-time scripts? | Maintained? (last release, open issues glanced) | Could stdlib or something already here do it? | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| [name] | | | | | | accept / replace / remove |

## Verdict notes

For every **replace** or **remove**: what happens instead, in one sentence.

For every **accept**: the one-sentence reason it earns its place. "The agent
picked it" is not a reason. "Parsing RFC-compliant CSVs with embedded
newlines by hand is a bug farm and this is the standard tool" is.

## The three shapes to scan for on any diff, forever

1. **A credential where credentials must never be:** hardcoded in source,
   printed in a log line, committed in a config file. Keys live in `.env`,
   which lives in `.gitignore`, which you verified in the setup lab.
2. **A package added for work the project could already do:** a network
   library for one request, a color library for two ANSI codes, a date
   library for one timestamp. Each one is supply chain you now carry.
3. **A script whose behavior is wider than its name:** "backup" that also
   deletes, "format" that also fetches, "test" that also publishes. Read
   the body of every script a diff adds, every time. The name is a claim,
   never a fact.
