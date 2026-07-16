"""Ingestion patterns: files, APIs, webhooks, queues, idempotency."""

from .records import IngestRecord, canonicalize, hash_record
from .idempotency import IdempotencyStore
from .files import ingest_pdf, ingest_csv, ingest_jsonl
from .api_pull import APIIngester, RateLimited, PermanentError
from .queue import QueueClient
from .worker import Worker

__all__ = [
    "IngestRecord",
    "canonicalize",
    "hash_record",
    "IdempotencyStore",
    "ingest_pdf",
    "ingest_csv",
    "ingest_jsonl",
    "APIIngester",
    "RateLimited",
    "PermanentError",
    "QueueClient",
    "Worker",
]
