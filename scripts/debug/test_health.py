import asyncio
import sys
sys.path.insert(0, r'E:\Global Airdrop Hunter\backend')

async def test_health():
    from backend.core.adapters_impl import (
        CoinGeckoAdapter, DefiLlamaAdapter, GitHubAdapter, RSSAdapter
    )
    from backend.core.adapters_galxe_layer3 import GalxeAdapter
    from backend.core.models import Source, SourceType
    
    sources = [
        Source(id="coingecko", name="CoinGecko", type=SourceType.API, base_url="https://api.coingecko.com/api/v3", config={"include_new_tokens": True, "min_market_cap_usd": 1000000, "categories": []}, rate_limit=50, timeout=30),
        Source(id="defillama", name="DefiLlama", type=SourceType.API, base_url="https://api.llama.fi", config={"include_new_protocols": True, "min_tvl_usd": 1000000, "chains": []}, rate_limit=100, timeout=30),
        Source(id="github", name="GitHub", type=SourceType.API, base_url="https://api.github.com", config={"organizations": ["ethereum", "arbitrum", "optimism", "polygon", "base", "uniswap", "aave", "lidofinance"], "repositories": [], "keywords": ["airdrop", "claim", "rewards", "incentive", "testnet", "distribution", "merkle"]}, rate_limit=60, timeout=30),
        Source(id="galxe", name="Galxe", type=SourceType.API, base_url="https://graphigo.prd.galaxy.eco/query", config={"space_ids": [], "include_ended": False, "min_rewards": 1, "campaign_types": []}, rate_limit=30, timeout=30),
        Source(id="rss-ethereum-blog", name="Ethereum Foundation Blog", type=SourceType.RSS, base_url="https://blog.ethereum.org/feed.xml", config={"feed_url": "https://blog.ethereum.org/feed.xml", "keywords": ["airdrop", "claim", "rewards", "incentive", "testnet", "distribution", "launch", "staking"], "date_format": ""}, rate_limit=30, timeout=30),
        Source(id="rss-base-blog", name="Base Blog", type=SourceType.RSS, base_url="https://base.org/blog/rss.xml", config={"feed_url": "https://base.org/blog/rss.xml", "keywords": ["airdrop", "claim", "rewards", "incentive", "testnet", "distribution", "launch"], "date_format": ""}, rate_limit=30, timeout=30),
        Source(id="rss-polygon-blog", name="Polygon Blog", type=SourceType.RSS, base_url="https://blog.polygon.technology/rss.xml", config={"feed_url": "https://blog.polygon.technology/rss.xml", "keywords": ["airdrop", "claim", "rewards", "incentive", "testnet", "distribution", "launch"], "date_format": ""}, rate_limit=30, timeout=30),
    ]
    
    adapters = {
        "coingecko": CoinGeckoAdapter,
        "defillama": DefiLlamaAdapter,
        "github": GitHubAdapter,
        "galxe": GalxeAdapter,
        "rss-ethereum-blog": RSSAdapter,
        "rss-base-blog": RSSAdapter,
        "rss-polygon-blog": RSSAdapter,
    }
    
    print('Testing health checks for', len(sources), 'sources...')
    
    for source in sources:
        adapter_cls = adapters.get(source.id)
        if adapter_cls:
            adapter = adapter_cls(source)
            try:
                healthy = await adapter.health_check()
                status = "HEALTHY" if healthy else "UNHEALTHY"
                print('  {} ({}): {}'.format(source.id, source.name, status))
                if hasattr(adapter, 'close'):
                    await adapter.close()
            except Exception as e:
                print('  {} ({}): ERROR - {}'.format(source.id, source.name, e))
            await asyncio.sleep(0.5)  # Small delay between requests
        else:
            print('  {} ({}): NO ADAPTER CLASS'.format(source.id, source.name))

asyncio.run(test_health())