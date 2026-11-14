import asyncio
import sys
sys.path.insert(0, r'E:\Global Airdrop Hunter\backend')

async def test():
    from backend.core.adapters_impl import RSSAdapter
    from backend.core.models import Source, SourceType
    
    source = Source(
        id="rss-ethereum-blog", 
        name="Ethereum Foundation Blog", 
        type=SourceType.RSS, 
        base_url="https://blog.ethereum.org/feed.xml", 
        config={"feed_url": "https://blog.ethereum.org/feed.xml", "keywords": ["airdrop", "claim", "rewards", "incentive", "testnet", "distribution", "launch", "staking"], "date_format": ""}, 
        rate_limit=30, 
        timeout=30
    )
    
    adapter = RSSAdapter(source)
    try:
        healthy = await adapter.health_check()
        print('Health check result:', healthy)
    except Exception as e:
        print('ERROR:', e)
        import traceback
        traceback.print_exc()

asyncio.run(test())