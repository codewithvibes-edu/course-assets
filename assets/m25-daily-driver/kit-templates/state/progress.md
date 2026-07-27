# Progress: [job]

Append-only. One line per state change: timestamp, stage, what happened,
evidence path. The fresh-session resume reads this top to bottom and
should never need the old transcript.
