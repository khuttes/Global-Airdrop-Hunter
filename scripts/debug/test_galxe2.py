import asyncio
import aiohttp

async def test():
    async with aiohttp.ClientSession() as session:
        # Test introspection
        query = "{ __typename }"
        async with session.post(
            'https://graphigo.prd.galaxy.eco/query',
            json={'query': query},
            timeout=30
        ) as resp:
            print('Introspection status:', resp.status)
            data = await resp.json()
            print('Data:', data)

asyncio.run(test())