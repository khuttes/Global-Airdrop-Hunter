-- 001_initial_schema.sql
-- Global Airdrop Hunter - Initial Database Schema
-- Version: 1.0.0

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- Campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    id TEXT PRIMARY KEY,
    stable_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    project TEXT,
    type TEXT NOT NULL DEFAULT 'airdrop',
    network TEXT,
    description TEXT,
    official_url TEXT,
    campaign_url TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    verification_status TEXT NOT NULL DEFAULT 'unverified',
    risk_level TEXT NOT NULL DEFAULT 'medium',
    risk_score INTEGER NOT NULL DEFAULT 50 CHECK (risk_score >= 0 AND risk_score <= 100),
    deadline TIMESTAMP,
    snapshot_date TIMESTAMP,
    discovered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for campaigns
CREATE INDEX IF NOT EXISTS idx_campaigns_stable_id ON campaigns(stable_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_type ON campaigns(type);
CREATE INDEX IF NOT EXISTS idx_campaigns_network ON campaigns(network);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_verification ON campaigns(verification_status);
CREATE INDEX IF NOT EXISTS idx_campaigns_risk ON campaigns(risk_level);
CREATE INDEX IF NOT EXISTS idx_campaigns_discovered ON campaigns(discovered_at DESC);
CREATE INDEX IF NOT EXISTS idx_campaigns_deadline ON campaigns(deadline);
CREATE INDEX IF NOT EXISTS idx_campaigns_name_search ON campaigns(name, project);

-- Campaign Evidence table
CREATE TABLE IF NOT EXISTS campaign_evidence (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    source_type TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    title TEXT,
    snippet TEXT,
    fetched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verified INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_evidence_campaign ON campaign_evidence(campaign_id);
CREATE INDEX IF NOT EXISTS idx_evidence_hash ON campaign_evidence(content_hash);

-- Campaign Risk Findings table
CREATE TABLE IF NOT EXISTS campaign_risk_findings (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    rule_id TEXT NOT NULL,
    rule_version INTEGER NOT NULL,
    finding TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT,
    evidence_url TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risk_campaign ON campaign_risk_findings(campaign_id);
CREATE INDEX IF NOT EXISTS idx_risk_severity ON campaign_risk_findings(severity);

-- Campaign Eligibility Requirements table
CREATE TABLE IF NOT EXISTS campaign_eligibility (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    requirement TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'unknown',
    evidence_url TEXT,
    source TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_eligibility_campaign ON campaign_eligibility(campaign_id);

-- Campaign Field History table
CREATE TABLE IF NOT EXISTS campaign_field_history (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source TEXT
);

CREATE INDEX IF NOT EXISTS idx_field_history_campaign ON campaign_field_history(campaign_id);
CREATE INDEX IF NOT EXISTS idx_field_history_field ON campaign_field_history(field_name);

-- Sources table
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    base_url TEXT NOT NULL,
    config TEXT NOT NULL DEFAULT '{}',
    rate_limit INTEGER NOT NULL DEFAULT 60,
    timeout INTEGER NOT NULL DEFAULT 30,
    status TEXT NOT NULL DEFAULT 'enabled',
    enabled INTEGER NOT NULL DEFAULT 1,
    last_health_check TIMESTAMP,
    last_scan TIMESTAMP,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    total_scans INTEGER NOT NULL DEFAULT 0,
    total_records INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status);
CREATE INDEX IF NOT EXISTS idx_sources_enabled ON sources(enabled);

-- Scan History table
CREATE TABLE IF NOT EXISTS scan_history (
    id TEXT PRIMARY KEY,
    sources_scanned TEXT NOT NULL DEFAULT '[]',
    campaigns_found INTEGER NOT NULL DEFAULT 0,
    campaigns_new INTEGER NOT NULL DEFAULT 0,
    campaigns_updated INTEGER NOT NULL DEFAULT 0,
    errors TEXT NOT NULL DEFAULT '[]',
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scan_history_started ON scan_history(started_at DESC);

-- User Tracked Campaigns table
CREATE TABLE IF NOT EXISTS user_tracked (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'tracking',
    progress TEXT NOT NULL DEFAULT '{}',
    notes TEXT,
    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(campaign_id)
);

CREATE INDEX IF NOT EXISTS idx_user_tracked_campaign ON user_tracked(campaign_id);

-- User Notes table
CREATE TABLE IF NOT EXISTS user_notes (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_notes_campaign ON user_notes(campaign_id);

-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert default settings
INSERT OR IGNORE INTO settings (key, value) VALUES
    ('theme', 'dark'),
    ('auto_refresh_minutes', '30'),
    ('notifications_enabled', '1'),
    ('database_version', '1');