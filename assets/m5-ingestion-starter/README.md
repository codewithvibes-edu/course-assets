# Module 5 — Ingestion pipeline starter

Reference Python implementation of the ingestion patterns from module 5.
Files (PDF / CSV / JSON), APIs (with cursor + retries + rate-limit
handling), webhooks (with signature verification + idempotency), a
Postgres-backed queue, and a worker pattern.

This is educational reference code that runs end-to-end with toy data.
Real production deployments need adaptations covered in module 13
(cost / reliability) and module 14 (safety).

## What's in here

```
m5-ingestion-starter/
├── README.md
├── requirements.txt
├── ingestion/
│   ├── __init__.py
│   ├── files.py          # PDF / CSV / JSON ingestion
│   ├── api_pull.py       # cursor-based paginated API ingestion with retry
│   ├── webhooks.py       # FastAPI webhook handler with signature verify
│   ├── queue.py          # Postgres-as-queue (FOR UPDATE SKIP LOCKED)
│   ├── worker.py         # generic worker that drains the queue
│   ├── idempotency.py    # idempotency-key store
│   └── records.py        # canonical record schema + helpers
├── examples/
│   ├── pull_news_api.py  # worked example: paginated news API ingestion
│   └── ingest_pdfs.py    # worked example: ingest a folder of PDFs
├── sql/
│   ├── 0001_queue.sql    # queue + idempotency tables
│   └── 0002_records.sql  # ingested records table
└── tests/
    ├── test_files.py
    ├── test_api_pull.py
    └── test_idempotency.py
```

## Quick start

```bash
cd m5-ingestion-starter
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the file-ingest worked example against the included sample dir
python examples/ingest_pdfs.py --input-dir sample_pdfs --output out.jsonl

# Run tests
pytest
```

## Patterns covered

### File ingestion

- PDF text extraction with pdfplumber (native-text PDFs).
- CSV iteration with `csv.DictReader` plus encoding sniffing.
- JSON / JSONL streaming with `ijson` for large files.
- Every output record carries `source_path`, `ingested_at`, and a
  `source_id` so downstream code can trace back.

### API pull

- Cursor-based pagination with persistent state (resume after crash).
- Exponential backoff on 429 (rate limit) and 5xx errors.
- `Retry-After` header respected when present.
- Distinguishes transient errors (retry) from permanent ones (alert).
- Idempotent upsert keyed on the source's natural ID.

### Webhook handling

- FastAPI route with HMAC signature verification.
- Idempotency key stored in Postgres before any side-effects run.
- Synchronous handler returns 200 fast (queue the work async).
- Replay support: re-receiving a known event is a no-op.

### Postgres queue

- Standard "queue table" pattern with `FOR UPDATE SKIP LOCKED`.
- Visibility timeout so a crashed worker does not lose the item.
- Dead-letter handoff after N failed attempts.
- Worker pattern that drains the queue with backoff.

### Idempotency

- A small `idempotency_keys` table records every event ID processed.
- Insert-and-check pattern: handlers attempt to insert the key first;
  if it already exists, skip.

## What this is NOT

- A scraping framework. Module 5 covers scraping caveats; this starter
  does not include scraper code.
- A full streaming platform. Continuous streams (WebSockets, Kafka)
  need different patterns; module 5 references them but the starter
  focuses on the more common pull / webhook / file shapes.
- Production-ready as-is. Wire trace logging (module 12), budget caps
  (module 13), and PII redaction (module 14) before treating it as
  shippable for any real workload.

## License

MIT.
