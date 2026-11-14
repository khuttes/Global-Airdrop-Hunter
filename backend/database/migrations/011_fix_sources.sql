-- 011_fix_sources.sql
-- Global Airdrop Hunter - Fix Source Seeds
-- Version: 1.0.0
-- Corrects RSS feed URLs and disables Layer3 (no public API)

PRAGMA foreign_keys = ON;

-- Disable Layer3 (no public GraphQL API)
UPDATE sources SET enabled = 0, status = 'disabled', updated_at = datetime('now') WHERE id = 'layer3';

-- Fix Ethereum blog RSS URL
UPDATE sources SET base_url = 'https://ethereum.org/en/blog/rss.xml', 
    config = '{"feed_url": "https://ethereum.org/en/blog/rss.xml", "keywords": ["airdrop", "claim", "rewards", "incentive", "testnet", "distribution", "launch", "staking"], "date_format": ""}',
    updated_at = datetime('now')
WHERE id = 'rss-ethereum-blog';

-- Disable Arbitrum blog (403)
UPDATE sources SET enabled = 0, status = 'disabled', updated_at = datetime('now') WHERE id = 'rss-arbitrum-blog';

-- Disable Optimism blog (404)
UPDATE sources SET enabled = 0, status = 'disabled', updated_at = datetime('now') WHERE id = 'rss-optimism-blog';

-- Ensure Base and Polygon blogs are enabled
UPDATE sources SET enabled = 1, status = 'enabled', updated_at = datetime('now') WHERE id IN ('rss-base-blog', 'rss-polygon-blog');