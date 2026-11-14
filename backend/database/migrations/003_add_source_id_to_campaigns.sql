-- 003_add_source_id_to_campaigns.sql
-- Add source_id column to campaigns table
-- Version: 1.0.0

PRAGMA foreign_keys = ON;

ALTER TABLE campaigns ADD COLUMN source_id TEXT;

CREATE INDEX IF NOT EXISTS idx_campaigns_source_id ON campaigns(source_id);