---
template: self-critique-loop
version: 1.0.0
model_class: mid_size_or_frontier
default_temperature: 0.4
default_max_tokens: 1500
eval_set: ./eval/self-critique-loop.yaml
---

# Pattern overview

Three calls per output:

1. **Draft call.** Produce a first version against the user prompt.
2. **Critique call.** Same model rates its own output against a rubric;
   produces structured criticism with specific issues to fix.
3. **Revision call.** Same model rewrites incorporating the critique.

This pattern is the cheapest quality lift available for subjective tasks
(writing, code review, content review). Costs 3x a single call but
catches obvious issues before they reach production.

# Rubric template

```
Rate the draft 1-10 on each axis:
- Clarity: would a smart non-expert understand?
- Specificity: are claims concrete or vague?
- Voice: does it sound natural or AI-generated?
- Length: too long, too short, or right?
- Accuracy: any factual claims that need verification?

Then list 3 specific weaknesses to fix in the next draft.
```

# Implementation sketch

```python
def write_with_critique(prompt: str, max_iterations: int = 2) -> str:
    draft = call_model(prompt)

    for _ in range(max_iterations):
        critique = call_model(
            f"Draft:\n{draft}\n\nRubric:\n{RUBRIC}\n\nProduce structured critique."
        )

        # Bail out early if all axes scored 8+
        if not has_low_scores(critique, threshold=8):
            break

        revision_prompt = (
            f"Original prompt: {prompt}\n\n"
            f"Previous draft: {draft}\n\n"
            f"Critique: {critique}\n\n"
            f"Rewrite the draft addressing every weakness. "
            f"Keep what worked; fix what did not."
        )
        draft = call_model(revision_prompt)

    return draft
```

# Notes on tuning this template

- Temperature 0.4 in the draft + revision steps is a balance: low enough
  to be coherent, high enough to actually rewrite (not just rubber-stamp).
  Temperature 0 in critique because the rubric should produce consistent
  scores across runs.
- Sycophancy bias: the model is biased toward saying its own output is
  good. Compensate with explicit "what would bad output look like" in the
  rubric, and cap iterations at 2-3.
- Diminishing returns are sharp after iteration 2-3. Three iterations is
  the practical cap; beyond that you are paying for noise.
- For high-stakes content (where the cost of a bad output is real),
  swap the critique-call model for a stronger one than the draft model.
  Asymmetric quality (cheap drafter, expensive critic) often produces
  the best per-dollar output.
