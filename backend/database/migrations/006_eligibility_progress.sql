-- 006_eligibility_progress.sql
-- Add enhanced eligibility and progress tracking tables
-- Version: 1.0.0

PRAGMA foreign_keys = ON;

-- Add new columns to campaign_eligibility for progress tracking
ALTER TABLE campaign_eligibility ADD COLUMN progress_status TEXT NOT NULL DEFAULT 'potentially_eligible';
-- progress_status: 'potentially_eligible', 'user_reported_met', 'user_reported_not_met', 'not_applicable', 'claim_available', 'claimed'

ALTER TABLE campaign_eligibility ADD COLUMN user_notes TEXT;
ALTER TABLE campaign_eligibility ADD COLUMN completed_at TIMESTAMP;

-- User progress tracking table (separate from evidence-based eligibility)
CREATE TABLE IF NOT EXISTS user_eligibility_progress (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    requirement_id TEXT NOT NULL REFERENCES campaign_eligibility(id) ON DELETE CASCADE,
    user_status TEXT NOT NULL DEFAULT 'unknown',
    -- user_status: 'unknown', 'met', 'not_met', 'in_progress', 'not_applicable'
    user_notes TEXT,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(campaign_id, requirement_id)
);

CREATE INDEX IF NOT EXISTS idx_user_progress_campaign ON user_eligibility_progress(campaign_id);
CREATE INDEX IF NOT EXISTS idx_user_progress_requirement ON user_eligibility_progress(requirement_id);

-- Campaign claim tracking
CREATE TABLE IF NOT EXISTS campaign_claims (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    claim_type TEXT NOT NULL, -- 'airdrop', 'nft_mint', 'reward_claim', 'testnet_reward'
    claim_url TEXT,
    transaction_hash TEXT,
    block_number INTEGER,
    network TEXT,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'submitted', 'confirmed', 'failed', 'cancelled'
    claimed_at TIMESTAMP,
    confirmed_at TIMESTAMP,
    user_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_campaign_claims_campaign ON campaign_claims(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_claims_status ON campaign_claims(status);

-- Add migration record
INSERT OR IGNORE INTO schema_migrations (id, name) VALUES ('006', '006_eligibility_progress.sql');