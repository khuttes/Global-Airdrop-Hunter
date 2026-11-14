-- 004_deduplication_tables.sql
-- Add tables for deduplication audit trail and field change history
-- Version: 1.0.0

PRAGMA foreign_keys = ON;

-- Campaign merge audit trail
CREATE TABLE IF NOT EXISTS campaign_merge_audit (
    id TEXT PRIMARY KEY,
    surviving_campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    merged_campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    merged_campaign_stable_id TEXT NOT NULL,
    match_reasons TEXT NOT NULL,  -- JSON array of reasons
    similarity_score REAL NOT NULL,
    field_comparison TEXT NOT NULL,  -- JSON object
    merged_by TEXT NOT NULL DEFAULT 'system',  -- 'system' or 'user'
    merged_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(merged_campaign_id)
);

CREATE INDEX IF NOT EXISTS idx_merge_audit_surviving ON campaign_merge_audit(surviving_campaign_id);
CREATE INDEX IF NOT EXISTS idx_merge_audit_merged ON campaign_merge_audit(merged_campaign_id);

-- Add missing columns to campaign_field_history if they don't exist
-- (SQLite doesn't support ADD COLUMN IF NOT EXISTS, so we use a workaround)
-- Check if change_source column exists
-- If not, add it and source_id column

-- We'll handle this in Python migration code instead

-- Campaign lifecycle events
CREATE TABLE IF NOT EXISTS campaign_lifecycle_events (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,  -- 'created', 'updated', 'status_changed', 'expired', 'withdrawn', 'revived', 'merged'
    old_status TEXT,
    new_status TEXT,
    event_data TEXT,  -- JSON with additional context
    detected_by TEXT NOT NULL DEFAULT 'system',  -- 'system', 'user', 'source'
    source_id TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lifecycle_campaign ON campaign_lifecycle_events(campaign_id);
CREATE INDEX IF NOT EXISTS idx_lifecycle_type ON campaign_lifecycle_events(event_type);
CREATE INDEX IF NOT EXISTS idx_lifecycle_created ON campaign_lifecycle_events(created_at DESC);

-- Insert migration record
INSERT OR IGNORE INTO schema_migrations (id, name) VALUES ('004', '004_deduplication_tables.sql');