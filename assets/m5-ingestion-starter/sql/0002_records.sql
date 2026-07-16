-- Ingested records table. Each row is one IngestRecord.
-- The unique constraint on (source_type, source_name, source_id) gives
-- us cheap upsert + dedup at the storage edge.

CREATE TABLE IF NOT EXISTS ingested_records (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type   TEXT NOT NULL,
    source_name   TEXT NOT NULL,
    source_id     TEXT NOT NULL,
    payload       JSONB NOT NULL,
    metadata      JSONB NOT NULL DEFAULT '{}'::jsonb,
    content_hash  TEXT NOT NULL,
    ingested_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_type, source_name, source_id)
);

CREATE INDEX IF NOT EXISTS idx_records_ingested_at
    ON ingested_records (ingested_at DESC);

CREATE INDEX IF NOT EXISTS idx_records_content_hash
    ON ingested_records (content_hash);
