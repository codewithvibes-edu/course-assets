---
template: few-shot-runner
version: 1.0.0
model_class: mid_size_or_frontier
default_temperature: 0.3
default_max_tokens: 1200
eval_set: ./eval/few-shot-runner.yaml
---

# Pattern overview

Few-shot prompting with a rotating example pool. Useful when you have a
library of past good outputs (your own prior writing, sample translations,
exemplar code reviews) and want new outputs to match the established
voice or style.

The pattern: at runtime, sample 3-5 examples from a larger pool. Sampling
strategies:

- **Random:** simple; works when the pool is uniform.
- **Most similar:** embed the user input + every pool example; pick the
  top-N by cosine similarity. Voice consistency improves; cost goes up.
- **Diverse:** force the sample to span different cases (one short, one
  long, one edge-case). Reduces overfitting to a single style.

# System prompt

You produce {{output_type}} that matches the voice and style of the
provided examples. Examples represent the desired voice; the user input
defines the new task. Match the examples in tone, structure, and depth.

Do not copy phrases verbatim from examples. Do not output anything outside
the requested {{output_type}}. Use the examples as style guides, not
content sources.

# Example sampling code (Python)

```python
import random
import numpy as np
from sentence_transformers import SentenceTransformer

class ExamplePool:
    def __init__(self, examples: list[dict], embedding_model: str = "BAAI/bge-base-en-v1.5"):
        """examples: list of {"input": str, "output": str}"""
        self.examples = examples
        model = SentenceTransformer(embedding_model)
        inputs = [e["input"] for e in examples]
        self.input_embeddings = model.encode(inputs, normalize_embeddings=True)
        self.model = model

    def sample_random(self, n: int = 3) -> list[dict]:
        return random.sample(self.examples, min(n, len(self.examples)))

    def sample_most_similar(self, query: str, n: int = 3) -> list[dict]:
        q = self.model.encode(query, normalize_embeddings=True)
        sims = self.input_embeddings @ q
        order = np.argsort(sims)[::-1][:n]
        return [self.examples[i] for i in order]

    def sample_diverse(self, n: int = 3) -> list[dict]:
        """
        Naive diverse sampling: cluster examples by embedding similarity,
        pick one from each of the n largest clusters. Real diverse sampling
        uses better algorithms (k-means, MMR); this is the starter version.
        """
        if len(self.examples) <= n:
            return list(self.examples)
        # Pick first; then iteratively pick the example most dissimilar
        # from those already picked.
        picked = [random.randrange(len(self.examples))]
        while len(picked) < n:
            picked_emb = self.input_embeddings[picked]
            sims = self.input_embeddings @ picked_emb.T
            max_sim_per = sims.max(axis=1)
            # Avoid picking something already picked
            for i in picked:
                max_sim_per[i] = float("inf")
            picked.append(int(max_sim_per.argmin()))
        return [self.examples[i] for i in picked]
```

# Prompt assembly

```python
def assemble_prompt(system: str, examples: list[dict], user_input: str) -> str:
    parts = [system]
    for ex in examples:
        parts.append(f"\n\nInput: {ex['input']}\nOutput: {ex['output']}")
    parts.append(f"\n\nInput: {user_input}\nOutput:")
    return "".join(parts)
```

# Notes on tuning this template

- 3-5 examples is the sweet spot. More examples bloat the prompt and
  produce diminishing returns; fewer examples lose voice consistency.
- Most-similar sampling beats random when the pool spans multiple
  sub-styles. Random beats most-similar when the pool is small and uniform.
- Voice quality is sensitive to example quality. Curate the pool; remove
  examples that produced bad outputs in real use. Prune aggressively.
- Output validation matters: even a well-tuned few-shot prompt produces
  the occasional off-style output. A self-critique loop on top
  (`self-critique-loop.md`) catches the worst cases.
