# Connection threat model (lesson 6)

One page per connection profile. The profile stores metadata and a
pointer; this page proves you know where the secret actually lives and
what path your data walks.

## Profile facts (safe to commit)

| Field | Value |
| --- | --- |
| Logical ID | |
| Adapter ID | |
| Base URL | |
| Model ID | |
| Privacy class (public / internal / personal / regulated) | |
| Declared capabilities + last-tested date | |

## The secret (never in the profile, never on this page)

| Question | Answer |
| --- | --- |
| Where the value lives (env var name / keychain entry / vault path) | |
| Who can read that location | |
| How it reaches the process (and what would log it by accident) | |
| Rotation story: how you would replace it in under five minutes | |
| The fail-closed check: what happens when the pointer resolves to nothing | [paste the actual error message; it should name the pointer, not the value] |

## The data path

| Question | Answer |
| --- | --- |
| What leaves the machine on each request, exactly | |
| What the provider's CURRENT policy says it retains (dated) | |
| What raw_debug may contain, and what redaction strips | |
| Which privacy classes of data this connection may receive | |
| The capability gate that fails closed when a feature is missing | [name the check and paste its one passed test] |
