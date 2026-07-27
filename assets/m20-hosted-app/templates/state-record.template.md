# State record: what this app remembers, sends, and forgets (lesson 5)

The provider remembers nothing between requests. Everything the next turn
needs, the app sends again, which means state is a decision you make on
every request, not a feature the API has.

## The diagram (fill in the four boxes)

```
              +---------------------------+
 user input ->|  SENT on every request:   |-> provider (sees ONLY this)
              |  _______________________  |
              +---------------------------+
              |  RETAINED locally:        |
              |  what: ________________   |
              |  bound: _______________   |
              |  dropped when: ________   |
              +---------------------------+
              |  DISCARDED immediately:   |
              |  _______________________  |
              +---------------------------+
              |  REDACTED before sending: |
              |  _______________________  |
              +---------------------------+
```

## The bound, proven

| Question | Answer |
| --- | --- |
| History cap (a number, from configuration) | |
| What drops when the cap is hit | oldest turn first |
| How the drop is visible (not silent) | |
| The behavior check you ran when the bound was reached | [the chat transcript line showing "sending N turns; dropped: M" with the service confirming N] |

## What this is not

Durable memory, summaries of dropped turns, and retrieval over past
conversations are real tools with a real module (m12). At this scale, a
bound you can explain and prove beats a memory you cannot. If the app
genuinely needs to remember more than the cap, write that as a version-two
requirement and keep version one honest.
