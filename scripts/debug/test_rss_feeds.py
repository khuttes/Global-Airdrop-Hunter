import asyncio
import sys
import os
sys.path.insert(0, r'E:\Global Airdrop Hunter\backend')

os.environ['DATABASE_PATH'] = r'C:\Users\windows11\AppData\Local\GlobalAirdropHunter\app.db'

async def test_rss_feeds():
    from backend.core.adapters_impl import RSSAdapter
    from backend.core.models import Source, SourceType
    
    feeds = [
        ("rss-ethereum-blog", "Ethereum Foundation Blog", "https://blog.ethereum.org/feed.xml"),
        ("rss-base-blog", "Base Blog", "https://base.org/blog/rss.xml"),
        ("rss-polygon-blog", "Polygon Blog", "https://blog.polygon.technology/rss.xml"),
    ]
    
    for sid, name, url in feeds:
        print('Testing {}...'.format(name))
        source = Source(
            id=sid, name=name, type=SourceType.RSS, base_url=url, 
            config={"feed_url": url, "keywords": ["airdrop", "claim", "rewards", "incentive", "testnet", "distribution", "launch"], "date_format": ""}, 
            rate_limit=30, timeout=30
        )
        adapter = RSSAdapter(source)
        try:
            result = await adapter.discover()
            print('  Campaigns: {}, Errors: {}'.format(len(result.campaigns), result.errors))
            for c in result.campaigns[:3]:
                print('    - {}'.format(c.name[:60]))
        except Exception as e:
            print('  ERROR: {}'.format(e))
            import traceback
            traceback.print_exc()

asyncio.run(test_rss_feeds())