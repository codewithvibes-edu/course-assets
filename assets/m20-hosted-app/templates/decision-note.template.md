# Decision note: direct HTTP vs SDK (lesson 3)

You ran the same request both ways. Record what you actually observed,
pick ONE implementation to keep, and say why. There is no universally
right answer; there is a right answer for this app, this team (you), and
this month. That is what makes it a decision instead of a fashion.

## The same request, two ways

| Observation | Direct HTTP | SDK / thin client |
| --- | --- | --- |
| Lines of code for one working call | | |
| Dependencies added (count, from the lockfile) | | |
| Defaults it set without asking (timeouts? retries? headers?) | | |
| What an error looks like (raw body visible, or wrapped type?) | | |
| Streaming: events visible, or abstracted? | | |
| Types: yours, or provider-shaped objects through your code? | | |

## The decision

**Keeping:** [direct HTTP / the SDK], for this app.

**Because:** [2-3 sentences grounded in the table, not in vibes.]

**The coupling either way:** list every place in the code that knows which
provider this is (endpoint paths, header names, field names, error shapes,
event names). Short list or long, WRITE IT, because Module 21 starts by
measuring exactly this list, and you just did the measuring early.
