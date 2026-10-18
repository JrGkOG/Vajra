-- Hash-chained audit ledger (blockchain layer)
-- Run once in the Supabase SQL editor.
--
-- Every row commits to the one before it:
--     entry_hash = SHA-256( prev_hash || canonical_json(entry) )
-- Editing or deleting any historical row breaks every hash after it, and the
-- head of this chain is periodically pinned on-chain by VajraRegistry.
--
-- UNIQUE(seq) is the fork guard: if two API workers try to append at the same
-- position, the database rejects the second and it retries on the new head.

CREATE TABLE IF NOT EXISTS ledger_entries (
    seq         BIGINT PRIMARY KEY,
    entry       JSONB  NOT NULL,       -- the exact body that was hashed
    prev_hash   TEXT   NOT NULL,       -- 64 hex chars; 00..00 for genesis
    entry_hash  TEXT   NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ledger_entries_created ON ledger_entries(created_at DESC);

COMMENT ON TABLE ledger_entries IS
  'Append-only hash-chained mirror of audit_logs + activity_logs; head anchored on-chain';
