-- Queue + dead-letter + idempotency tables.
-- Apply with: psql ... -f sql/0001_queue.sql

CREATE TABLE IF NOT EXISTS queue (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue        TEXT NOT NULL,
    payload      JSONB NOT NULL,
    status       TEXT NOT NULL DEFAULT 'pending',
    attempts     INTEGER NOT NULL DEFAULT 0,
    visible_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    last_error   TEXT
);

CREATE INDEX IF NOT EXISTS idx_queue_pending
    ON queue (queue, visible_at)
    WHERE status = 'pending';

CREATE TABLE IF NOT EXISTS dead_letter (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue       TEXT NOT NULL,
    payload     JSONB NOT NULL,
    attempts    INTEGER NOT NULL,
    last_error  TEXT,
    moved_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS idempotency_keys (
    key        TEXT PRIMARY KEY,
    scope      TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata   JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_idempotency_scope_created
    ON idempotency_keys (scope, created_at DESC);
