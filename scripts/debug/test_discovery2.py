import asyncio
import sys
import os
sys.path.insert(0, r'E:\Global Airdrop Hunter\backend')

os.environ['DATABASE_PATH'] = r'C:\Users\windows11\AppData\Local\GlobalAirdropHunter\app.db'

async def test_discovery():
    from backend.core.discovery import discovery_service
    from backend.core.models import ScanRequest
    
    print('Starting discovery scan...')
    request = ScanRequest(sources=[])
    result = await discovery_service.run_scan(request)
    
    print('\n=== SCAN RESULT ===')
    print('Scan ID:', result.scan_id)
    print('Sources scanned:', result.sources_scanned)
    print('Campaigns found:', result.campaigns_found)
    print('Campaigns new:', result.campaigns_new)
    print('Campaigns updated:', result.campaigns_updated)
    print('Errors:', result.errors)

asyncio.run(test_discovery())