from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from backend.core.discovery import discovery_service
from backend.core.models import ScanRequest, ScanResult

router = APIRouter()


@router.post("/discovery/scans", response_model=ScanResult, status_code=status.HTTP_202_ACCEPTED)
async def start_scan(request: ScanRequest):
    """Start a discovery scan on specified sources."""
    return await discovery_service.run_scan(request)


@router.get("/discovery/scans", response_model=List[dict])
async def get_scan_history(limit: int = 50):
    """Get scan history."""
    return discovery_service.get_scan_history(limit=limit)


@router.get("/discovery/scans/{scan_id}", response_model=dict)
async def get_scan(scan_id: str):
    """Get a specific scan by ID."""
    # For now, just return from history
    history = discovery_service.get_scan_history(limit=100)
    for scan in history:
        if str(scan.get("id")) == scan_id:
            return scan
    raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Scan not found"})