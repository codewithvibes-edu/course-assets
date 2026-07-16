# Module 6 — Cleaning + dedup + schema reusable module

Reference Python module for the cleaning operations from module 6.
HTML / boilerplate / encoding cleanup, three flavors of dedup
(exact / fuzzy / embedding), and schema enforcement. Drop into a
project and pipe ingested records (Module 5 output) through it before
chunking + retrieval.

## What's in here

```
m6-cleaning/
├── README.md
├── requirements.txt
├── cleaning/
│   ├── __init__.py
│   ├── html.py              # strip HTML, extract main content
│   ├── encoding.py          # mojibake fixes, normalize quotes/dashes
│   ├── boilerplate.py       # strip common email/PDF/HTML boilerplate
│   ├── dedup.py             # exact + fuzzy (Jaccard) + embedding-based
│   └── schema.py            # Pydantic helpers for enforcement
└── tests/
    ├── test_html.py
    ├── test_encoding.py
    ├── test_dedup.py
    └── test_schema.py
```

## Quick start

```bash
cd m6-cleaning
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## Usage

```python
from cleaning.html import extract_main_content
from cleaning.encoding import normalize_text
from cleaning.boilerplate import strip_email_boilerplate
from cleaning.dedup import exact_dedup, fuzzy_dedup
from cleaning.schema import EnforcedRecord

# Pipeline shape: ingested -> clean -> dedup -> schema-enforce -> store
text = extract_main_content(raw_html)
text = normalize_text(text)
text = strip_email_boilerplate(text)
records = [EnforcedRecord.model_validate(r) for r in records]
records = fuzzy_dedup(records, threshold=0.92)
```

## Three dedup flavors

| Flavor            | When                                                    | Cost                                        |
| ----------------- | ------------------------------------------------------- | ------------------------------------------- |
| `exact_dedup`     | identical content (different IDs)                       | O(n) hashing                                |
| `fuzzy_dedup`     | near-identical (whitespace, capitalization, formatting) | O(n²) Jaccard, falls to MinHash for n > 10k |
| `embedding_dedup` | semantically similar (paraphrases)                      | O(n²) cosine; needs sentence-transformers   |

## License

MIT.
