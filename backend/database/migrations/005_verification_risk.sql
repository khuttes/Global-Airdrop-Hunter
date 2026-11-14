-- 005_verification_risk.sql
-- Add verification and risk intelligence tables
-- Version: 1.0.0

PRAGMA foreign_keys = ON;

-- Official domain verification cache
CREATE TABLE IF NOT EXISTS domain_verification (
    domain TEXT PRIMARY KEY,
    is_official INTEGER NOT NULL DEFAULT 0,
    registrar TEXT,
    creation_date TIMESTAMP,
    expiry_date TIMESTAMP,
    ssl_valid INTEGER NOT NULL DEFAULT 0,
    ssl_issuer TEXT,
    ssl_expiry TIMESTAMP,
    dns_records TEXT,  -- JSON array of DNS records
    whois_data TEXT,   -- JSON object
    verified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verification_source TEXT NOT NULL,  -- 'whois', 'ssl', 'dns', 'project_confirmed'
    confidence REAL NOT NULL DEFAULT 0.0
);

CREATE INDEX IF NOT EXISTS idx_domain_verification_official ON domain_verification(is_official);
CREATE INDEX IF NOT EXISTS idx_domain_verification_verified ON domain_verification(verified_at);

-- Risk rules with versions
CREATE TABLE IF NOT EXISTS risk_rules (
    id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL UNIQUE,
    version INTEGER NOT NULL DEFAULT 1,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,  -- 'security', 'financial', 'verification', 'technical', 'quality', 'transparency'
    severity TEXT NOT NULL,  -- 'low', 'medium', 'high', 'critical'
    weight INTEGER NOT NULL DEFAULT 10,  -- 0-100
    is_critical_override INTEGER NOT NULL DEFAULT 0,  -- if 1, triggers critical regardless of score
    is_active INTEGER NOT NULL DEFAULT 1,
    logic_type TEXT NOT NULL,  -- 'keyword', 'regex', 'domain_check', 'contract_check', 'custom'
    logic_config TEXT,  -- JSON configuration for the rule
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risk_rules_rule_id ON risk_rules(rule_id);
CREATE INDEX IF NOT EXISTS idx_risk_rules_category ON risk_rules(category);
CREATE INDEX IF NOT EXISTS idx_risk_rules_severity ON risk_rules(severity);
CREATE INDEX IF NOT EXISTS idx_risk_rules_active ON risk_rules(is_active);

-- Campaign verification assessments
CREATE TABLE IF NOT EXISTS campaign_verification (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    verification_status TEXT NOT NULL,  -- 'officially_corroborated', 'independently_corroborated', 'unverified', 'suspicious', 'expired', 'withdrawn'
    confidence REAL NOT NULL DEFAULT 0.0,
    primary_evidence_urls TEXT,  -- JSON array of primary source URLs
    secondary_evidence_urls TEXT,  -- JSON array of secondary source URLs
    assessed_by TEXT NOT NULL DEFAULT 'system',  -- 'system', 'user', 'analyst'
    assessed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    UNIQUE(campaign_id)
);

CREATE INDEX IF NOT EXISTS idx_campaign_verification_status ON campaign_verification(verification_status);
CREATE INDEX IF NOT EXISTS idx_campaign_verification_campaign ON campaign_verification(campaign_id);

-- Risk assessments with findings
CREATE TABLE IF NOT EXISTS campaign_risk_assessment (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    risk_score INTEGER NOT NULL DEFAULT 50,  -- 0-100
    risk_level TEXT NOT NULL DEFAULT 'medium',  -- 'low', 'medium', 'high', 'critical'
    critical_override INTEGER NOT NULL DEFAULT 0,
    total_findings INTEGER NOT NULL DEFAULT 0,
    high_findings INTEGER NOT NULL DEFAULT 0,
    critical_findings INTEGER NOT NULL DEFAULT 0,
    assessed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assessed_by TEXT NOT NULL DEFAULT 'system',
    UNIQUE(campaign_id)
);

CREATE INDEX IF NOT EXISTS idx_risk_assessment_campaign ON campaign_risk_assessment(campaign_id);
CREATE INDEX IF NOT EXISTS idx_risk_assessment_level ON campaign_risk_assessment(risk_level);

-- Individual risk findings with rule references
CREATE TABLE IF NOT EXISTS risk_findings (
    id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    rule_id TEXT NOT NULL,
    rule_version INTEGER NOT NULL,
    finding TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT,
    evidence_url TEXT,
    matched_content TEXT,  -- What triggered the rule
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risk_findings_campaign ON risk_findings(campaign_id);
CREATE INDEX IF NOT EXISTS idx_risk_findings_rule ON risk_findings(rule_id);
CREATE INDEX IF NOT EXISTS idx_risk_findings_severity ON risk_findings(severity);

-- Insert default risk rules
INSERT OR IGNORE INTO risk_rules (id, rule_id, version, name, description, category, severity, weight, is_critical_override, logic_type, logic_config) VALUES
    ('rr-001', 'credential_request', 1, 'Credential Request', 'Campaign asks for private keys, seed phrases, or passwords', 'security', 'critical', 100, 1, 'keyword', '{"keywords": ["private key", "seed phrase", "mnemonic", "recovery phrase", "wallet password", "keystore", "json wallet"]}'),
    ('rr-002', 'upfront_payment', 1, 'Upfront Payment Required', 'Campaign requires payment to participate or claim', 'financial', 'critical', 100, 1, 'keyword', '{"keywords": ["pay to claim", "send eth", "send bnb", "deposit required", "gas fee required", "pay gas", "payment required"]}'),
    ('rr-003', 'domain_impersonation', 1, 'Domain Impersonation', 'Campaign URL mimics official project domain', 'security', 'high', 75, 0, 'domain_check', '{"check_typosquatting": true, "check_subdomain_spoofing": true}'),
    ('rr-004', 'no_primary_evidence', 1, 'No Primary Evidence', 'No verifiable official source corroborates the campaign', 'verification', 'high', 50, 0, 'custom', '{"requires_official_source": true}'),
    ('rr-005', 'unverified_contract', 1, 'Unverified Contract', 'Smart contract not verified on block explorer', 'technical', 'high', 40, 0, 'contract_check', '{"explorer_apis": ["etherscan", "bscscan", "polygonscan", "arbiscan"]}'),
    ('rr-006', 'unrealistic_guarantee', 1, 'Unrealistic Guarantee', 'Promises guaranteed returns or impossible yields', 'financial', 'high', 60, 0, 'keyword', '{"keywords": ["guaranteed", "100% return", "risk free", "cannot lose", "guaranteed profit", "fixed return"]}'),
    ('rr-007', 'unexpected_permissions', 1, 'Unexpected Permissions', 'Requests excessive token approvals or contract permissions', 'security', 'high', 50, 0, 'contract_check', '{"check_approval_functions": ["approve", "setApprovalForAll", "permit", "increaseAllowance"]}'),
    ('rr-008', 'recent_domain', 1, 'Recently Registered Domain', 'Campaign domain registered within last 30 days', 'security', 'medium', 30, 0, 'domain_check', '{"max_age_days": 30}'),
    ('rr-009', 'no_social_presence', 1, 'No Social Presence', 'Project has no verifiable social media or community', 'verification', 'medium', 25, 0, 'custom', '{"requires_social": true}'),
    ('rr-010', 'anonymous_team', 1, 'Anonymous Team', 'Project team is completely anonymous with no doxxing', 'verification', 'medium', 20, 0, 'custom', '{"requires_team_info": true}'),
    ('rr-011', 'single_source', 1, 'Single Source Only', 'Campaign only found on one unverified source', 'verification', 'medium', 20, 0, 'custom', '{"min_sources": 2}'),
    ('rr-012', 'copy_paste_content', 1, 'Copied Content', 'Campaign description appears copied from other campaigns', 'quality', 'low', 15, 0, 'content_similarity', '{"threshold": 0.85}'),
    ('rr-013', 'poor_grammar', 1, 'Poor Grammar/Spelling', 'Official communications have significant errors', 'quality', 'low', 10, 0, 'custom', '{"check_spelling": true}'),
    ('rr-014', 'no_roadmap', 1, 'No Public Roadmap', 'Project lacks a public development roadmap', 'transparency', 'low', 15, 0, 'custom', '{"requires_roadmap": true}'),
    ('rr-015', 'unverified_social', 1, 'Unverified Social Accounts', 'Social media accounts not verified or recently created', 'verification', 'low', 10, 0, 'custom', '{"check_verification_badges": true}');

-- Insert migration record
INSERT OR IGNORE INTO schema_migrations (id, name) VALUES ('005', '005_verification_risk.sql');