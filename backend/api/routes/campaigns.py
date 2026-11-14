from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional
from uuid import UUID

from backend.database.repositories import campaign_repository
from backend.core.models import (
    Campaign, CampaignCreate, CampaignUpdate, CampaignListItem,
    CampaignsResponse, CampaignFilters, PaginationParams,
    CampaignType, CampaignStatus, VerificationStatus, RiskLevel
)

router = APIRouter()


@router.get("/campaigns", response_model=CampaignsResponse)
async def list_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[CampaignType] = None,
    network: Optional[str] = None,
    status: Optional[CampaignStatus] = None,
    verification_status: Optional[VerificationStatus] = None,
    risk_level: Optional[RiskLevel] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "discovered_at",
    sort_order: Optional[str] = "desc",
):
    filters = CampaignFilters(
        type=type,
        network=network,
        status=status,
        verification_status=verification_status,
        risk_level=risk_level,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    pagination = PaginationParams(page=page, page_size=page_size)
    return campaign_repository.list(filters, pagination)


@router.post("/campaigns", response_model=Campaign, status_code=status.HTTP_201_CREATED)
async def create_campaign(campaign: CampaignCreate):
    return campaign_repository.create(campaign)


@router.get("/campaigns/{campaign_id}", response_model=Campaign)
async def get_campaign(campaign_id: UUID):
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    return campaign


@router.patch("/campaigns/{campaign_id}", response_model=Campaign)
async def update_campaign(campaign_id: UUID, update: CampaignUpdate):
    campaign = campaign_repository.update(str(campaign_id), update)
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    return campaign


@router.delete("/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(campaign_id: UUID):
    deleted = campaign_repository.delete(str(campaign_id))
    if not deleted:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})


@router.post("/campaigns/{campaign_id}/save", response_model=Campaign)
async def save_campaign(campaign_id: UUID):
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    # In a real implementation, this would add to user_tracked table
    return campaign