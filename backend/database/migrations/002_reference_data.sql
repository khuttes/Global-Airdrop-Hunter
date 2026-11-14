-- 002_reference_data.sql
-- Global Airdrop Hunter - Reference Data Tables
-- Version: 1.0.0

PRAGMA foreign_keys = ON;

-- Campaign categories
CREATE TABLE IF NOT EXISTS campaign_categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    description TEXT,
    icon TEXT,
    color TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Blockchain networks
CREATE TABLE IF NOT EXISTS blockchains (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    native_token TEXT,
    rpc_url TEXT,
    explorer_url TEXT,
    chain_id INTEGER,
    is_testnet INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Risk rules
CREATE TABLE IF NOT EXISTS risk_rules (
    id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL UNIQUE,
    version INTEGER NOT NULL DEFAULT 1,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    weight INTEGER NOT NULL DEFAULT 10,
    is_active INTEGER NOT NULL DEFAULT 1,
    logic TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert default campaign categories
INSERT OR IGNORE INTO campaign_categories (id, name, slug, description, icon, color, display_order) VALUES
    ('cat-airdrop', 'Airdrop', 'airdrop', 'Token distribution to eligible addresses', 'gift', '#1f6feb', 1),
    ('cat-nft', 'NFT', 'nft', 'Non-fungible token campaigns and mints', 'image', '#a371f7', 2),
    ('cat-testnet', 'Testnet', 'testnet', 'Testnet participation and activities', 'flask-conical', '#d29922', 3),
    ('cat-reward', 'Reward', 'reward', 'Staking, liquidity, and protocol rewards', 'award', '#3fb950', 4);

-- Insert default blockchain networks
INSERT OR IGNORE INTO blockchains (id, name, slug, native_token, rpc_url, explorer_url, chain_id, is_testnet, is_active, display_order) VALUES
    ('bc-eth', 'Ethereum', 'ethereum', 'ETH', 'https://eth.llamarpc.com', 'https://etherscan.io', 1, 0, 1, 1),
    ('bc-polygon', 'Polygon', 'polygon', 'MATIC', 'https://polygon-rpc.com', 'https://polygonscan.com', 137, 0, 1, 2),
    ('bc-arbitrum', 'Arbitrum', 'arbitrum', 'ETH', 'https://arb1.arbitrum.io/rpc', 'https://arbiscan.io', 42161, 0, 1, 3),
    ('bc-optimism', 'Optimism', 'optimism', 'ETH', 'https://mainnet.optimism.io', 'https://optimistic.etherscan.io', 10, 0, 1, 4),
    ('bc-bsc', 'BNB Smart Chain', 'bsc', 'BNB', 'https://bsc-dataseed.binance.org', 'https://bscscan.com', 56, 0, 1, 5),
    ('bc-base', 'Base', 'base', 'ETH', 'https://mainnet.base.org', 'https://basescan.org', 8453, 0, 1, 6),
    ('bc-linea', 'Linea', 'linea', 'ETH', 'https://rpc.linea.build', 'https://lineascan.build', 59144, 0, 1, 7),
    ('bc-zksync', 'zkSync Era', 'zksync', 'ETH', 'https://mainnet.era.zksync.io', 'https://explorer.zksync.io', 324, 0, 1, 8),
    ('bc-scroll', 'Scroll', 'scroll', 'ETH', 'https://rpc.scroll.io', 'https://scrollscan.com', 534352, 0, 1, 9),
    ('bc-eth-sepolia', 'Ethereum Sepolia', 'ethereum-sepolia', 'ETH', 'https://rpc.sepolia.org', 'https://sepolia.etherscan.io', 11155111, 1, 1, 10),
    ('bc-arb-sepolia', 'Arbitrum Sepolia', 'arbitrum-sepolia', 'ETH', 'https://sepolia-rollup.arbitrum.io/rpc', 'https://sepolia.arbiscan.io', 421614, 1, 1, 11),
    ('bc-op-sepolia', 'Optimism Sepolia', 'optimism-sepolia', 'ETH', 'https://sepolia.optimism.io', 'https://sepolia-optimism.etherscan.io', 11155420, 1, 1, 12);

-- Insert default risk rules
INSERT OR IGNORE INTO risk_rules (id, rule_id, version, name, description, category, severity, weight, is_active, logic) VALUES
    ('rr-001', 'credential_request', 1, 'Credential Request', 'Campaign asks for private keys, seed phrases, or passwords', 'security', 'critical', 100, 1, 'detect_credential_request'),
    ('rr-002', 'upfront_payment', 1, 'Upfront Payment Required', 'Campaign requires payment to participate or claim', 'financial', 'critical', 100, 1, 'detect_upfront_payment'),
    ('rr-003', 'domain_impersonation', 1, 'Domain Impersonation', 'Campaign URL mimics official project domain', 'security', 'high', 75, 1, 'detect_domain_spoofing'),
    ('rr-004', 'no_primary_evidence', 1, 'No Primary Evidence', 'No verifiable official source corroborates the campaign', 'verification', 'high', 50, 1, 'no_official_source'),
    ('rr-005', 'unverified_contract', 1, 'Unverified Contract', 'Smart contract not verified on block explorer', 'technical', 'high', 40, 1, 'contract_unverified'),
    ('rr-006', 'unrealistic_guarantee', 1, 'Unrealistic Guarantee', 'Promises guaranteed returns or impossible yields', 'financial', 'high', 60, 1, 'detect_unrealistic_claims'),
    ('rr-007', 'unexpected_permissions', 1, 'Unexpected Permissions', 'Requests excessive token approvals or contract permissions', 'security', 'high', 50, 1, 'detect_excessive_approvals'),
    ('rr-008', 'recent_domain', 1, 'Recently Registered Domain', 'Campaign domain registered within last 30 days', 'security', 'medium', 30, 1, 'domain_age_lt_30'),
    ('rr-009', 'no_social_presence', 1, 'No Social Presence', 'Project has no verifiable social media or community', 'verification', 'medium', 25, 1, 'no_social_verification'),
    ('rr-010', 'anonymous_team', 1, 'Anonymous Team', 'Project team is completely anonymous with no doxxing', 'verification', 'medium', 20, 1, 'team_anonymous'),
    ('rr-011', 'single_source', 1, 'Single Source Only', 'Campaign only found on one unverified source', 'verification', 'medium', 20, 1, 'single_unverified_source'),
    ('rr-012', 'copy_paste_content', 1, 'Copied Content', 'Campaign description appears copied from other campaigns', 'quality', 'low', 15, 1, 'detect_duplicate_content'),
    ('rr-013', 'poor_grammar', 1, 'Poor Grammar/Spelling', 'Official communications have significant errors', 'quality', 'low', 10, 1, 'detect_poor_quality'),
    ('rr-014', 'no_roadmap', 1, 'No Public Roadmap', 'Project lacks a public development roadmap', 'transparency', 'low', 15, 1, 'no_roadmap'),
    ('rr-015', 'unverified_social', 1, 'Unverified Social Accounts', 'Social media accounts not verified or recently created', 'verification', 'low', 10, 1, 'unverified_social');

-- Indexes for reference data
CREATE INDEX IF NOT EXISTS idx_campaign_categories_slug ON campaign_categories(slug);
CREATE INDEX IF NOT EXISTS idx_blockchains_slug ON blockchains(slug);
CREATE INDEX IF NOT EXISTS idx_blockchains_chain_id ON blockchains(chain_id);
CREATE INDEX IF NOT EXISTS idx_risk_rules_rule_id ON risk_rules(rule_id);
CREATE INDEX IF NOT EXISTS idx_risk_rules_category ON risk_rules(category);