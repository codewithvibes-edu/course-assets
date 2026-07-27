# Application contract: [app name]

Written before a provider is chosen, because the contract is about YOUR
promise, and the provider is an implementation detail behind it. The tests
in lesson 7 treat every line here as a claim to check.

## The job

One sentence: [summarizer / extractor / classifier] that takes [input]
and produces [output] for [the one user].

## Accepted input

| Question | Answer |
| --- | --- |
| Format(s) accepted | |
| Maximum size (chars or bytes, a number) | |
| What happens to input OVER the limit | refused with a message, before any network call |
| Encoding assumptions | |

## Validated output

| Question | Answer |
| --- | --- |
| Shape (free text, or a structure with named fields) | |
| If structured: what validates it, and when | after the done event, never on partial text |
| Where partial text may be shown | display only, marked as partial |
| Where partial text may never go | saved results, downstream parsing, logs |

## Limits and budgets

| Budget | Number | What happens when it fires |
| --- | --- | --- |
| Request timeout | s | visible failure, outcome logged as timeout |
| Max history turns (if conversational) | | oldest dropped, drop count visible |
| Max cost per run (if calculable) | | |

## Failure behavior (one row per failure the app can meet)

| Failure | User sees | App does | Logged outcome |
| --- | --- | --- | --- |
| bad credential | | | auth |
| rate limit | | wait the stated time or stop; never hammer | rate_limit |
| invalid input (theirs) | | | bad_input |
| server error | | | server |
| timeout | | no false "completed" | timeout |
| malformed / partial stream | | partial never presented as final | malformed |
| user cancel | | clean exit, partial marked partial | canceled |

## Data sensitivity

| Question | Answer |
| --- | --- |
| Data class of the input (public / internal / personal / regulated) | |
| What leaves the machine, exactly | |
| What the provider may retain (from THEIR current policy page, dated) | |
| What must never be logged | prompt and output content, credentials |
| What the usage log records instead | route, model, latency, usage, request id, outcome |
