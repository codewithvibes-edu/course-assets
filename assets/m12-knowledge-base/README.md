# Module 12 — Knowledge-base starter kit

A markdown-and-links knowledge base for an agent. No vector store, no
service to babysit. You organize a domain into one master/index note
that links to detail notes, the agent reads the master and follows only
the links it needs, and a few maintenance habits keep the base from
rotting. This is the architecture from Module 12, in files you can copy.

## What's in here

```
m12-knowledge-base/
├── README.md
├── master-note.template.md       # the index note for one domain
├── job-note.template.md          # a job/SOP as an index note
├── daily-log.template.md         # agent-written session log, index at top
├── shared-agent-log.template.md  # append-only coordination log for >1 agent
└── anti-bloat-rules.md           # drop into your agent's standing instructions
```

## How to use it

1. Pick one domain. Copy `master-note.template.md` to `<domain>.md` and
   fill the one-line summary and the links. Each `[[link]]` is a detail
   note you write next.
2. For each recurring task, copy `job-note.template.md` to
   `job-<name>.md`. A job note is a standard operating procedure that is
   really an index: the agent reads it, follows its links, and ends up
   with both the steps and the context it needs.
3. Point your agent at the master note (or the job note) on boot. It
   self-loads the domain by traversing links instead of you pasting
   context in.
4. Have the agent write a `daily-log.template.md` at the end of a session
   and after anything significant. The human does not write these.
5. Paste `anti-bloat-rules.md` into the agent's standing instructions so
   it appends instead of spawning, and prune on a cadence.

## The one rule that matters

Keep the always-loaded layer small. Push detail into linked files the
agent retrieves only when relevant. An index that outgrows the context
window truncates silently, and the agent gets quietly dumber while
looking just as confident. Density beats volume.
