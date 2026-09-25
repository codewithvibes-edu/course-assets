# Module 12 — Eval harness starter

Reference Python eval harness for grading prompt outputs. Three eval
types covered in module 12: deterministic, model-graded, and human
review. CLI to run a suite, structured JSON output, regression
comparison against a previous run.

## What's in here

```
m12-eval-harness/
├── README.md
├── requirements.txt
├── eval_runner.py            # CLI: run a suite, save results
├── compare.py                # CLI: compare current vs prior run
├── eval_harness/
│   ├── __init__.py
│   ├── types.py              # EvalCase, EvalResult, Score
│   ├── deterministic.py      # exact-match, regex, JSON-schema, length
│   ├── model_graded.py       # rubric grader using a stronger model
│   ├── human.py              # CLI prompt-and-record workflow
│   └── runner.py             # orchestrates the three layers
├── examples/
│   ├── classifier.suite.yaml # eval suite for a structured-output classifier
│   └── prompts.py            # the prompt being evaluated (placeholder)
└── tests/
    └── test_deterministic.py
```

## Quick start

```bash
cd m12-eval-harness
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the example eval suite
python eval_runner.py --suite examples/classifier.suite.yaml --output results.json

# Compare a new run against a prior baseline
python compare.py --baseline baseline.json --current results.json
```

## Suite file shape

```yaml
suite_name: 'classifier'
prompt_module: 'examples.prompts'
prompt_function: 'classify'

cases:
  - id: 'billing-001'
    input: 'My card was charged twice for the same plan.'
    deterministic:
      - type: json_schema
        schema_path: 'examples/classifier.schema.json'
      - type: field_value
        field: 'category'
        expected: 'billing'
    model_graded:
      - rubric: 'Is the suggested_action appropriate for the urgency?'
        grader_model: 'claude-opus-5-5'
        passing_threshold: 0.8
    human_review_sample_rate: 0.05
```

## Three eval types covered

### Deterministic (cheap, fast, run on every change)

- Exact match
- JSON schema validity
- Regex match
- Field presence + field value
- Length sanity (min/max)
- Banned-phrase absence

### Model-graded (slower, costs API calls, rubric-based)

- A stronger model (Claude Opus 5.5, GPT-6 Astra) scores the output of a weaker
  one against a rubric.
- Useful for subjective quality (writing tone, code style, edge case
  handling).
- Sycophancy bias: the model is biased toward saying its own output is
  good. Use a different model than the one being evaluated where
  practical, and sample human review periodically to calibrate.

### Human review (slow, expensive, the only ground truth)

- CLI walks through a sampled subset of outputs, prompts the reviewer
  for a 1-5 score and a free-form note, records to JSON.
- Sample rate configurable per suite (default 5%).
- The recorded reviews feed back into the model-graded calibration.

## Running in CI

Add to `.github/workflows/ci.yml`:

```yaml
- name: Run prompt evals
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    python eval_runner.py --suite eval_suites/all.yaml --output current.json
    python compare.py --baseline eval_suites/baseline.json --current current.json
    # compare.py exits non-zero if regression > N%
```

## License

MIT.
