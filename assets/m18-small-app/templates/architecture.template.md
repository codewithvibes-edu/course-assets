# Architecture: [app name]

Two designs, same anatomy for both, one winner, reasons on paper. Ask the
agent for both; the comparison and the verdict are yours.

## Design A: [name it, e.g. "single script + JSON file"]

- **Components:** [the parts and what each owns]
- **Files:** [what files exist and why each one]
- **Dependencies:** [every package beyond the standard library, or "none"]
- **Data flow:** [where input enters -> what touches it -> where the result
  lands. Napkin-drawable or it is not understood.]

## Design B: [name it]

- **Components:**
- **Files:**
- **Dependencies:**
- **Data flow:**

## The heavyweight checkpoint

Any of the following appearing in EITHER design needs one written sentence
justifying it against a requirement ID. No sentence, no component.

| Component | In design | Justifying sentence (or "cut") |
| --- | --- | --- |
| Web framework | | |
| Database | | |
| Background process / queue | | |
| Hosted service | | |

## Verdict

**Winner:** Design [A/B].

**Why, against the acceptance criteria:** [2-4 sentences. "Simpler" is a
fine reason when it is true. If the bigger design won, the extra component
earns its keep against a specific criterion, named here.]

**What the rejected design got right:** [1-2 sentences. This is the answer
to future-you asking "wait, why did we not just..."]
