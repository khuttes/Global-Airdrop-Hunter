import asyncio
import sys
sys.path.insert(0, r'E:\Global Airdrop Hunter\backend')

async def test_health():
    from backend.core.adapters_galxe_layer3 import Layer3Adapter
    from backend.core.adapters_impl import RSSAdapter
    from backend.core.models import Source, SourceType
    
    # Test Layer3
    print('Testing Layer3...')
    layer3_source = Source(id="layer3", name="Layer3", type=SourceType.API, base_url="https://api.layer3.xyz/graphql", config={"campaign_ids": [], "include_completed": False, "min_xp": 0, "networks": []}, rate_limit=30, timeout=30)
    adapter = Layer3Adapter(layer3_source)
    try:
        healthy = await adapter.health_check()
        print('  Layer3 health_check: {}'.format(healthy))
        if hasattr(adapter, 'close'):
            await adapter.close()
    except Exception as e:
        print('  Layer3 ERROR: {}'.format(e))
        import traceback
        traceback.print_exc()
    
    # Test RSS
    print('Testing RSS (Ethereum Blog)...')
    rss_source = Source(id="rss-ethereum-blog", name="Ethereum Foundation Blog", type=SourceType.RSS, base_url="https://blog.ethereum.org/rss.xml", config={"feed_url": "https://blog.ethereum.org/rss.xml", "keywords": ["airdrop", "claim", "rewards", "incentive", "testnet", "distribution", "launch"], "date_format": ""}, rate_limit=30, timeout=30)
    adapter2 = RSSAdapter(rss_source)
    try:
        healthy = await adapter2.health_check()
        print('  RSS health_check: {}'.format(healthy))
    except Exception as e:
        print('  RSS ERROR: {}'.format(e))
        import traceback
        traceback.print_exc()

asyncio.run(test_health())