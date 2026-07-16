# Shared log: <work / project name>

> The coordination channel for more than one agent working the same job.
> Every agent reads this before acting and appends after acting. It is
> the cheap alternative to a message bus: an append-only shared note.
> Newest at the bottom. The index up top is how an agent catches up fast.

## Active agents

- <agent-id> — <what it owns>
- <agent-id> — <what it owns>

## Index

- HH:MM <agent-id> — <one line: claimed / did / released>
- HH:MM <agent-id> — ...

---

## HH:MM — <agent-id>

**Claiming:** <the unit of work this agent is taking, so others do not
step on it>

**Did:** <what changed>

**Releasing / handing off:** <what is now free for another agent, or
what the next agent should pick up>

---

## HH:MM — <agent-id>

**Claiming:**

**Did:**

**Releasing / handing off:**

---

When this works and when it does not: an append-only shared note scales
further than you expect for a handful of agents on one body of work.
Once you have many agents, high write contention, or need guaranteed
ordering, graduate to a real message bus or queue. Not before.
