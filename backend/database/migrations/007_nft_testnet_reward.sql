-- 007_nft_testnet_reward.sql
-- Add NFT, Testnet, and Reward specific fields
-- Version: 1.0.0

PRAGMA foreign_keys = ON;

-- NFT-specific fields for campaigns
ALTER TABLE campaigns ADD COLUMN nft_collection_name TEXT;
ALTER TABLE campaigns ADD COLUMN nft_collection_slug TEXT;
ALTER TABLE campaigns ADD COLUMN nft_mint_price TEXT;
ALTER TABLE campaigns ADD COLUMN nft_mint_currency TEXT;
ALTER TABLE campaigns ADD COLUMN nft_total_supply INTEGER;
ALTER TABLE campaigns ADD COLUMN nft_minted_supply INTEGER;
ALTER TABLE campaigns ADD COLUMN nft_mint_start TIMESTAMP;
ALTER TABLE campaigns ADD COLUMN nft_mint_end TIMESTAMP;
ALTER TABLE campaigns ADD COLUMN nft_whitelist_url TEXT;
ALTER TABLE campaigns ADD COLUMN nft_official_collection_url TEXT;
ALTER TABLE campaigns ADD COLUMN nft_marketplace_urls TEXT; -- JSON array
ALTER TABLE campaigns ADD COLUMN nft_royalty_percentage REAL;
ALTER TABLE campaigns ADD COLUMN nft_standard TEXT; -- ERC-721, ERC-1155, etc.

-- Testnet-specific fields for campaigns
ALTER TABLE campaigns ADD COLUMN testnet_network_name TEXT;
ALTER TABLE campaigns ADD COLUMN testnet_chain_id INTEGER;
ALTER TABLE campaigns ADD COLUMN testnet_rpc_url TEXT;
ALTER TABLE campaigns ADD COLUMN testnet_explorer_url TEXT;
ALTER TABLE campaigns ADD COLUMN testnet_faucet_url TEXT;
ALTER TABLE campaigns ADD COLUMN testnet_docs_url TEXT;
ALTER TABLE campaigns ADD COLUMN testnet_github_url TEXT;
ALTER TABLE campaigns ADD COLUMN testnet_tasks TEXT; -- JSON array of tasks
ALTER TABLE campaigns ADD COLUMN testnet_duration_days INTEGER;
ALTER TABLE campaigns ADD COLUMN testnet_reward_type TEXT; -- token, nft, points, etc.
ALTER TABLE campaigns ADD COLUMN testnet_reward_amount TEXT;

-- Reward-specific fields for campaigns
ALTER TABLE campaigns ADD COLUMN reward_token_symbol TEXT;
ALTER TABLE campaigns ADD COLUMN reward_token_address TEXT;
ALTER TABLE campaigns ADD COLUMN reward_token_decimals INTEGER;
ALTER TABLE campaigns ADD COLUMN reward_amount_per_user TEXT;
ALTER TABLE campaigns ADD COLUMN reward_total_pool TEXT;
ALTER TABLE campaigns ADD COLUMN reward_distribution_method TEXT; -- airdrop, claim, staking, etc.
ALTER TABLE campaigns ADD COLUMN reward_claim_start TIMESTAMP;
ALTER TABLE campaigns ADD COLUMN reward_claim_end TIMESTAMP;
ALTER TABLE campaigns ADD COLUMN reward_vesting_schedule TEXT; -- JSON
ALTER TABLE campaigns ADD COLUMN reward_apy REAL;
ALTER TABLE campaigns ADD COLUMN reward_lockup_period_days INTEGER;

-- Notification/Calendar tracking
CREATE TABLE IF NOT EXISTS campaign_events (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL, -- 'deadline', 'mint_start', 'mint_end', 'claim_start', 'claim_end', 'distribution', 'announcement', 'snapshot'
    event_title TEXT NOT NULL,
    event_description TEXT,
    event_date TIMESTAMP NOT NULL,
    is_all_day INTEGER NOT NULL DEFAULT 0,
    reminder_days_before INTEGER NOT NULL DEFAULT 1,
    is_notified INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_campaign_events_campaign ON campaign_events(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_events_date ON campaign_events(event_date);
CREATE INDEX IF NOT EXISTS idx_campaign_events_type ON campaign_events(event_type);

-- User notification preferences
CREATE TABLE IF NOT EXISTS user_notification_prefs (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    notify_deadline INTEGER NOT NULL DEFAULT 1,
    notify_mint_start INTEGER NOT NULL DEFAULT 1,
    notify_mint_end INTEGER NOT NULL DEFAULT 1,
    notify_claim_start INTEGER NOT NULL DEFAULT 1,
    notify_claim_end INTEGER NOT NULL DEFAULT 1,
    notify_distribution INTEGER NOT NULL DEFAULT 1,
    reminder_days_before INTEGER NOT NULL DEFAULT 1,
    in_app_enabled INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(campaign_id)
);

CREATE INDEX IF NOT EXISTS idx_user_notification_prefs_campaign ON user_notification_prefs(campaign_id);

-- Insert migration record
INSERT OR IGNORE INTO schema_migrations (id, name) VALUES ('007', '007_nft_testnet_reward.sql');