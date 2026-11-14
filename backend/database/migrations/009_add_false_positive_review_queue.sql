-- Migration: Add false_positive_review_queue table
CREATE TABLE IF NOT EXISTS false_positive_review_queue (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    trigger_rules TEXT NOT NULL,  -- JSON array
    status TEXT NOT NULL DEFAULT 'pending',
    priority TEXT NOT NULL DEFAULT 'medium',
    reviewer_notes TEXT,
    created_at TIMESTAMP NOT NULL,
    reviewed_at TIMESTAMP,
    reviewed_by TEXT,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_fprq_status_priority 
ON false_positive_review_queue(status, priority);