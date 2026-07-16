# Module 14 — Guardrails reusable module

Output validation, PII redaction, prompt-injection test patterns. Drop
into a Python project to gate LLM-generated content before it leaves
the agent. Includes a 50+ test prompt-injection corpus to stress-test
your own systems.

## What's in here

```
m14-guardrails/
├── README.md
├── requirements.txt
├── guardrails/
│   ├── __init__.py
│   ├── redact.py            # PII detection + redaction
│   ├── validate.py          # output validators (banned phrases, format,
│   │                          internal-leak detection, length sanity)
│   ├── jailbreak.py         # prompt injection detection (heuristic)
│   └── audit.py             # audit log helper
├── tests/
│   ├── test_redact.py
│   ├── test_validate.py
│   └── test_jailbreak.py
└── injection_corpus.json    # 50+ prompt-injection test cases
```

## Quick start

```bash
cd m14-guardrails
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

In production code:

```python
from guardrails.redact import redact, PIIType
from guardrails.validate import OutputValidator
from guardrails.jailbreak import detect_injection

# Before sending to the model
clean_input, redactions = redact(user_input, types={PIIType.SSN, PIIType.CREDIT_CARD})

# Run the model

# Before sending to the user / customer
validator = OutputValidator(
    banned_phrases=["guaranteed refund", "we will fix this"],
    max_length=2000,
    block_internal_hostnames=True,
)
result = validator.check(model_output)
if not result.passed:
    log_for_human_review(model_output, result.failures)
else:
    deliver(model_output)
```

## What this module does NOT do

- Replace a security review for high-stakes deployments.
- Catch every possible jailbreak. Prompt injection is unsolved; the
  injection_corpus is for stress-testing, not certification.
- Handle every PII pattern. The defaults cover credit cards, SSN, phone,
  email. Add domain-specific patterns (Medicare numbers, account IDs,
  internal employee IDs) per your context.
- Make decisions about what to do when validation fails. That is the
  caller's job; this module returns structured failure info.

## License

MIT.
