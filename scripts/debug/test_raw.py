import asyncio
import aiohttp
import sys
sys.path.insert(0, r'E:\Global Airdrop Hunter\backend')

async def test_raw():
    # Test Layer3 GraphQL endpoint directly
    print('Testing Layer3 GraphQL endpoint...')
    try:
        async with aiohttp.ClientSession() as session:
            query = "{ __typename }"
            async with session.post(
                "https://api.layer3.xyz/graphql",
                json={"query": query},
                timeout=30
            ) as response:
                print('  Status: {}'.format(response.status))
                text = await response.text()
                print('  Response: {}'.format(text[:200]))
    except Exception as e:
        print('  ERROR: {}'.format(e))
    
    # Test RSS feed directly
    print('Testing RSS feed...')
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://blog.ethereum.org/rss.xml",
                timeout=30
            ) as response:
                print('  Status: {}'.format(response.status))
                text = await response.text()
                print('  Response: {}'.format(text[:200]))
    except Exception as e:
        print('  ERROR: {}'.format(e))
    
    # Test other RSS feeds
    feeds = [
        "https://arbitrum.io/blog/rss.xml",
        "https://optimism.io/blog/rss.xml",
        "https://base.org/blog/rss.xml",
        "https://blog.polygon.technology/rss.xml",
    ]
    for feed in feeds:
        print('Testing {}...'.format(feed))
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(feed, timeout=30) as response:
                    print('  Status: {}'.format(response.status))
        except Exception as e:
            print('  ERROR: {}'.format(e))

asyncio.run(test_raw())