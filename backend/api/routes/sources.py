from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from backend.database.repositories import source_repository
from backend.core.adapter_registry import adapter_registry
from backend.core.models import (
    Source, SourceCreate, SourceUpdate, SourceStatus, SourceType,
    ScanRequest, ScanResult
)
from backend.core.adapters import SourceMetadata

router = APIRouter()


@router.get("/sources", response_model=List[Source])
async def list_sources(enabled_only: bool = Query(False)):
    return source_repository.list(enabled_only=enabled_only)


@router.post("/sources", response_model=Source, status_code=status.HTTP_201_CREATED)
async def create_source(source: SourceCreate):
    # Check if source with same name exists
    existing = source_repository.get_by_name(source.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DUPLICATE_SOURCE", "message": "Source with this name already exists"}
        )
    return source_repository.create(source)


@router.get("/sources/{source_id}", response_model=Source)
async def get_source(source_id: UUID):
    source = source_repository.get_by_id(str(source_id))
    if not source:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Source not found"})
    return source


@router.patch("/sources/{source_id}", response_model=Source)
async def update_source(source_id: UUID, update: SourceUpdate):
    source = source_repository.update(str(source_id), update)
    if not source:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Source not found"})
    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(source_id: UUID):
    deleted = source_repository.delete(str(source_id))
    if not deleted:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Source not found"})


@router.post("/sources/{source_id}/health", response_model=dict)
async def check_source_health(source_id: UUID):
    source = source_repository.get_by_id(str(source_id))
    if not source:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Source not found"})

    adapter = adapter_registry.create_adapter(source)
    if not adapter:
        raise HTTPException(status_code=400, detail={"code": "NO_ADAPTER", "message": "No adapter available for this source"})

    healthy = await adapter.health_check()
    source_repository.update_health_check(source.id, healthy)

    return {
        "source_id": source.id,
        "healthy": healthy,
        "checked_at": datetime.utcnow().isoformat()
    }


@router.get("/adapters", response_model=List[SourceMetadata])
async def list_adapters():
    return adapter_registry.list_adapter_metadata()