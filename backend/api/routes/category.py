from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID

from backend.core.models import (
    CampaignEvent, UserNotificationPrefs
)
from backend.core.category_tracking import category_tracking_service
from backend.database.repositories import campaign_repository
from backend.core.models import CampaignType

router = APIRouter()


# ===== NFT Endpoints =====

@router.get("/campaigns/{campaign_id}/nft", response_model=dict)
async def get_nft_data(campaign_id: UUID):
    """Get NFT-specific data for a campaign."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    if campaign.type != CampaignType.NFT:
        raise HTTPException(status_code=400, detail={"code": "WRONG_TYPE", "message": "Campaign is not an NFT campaign"})
    
    data = category_tracking_service.get_nft_data(str(campaign_id))
    if not data:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "NFT data not found"})
    return data


@router.patch("/campaigns/{campaign_id}/nft", response_model=dict)
async def update_nft_data(campaign_id: UUID, update: dict):
    """Update NFT-specific data for a campaign."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    if campaign.type != CampaignType.NFT:
        raise HTTPException(status_code=400, detail={"code": "WRONG_TYPE", "message": "Campaign is not an NFT campaign"})
    
    updated = category_tracking_service.update_nft_data(str(campaign_id), update)
    if not updated:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    return category_tracking_service.get_nft_data(str(campaign_id))


# ===== Testnet Endpoints =====

@router.get("/campaigns/{campaign_id}/testnet", response_model=dict)
async def get_testnet_data(campaign_id: UUID):
    """Get Testnet-specific data for a campaign."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    if campaign.type != CampaignType.TESTNET:
        raise HTTPException(status_code=400, detail={"code": "WRONG_TYPE", "message": "Campaign is not a Testnet campaign"})
    
    data = category_tracking_service.get_testnet_data(str(campaign_id))
    if not data:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Testnet data not found"})
    return data


@router.patch("/campaigns/{campaign_id}/testnet", response_model=dict)
async def update_testnet_data(campaign_id: UUID, update: dict):
    """Update Testnet-specific data for a campaign."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    if campaign.type != CampaignType.TESTNET:
        raise HTTPException(status_code=400, detail={"code": "WRONG_TYPE", "message": "Campaign is not a Testnet campaign"})
    
    updated = category_tracking_service.update_testnet_data(str(campaign_id), update)
    if not updated:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    return category_tracking_service.get_testnet_data(str(campaign_id))


# ===== Reward Endpoints =====

@router.get("/campaigns/{campaign_id}/reward", response_model=dict)
async def get_reward_data(campaign_id: UUID):
    """Get Reward-specific data for a campaign."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    if campaign.type != CampaignType.REWARD:
        raise HTTPException(status_code=400, detail={"code": "WRONG_TYPE", "message": "Campaign is not a Reward campaign"})
    
    data = category_tracking_service.get_reward_data(str(campaign_id))
    if not data:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Reward data not found"})
    return data


@router.patch("/campaigns/{campaign_id}/reward", response_model=dict)
async def update_reward_data(campaign_id: UUID, update: dict):
    """Update Reward-specific data for a campaign."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    if campaign.type != CampaignType.REWARD:
        raise HTTPException(status_code=400, detail={"code": "WRONG_TYPE", "message": "Campaign is not a Reward campaign"})
    
    updated = category_tracking_service.update_reward_data(str(campaign_id), update)
    if not updated:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    return category_tracking_service.get_reward_data(str(campaign_id))


# ===== Category Data Endpoints =====

@router.get("/campaigns/{campaign_id}/category-data", response_model=dict)
async def get_category_data(campaign_id: UUID):
    """Get category-specific data based on campaign type."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    data = category_tracking_service.get_category_data(str(campaign_id))
    if not data:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Category data not found"})
    return data


@router.patch("/campaigns/{campaign_id}/category-data", response_model=dict)
async def update_category_data(campaign_id: UUID, update: dict):
    """Update category-specific data based on campaign type."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    updated = category_tracking_service.update_category_data(str(campaign_id), update)
    if not updated:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    return category_tracking_service.get_category_data(str(campaign_id))


# ===== Event/Calendar Endpoints =====

@router.get("/campaigns/{campaign_id}/events", response_model=List[dict])
async def get_campaign_events(campaign_id: UUID):
    """Get all events for a campaign."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    events = category_tracking_service.get_campaign_events(str(campaign_id))
    return [
        {
            "id": str(e.id),
            "campaign_id": str(e.campaign_id),
            "event_type": e.event_type,
            "event_title": e.event_title,
            "event_description": e.event_description,
            "event_date": e.event_date.isoformat(),
            "is_all_day": e.is_all_day,
            "reminder_days_before": e.reminder_days_before,
            "is_notified": e.is_notified,
            "created_at": e.created_at.isoformat(),
            "updated_at": e.updated_at.isoformat(),
        }
        for e in events
    ]


@router.post("/campaigns/{campaign_id}/events", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_event(campaign_id: UUID, event_data: dict):
    """Create a new campaign event."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    required_fields = ["event_type", "event_title", "event_date"]
    for field in required_fields:
        if field not in event_data:
            raise HTTPException(status_code=400, detail={"code": "MISSING_FIELD", "message": f"Missing required field: {field}"})
    
    event = CampaignEvent(
        campaign_id=campaign_id,
        event_type=event_data["event_type"],
        event_title=event_data["event_title"],
        event_description=event_data.get("event_description"),
        event_date=event_data["event_date"],
        is_all_day=event_data.get("is_all_day", False),
        reminder_days_before=event_data.get("reminder_days_before", 1),
    )
    
    created = category_tracking_service.create_event(event)
    if not created:
        raise HTTPException(status_code=500, detail={"code": "CREATE_FAILED", "message": "Failed to create event"})
    
    return {
        "id": str(created.id),
        "campaign_id": str(created.campaign_id),
        "event_type": created.event_type,
        "event_title": created.event_title,
        "event_description": created.event_description,
        "event_date": created.event_date.isoformat(),
        "is_all_day": created.is_all_day,
        "reminder_days_before": created.reminder_days_before,
        "is_notified": created.is_notified,
        "created_at": created.created_at.isoformat(),
        "updated_at": created.updated_at.isoformat(),
    }


@router.get("/campaigns/{campaign_id}/events/{event_id}", response_model=dict)
async def get_event(campaign_id: UUID, event_id: UUID):
    """Get a specific campaign event."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    event = category_tracking_service.get_event(str(event_id))
    if not event or str(event.campaign_id) != str(campaign_id):
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Event not found"})
    
    return {
        "id": str(event.id),
        "campaign_id": str(event.campaign_id),
        "event_type": event.event_type,
        "event_title": event.event_title,
        "event_description": event.event_description,
        "event_date": event.event_date.isoformat(),
        "is_all_day": event.is_all_day,
        "reminder_days_before": event.reminder_days_before,
        "is_notified": event.is_notified,
        "created_at": event.created_at.isoformat(),
        "updated_at": event.updated_at.isoformat(),
    }


@router.patch("/campaigns/{campaign_id}/events/{event_id}", response_model=dict)
async def update_event(campaign_id: UUID, event_id: UUID, update: dict):
    """Update a campaign event."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    event = category_tracking_service.get_event(str(event_id))
    if not event or str(event.campaign_id) != str(campaign_id):
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Event not found"})
    
    updated = category_tracking_service.update_event(str(event_id), update)
    if not updated:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Event not found"})
    
    return {
        "id": str(updated.id),
        "campaign_id": str(updated.campaign_id),
        "event_type": updated.event_type,
        "event_title": updated.event_title,
        "event_description": updated.event_description,
        "event_date": updated.event_date.isoformat(),
        "is_all_day": updated.is_all_day,
        "reminder_days_before": updated.reminder_days_before,
        "is_notified": updated.is_notified,
        "created_at": updated.created_at.isoformat(),
        "updated_at": updated.updated_at.isoformat(),
    }


@router.delete("/campaigns/{campaign_id}/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(campaign_id: UUID, event_id: UUID):
    """Delete a campaign event."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    event = category_tracking_service.get_event(str(event_id))
    if not event or str(event.campaign_id) != str(campaign_id):
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Event not found"})
    
    deleted = category_tracking_service.delete_event(str(event_id))
    if not deleted:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Event not found"})


# ===== Notification Preferences Endpoints =====

@router.get("/campaigns/{campaign_id}/notification-prefs", response_model=dict)
async def get_notification_prefs(campaign_id: UUID):
    """Get user notification preferences for a campaign."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    prefs = category_tracking_service.get_notification_prefs(str(campaign_id))
    if not prefs:
        # Return defaults
        return {
            "campaign_id": str(campaign_id),
            "notify_deadline": True,
            "notify_mint_start": True,
            "notify_mint_end": True,
            "notify_claim_start": True,
            "notify_claim_end": True,
            "notify_distribution": True,
            "reminder_days_before": 1,
            "in_app_enabled": True,
        }
    
    return {
        "id": str(prefs.id),
        "campaign_id": str(prefs.campaign_id),
        "notify_deadline": prefs.notify_deadline,
        "notify_mint_start": prefs.notify_mint_start,
        "notify_mint_end": prefs.notify_mint_end,
        "notify_claim_start": prefs.notify_claim_start,
        "notify_claim_end": prefs.notify_claim_end,
        "notify_distribution": prefs.notify_distribution,
        "reminder_days_before": prefs.reminder_days_before,
        "in_app_enabled": prefs.in_app_enabled,
        "created_at": prefs.created_at.isoformat(),
        "updated_at": prefs.updated_at.isoformat(),
    }


@router.patch("/campaigns/{campaign_id}/notification-prefs", response_model=dict)
async def update_notification_prefs(campaign_id: UUID, update: dict):
    """Update user notification preferences for a campaign."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    prefs = UserNotificationPrefs(
        campaign_id=campaign_id,
        notify_deadline=update.get("notify_deadline", True),
        notify_mint_start=update.get("notify_mint_start", True),
        notify_mint_end=update.get("notify_mint_end", True),
        notify_claim_start=update.get("notify_claim_start", True),
        notify_claim_end=update.get("notify_claim_end", True),
        notify_distribution=update.get("notify_distribution", True),
        reminder_days_before=update.get("reminder_days_before", 1),
        in_app_enabled=update.get("in_app_enabled", True),
    )
    
    updated = category_tracking_service.upsert_notification_prefs(prefs)
    if not updated:
        raise HTTPException(status_code=500, detail={"code": "UPDATE_FAILED", "message": "Failed to update preferences"})
    
    return {
        "id": str(updated.id),
        "campaign_id": str(updated.campaign_id),
        "notify_deadline": updated.notify_deadline,
        "notify_mint_start": updated.notify_mint_start,
        "notify_mint_end": updated.notify_mint_end,
        "notify_claim_start": updated.notify_claim_start,
        "notify_claim_end": updated.notify_claim_end,
        "notify_distribution": updated.notify_distribution,
        "reminder_days_before": updated.reminder_days_before,
        "in_app_enabled": updated.in_app_enabled,
        "created_at": updated.created_at.isoformat(),
        "updated_at": updated.updated_at.isoformat(),
    }