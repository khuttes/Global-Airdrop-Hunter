import asyncio
import sys
sys.path.insert(0, r'E:\Global Airdrop Hunter\backend')

async def test_discovery():
    # Import source repository directly (avoids circular import via __init__.py)
    from backend.database.repositories.source import source_repository
    from backend.core.adapter_registry import adapter_registry
    from backend.core.discovery import discovery_service
    from backend.core.models import ScanRequest
    
    sources = source_repository.get_enabled_sources()
    print('Enabled sources in DB:', len(sources))
    for s in sources:
        print('  - {} ({})'.format(s.id, s.name))
    
    print('\nStarting discovery scan...')
    request = ScanRequest(sources=None)
    result = await discovery_service.run_scan(request)
    
    print('\n=== SCAN RESULT ===')
    print('Scan ID:', result.scan_id)
    print('Sources scanned:', result.sources_scanned)
    print('Campaigns found:', result.campaigns_found)
    print('Campaigns new:', result.campaigns_new)
    print('Campaigns updated:', result.campaigns_updated)
    print('Errors:', result.errors)

asyncio.run(test_discovery())