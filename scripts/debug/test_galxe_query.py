import asyncio
import aiohttp

async def test():
    async with aiohttp.ClientSession() as session:
        query = """
        query GetPopularSpaces($first: Int) {
            popularSpaces(first: $first) {
                id
            }
        }
        """
        async with session.post(
            'https://graphigo.prd.galaxy.eco/query',
            json={'query': query, 'variables': {'first': 20}},
            timeout=30
        ) as resp:
            print('Popular spaces status:', resp.status)
            data = await resp.json()
            print('Data:', data)

asyncio.run(test())