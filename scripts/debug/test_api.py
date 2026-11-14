import asyncio
import aiohttp
import sys
sys.path.insert(0, r'E:\Global Airdrop Hunter\backend')

async def test_api():
    # First get the token from the running backend
    # The backend sets LOCAL_API_TOKEN in its environment
    # Let's try to access health without token first
    async with aiohttp.ClientSession() as session:
        # Test health (may not require auth)
        try:
            async with session.get('http://127.0.0.1:8000/api/v1/health') as resp:
                print('Health status:', resp.status)
                data = await resp.json()
                print('Health data:', data)
        except Exception as e:
            print('Health error:', e)
        
        # Try to get sources (requires auth)
        # We need to find the token. Let's check if there's a way to get it
        print('\nTrying to access sources without token...')
        try:
            async with session.get('http://127.0.0.1:8000/api/v1/sources') as resp:
                print('Sources status:', resp.status)
                data = await resp.json()
                print('Sources data:', data)
        except Exception as e:
            print('Sources error:', e)

asyncio.run(test_api())