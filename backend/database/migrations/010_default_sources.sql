-- 010_default_sources.sql
-- Global Airdrop Hunter - Default Source Seeds
-- Version: 1.0.0
-- Seeds the sources table with pre-configured adapters for real internet discovery

PRAGMA foreign_keys = ON;

-- CoinGecko - Token metadata, new listings, trending tokens
INSERT OR IGNORE INTO sources (id, name, type, base_url, config, rate_limit, timeout, status, enabled, created_at, updated_at) VALUES
(
    'coingecko',
    'CoinGecko',
    'api',
    'https://api.coingecko.com/api/v3',
    '{"include_new_tokens": true, "min_market_cap_usd": 1000000, "categories": []}',
    50,
    30,
    'enabled',
    1,
    datetime('now'),
    datetime('now')
);

-- DefiLlama - Protocol TVL, yields, new protocol listings
INSERT OR IGNORE INTO sources (id, name, type, base_url, config, rate_limit, timeout, status, enabled, created_at, updated_at) VALUES
(
    'defillama',
    'DefiLlama',
    'api',
    'https://api.llama.fi',
    '{"include_new_protocols": true, "min_tvl_usd": 1000000, "chains": []}',
    100,
    30,
    'enabled',
    1,
    datetime('now'),
    datetime('now')
);

-- GitHub - Official repositories, releases, documentation
INSERT OR IGNORE INTO sources (id, name, type, base_url, config, rate_limit, timeout, status, enabled, created_at, updated_at) VALUES
(
    'github',
    'GitHub',
    'api',
    'https://api.github.com',
    '{"organizations": ["ethereum", "arbitrum", "optimism", "polygon", "base", "uniswap", "aave", "lidofinance"], "repositories": [], "keywords": ["airdrop", "claim", "rewards", "incentive", "testnet", "distribution", "merkle"]}',
    60,
    30,
    'enabled',
    1,
    datetime('now'),
    datetime('now')
);

-- Galxe - Credential campaigns, NFTs, community rewards
INSERT OR IGNORE INTO sources (id, name, type, base_url, config, rate_limit, timeout, status, enabled, created_at, updated_at) VALUES
(
    'galxe',
    'Galxe',
    'api',
    'https://graphigo.prd.galaxy.eco/query',
    '{"space_ids": [], "include_ended": false, "min_rewards": 1, "campaign_types": []}',
    30,
    30,
    'enabled',
    1,
    datetime('now'),
    datetime('now')
);

-- Layer3 - DISABLED: No public GraphQL API available
-- INSERT OR IGNORE INTO sources (id, name, type, base_url, config, rate_limit, timeout, status, enabled, created_at, updated_at) VALUES
-- (
--     'layer3',
--     'Layer3',
--     'api',
--     'https://api.layer3.xyz/graphql',
--     '{"campaign_ids": [], "include_completed": false, "min_xp": 0, "networks": []}',
--     30,
--     30,
--     'enabled',
--     0,
--     datetime('now'),
--     datetime('now')
-- );

-- RSS Feeds - Official project blogs with working RSS endpoints
INSERT OR IGNORE INTO sources (id, name, type, base_url, config, rate_limit, timeout, status, enabled, created_at, updated_at) VALUES
(
    'rss-base-blog',
    'Base Blog',
    'rss',
    'https://base.org/blog/rss.xml',
    '{"feed_url": "https://base.org/blog/rss.xml", "keywords": ["airdrop", "claim", "rewards", "incentive", "testnet", "distribution", "launch"], "date_format": ""}',
    30,
    30,
    'enabled',
    1,
    datetime('now'),
    datetime('now')
);

INSERT OR IGNORE INTO sources (id, name, type, base_url, config, rate_limit, timeout, status, enabled, created_at, updated_at) VALUES
(
    'rss-polygon-blog',
    'Polygon Blog',
    'rss',
    'https://blog.polygon.technology/rss.xml',
    '{"feed_url": "https://blog.polygon.technology/rss.xml", "keywords": ["airdrop", "claim", "rewards", "incentive", "testnet", "distribution", "launch"], "date_format": ""}',
    30,
    30,
    'enabled',
    1,
    datetime('now'),
    datetime('now')
);

INSERT OR IGNORE INTO sources (id, name, type, base_url, config, rate_limit, timeout, status, enabled, created_at, updated_at) VALUES
(
    'rss-ethereum-blog',
    'Ethereum Foundation Blog',
    'rss',
    'https://ethereum.org/en/blog/rss.xml',
    '{"feed_url": "https://ethereum.org/en/blog/rss.xml", "keywords": ["airdrop", "claim", "rewards", "incentive", "testnet", "distribution", "launch", "staking"], "date_format": ""}',
    30,
    30,
    'enabled',
    1,
    datetime('now'),
    datetime('now')
);

-- Note: Arbitrum, Optimism blogs return 403/404 - disabled for now
-- INSERT OR IGNORE INTO sources (id, name, type, base_url, config, rate_limit, timeout, status, enabled, created_at, updated_at) VALUES
-- (
--     'rss-arbitrum-blog',
--     'Arbitrum Blog',
--     'rss',
--     'https://arbitrum.io/blog/rss.xml',
--     '{"feed_url": "https://arbitrum.io/blog/rss.xml", "keywords": ["airdrop", "claim", "rewards", "incentive", "testnet", "distribution", "launch"], "date_format": ""}',
--     30,
--     30,
--     'enabled',
--     0,
--     datetime('now'),
--     datetime('now')
-- );
-- 
-- INSERT OR IGNORE INTO sources (id, name, type, base_url, config, rate_limit, timeout, status, enabled, created_at, updated_at) VALUES
-- (
--     'rss-optimism-blog',
--     'Optimism Blog',
--     'rss',
--     'https://optimism.io/blog/rss.xml',
--     '{"feed_url": "https://optimism.io/blog/rss.xml", "keywords": ["airdrop", "claim", "rewards", "incentive", "testnet", "distribution", "launch"], "date_format": ""}',
--     30,
--     30,
--     'enabled',
--     0,
--     datetime('now'),
--     datetime('now')
-- );