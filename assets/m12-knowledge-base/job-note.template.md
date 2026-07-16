# job-<name> (job / SOP index note)

One-line summary: <what this job produces and when you run it>

Last reviewed: YYYY-MM-DD

## When to run this

<Trigger: a schedule, an event, a request shape. How the agent knows
this job applies.>

## Context to load first

1. Read [[<domain>]] (the master note for this domain)
2. Read [[<relevant-detail-note>]]

## Steps

1. <First action. Be specific about the input and the expected output.>
2. <Next action.>
3. <Where the result goes: the destination, the file, the queue.>

## Definition of done

<The agent should be able to check this itself. What does a finished,
correct result look like?>

## Approval gate

- Can do without asking: <low-consequence, reversible steps>
- Must ask before: <irreversible, money, or public actions>

## Failure behavior

<What the agent does when blocked, missing context, or unsure. Default:
stop and ask rather than guess.>

## Log

At the end of this job, append to [[daily-log-YYYY-MM-DD]]: what was
done, what was decided, what is open.
