-- 012_fix_ethereum_rss.sql
-- Global Airdrop Hunter - Fix Ethereum RSS Feed
-- Version: 1.0.0

PRAGMA foreign_keys = ON;

-- Fix Ethereum blog RSS URL to working endpoint
UPDATE sources SET base_url = 'https://blog.ethereum.org/feed.xml', 
    config = '{"feed_url": "https://blog.ethereum.org/feed.xml", "keywords": ["airdrop", "claim", "rewards", "incentive", "testnet", "distribution", "launch", "staking"], "date_format": ""}',
    updated_at = datetime('now')
WHERE id = 'rss-ethereum-blog';