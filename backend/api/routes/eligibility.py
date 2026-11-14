from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID

from backend.database.repositories import campaign_repository, eligibility_repository, user_progress_repository, claim_repository
from backend.core.models import (
    EligibilityRequirement, EligibilityStatus, ProgressStatus,
    UserEligibilityProgress, UserProgressStatus,
    CampaignClaim, ClaimStatus
)
from backend.core.eligibility import eligibility_service

router = APIRouter()


@router.get("/campaigns/{campaign_id}/eligibility", response_model=List[dict])
async def get_campaign_eligibility(campaign_id: UUID):
    """Get all eligibility requirements for a campaign."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    requirements = eligibility_repository.get_by_campaign(str(campaign_id))
    user_progress = user_progress_repository.get_by_campaign(str(campaign_id))
    progress_map = {str(p.requirement_id): p for p in user_progress}
    
    result = []
    for req in requirements:
        req_dict = {
            "id": str(req.id),
            "category": req.category,
            "requirement": req.requirement,
            "status": req.status.value,
            "progress_status": req.progress_status.value,
            "evidence_url": str(req.evidence_url) if req.evidence_url else None,
            "source": req.source,
            "timestamp": req.timestamp.isoformat(),
            "notes": req.notes,
            "user_progress": None,
        }
        if str(req.id) in progress_map:
            prog = progress_map[str(req.id)]
            req_dict["user_progress"] = {
                "user_status": prog.user_status.value,
                "user_notes": prog.user_notes,
                "completed_at": prog.completed_at.isoformat() if prog.completed_at else None,
            }
        result.append(req_dict)
    
    return result


@router.post("/campaigns/{campaign_id}/eligibility", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_eligibility_requirement(campaign_id: UUID, requirement: EligibilityRequirement):
    """Add a new eligibility requirement to a campaign."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    # Ensure campaign_id is set
    requirement_dict = requirement.dict()
    created = eligibility_repository.create_for_campaign(str(campaign_id), requirement)
    return {
        "id": str(created.id),
        "category": created.category,
        "requirement": created.requirement,
        "status": created.status.value,
        "progress_status": created.progress_status.value,
        "evidence_url": str(created.evidence_url) if created.evidence_url else None,
        "source": created.source,
        "timestamp": created.timestamp.isoformat(),
        "notes": created.notes,
    }


@router.get("/campaigns/{campaign_id}/eligibility/{requirement_id}", response_model=dict)
async def get_eligibility_requirement(campaign_id: UUID, requirement_id: UUID):
    """Get a specific eligibility requirement."""
    requirement = eligibility_repository.get_by_id(str(requirement_id))
    if not requirement or str(requirement.campaign_id) != str(campaign_id):
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Requirement not found"})
    
    return {
        "id": str(requirement.id),
        "category": requirement.category,
        "requirement": requirement.requirement,
        "status": requirement.status.value,
        "progress_status": requirement.progress_status.value,
        "evidence_url": str(requirement.evidence_url) if requirement.evidence_url else None,
        "source": requirement.source,
        "timestamp": requirement.timestamp.isoformat(),
        "notes": requirement.notes,
    }


@router.patch("/campaigns/{campaign_id}/eligibility/{requirement_id}", response_model=dict)
async def update_eligibility_requirement(campaign_id: UUID, requirement_id: UUID, update: dict):
    """Update an eligibility requirement."""
    requirement = eligibility_repository.get_by_id(str(requirement_id))
    if not requirement or str(requirement.campaign_id) != str(campaign_id):
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Requirement not found"})
    
    # Convert enum strings to enum values if present
    update_data = update.copy()
    if "status" in update_data:
        update_data["status"] = update_data["status"]
    if "progress_status" in update_data:
        update_data["progress_status"] = update_data["progress_status"]
    
    updated = eligibility_repository.update(str(requirement_id), update_data)
    if not updated:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Requirement not found"})
    
    return {
        "id": str(updated.id),
        "category": updated.category,
        "requirement": updated.requirement,
        "status": updated.status.value,
        "progress_status": updated.progress_status.value,
        "evidence_url": str(updated.evidence_url) if updated.evidence_url else None,
        "source": updated.source,
        "timestamp": updated.timestamp.isoformat(),
        "notes": updated.notes,
    }


@router.delete("/campaigns/{campaign_id}/eligibility/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_eligibility_requirement(campaign_id: UUID, requirement_id: UUID):
    """Delete an eligibility requirement."""
    requirement = eligibility_repository.get_by_id(str(requirement_id))
    if not requirement or str(requirement.campaign_id) != str(campaign_id):
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Requirement not found"})
    
    deleted = eligibility_repository.delete(str(requirement_id))
    if not deleted:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Requirement not found"})


@router.post("/campaigns/{campaign_id}/eligibility/extract", response_model=List[dict])
async def extract_eligibility_requirements(campaign_id: UUID):
    """Auto-extract eligibility requirements from campaign text."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    requirements = eligibility_service.extract_requirements(campaign)
    saved = eligibility_service.save_requirements(str(campaign_id), requirements)
    
    return [
        {
            "id": str(req.id),
            "category": req.category,
            "requirement": req.requirement,
            "status": req.status.value,
            "progress_status": req.progress_status.value,
            "evidence_url": str(req.evidence_url) if req.evidence_url else None,
            "source": req.source,
            "timestamp": req.timestamp.isoformat(),
            "notes": req.notes,
        }
        for req in saved
    ]


# User Progress endpoints
@router.get("/campaigns/{campaign_id}/progress", response_model=List[dict])
async def get_user_progress(campaign_id: UUID):
    """Get user progress for all requirements in a campaign."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    progress = user_progress_repository.get_by_campaign(str(campaign_id))
    return [
        {
            "id": str(p.id),
            "campaign_id": str(p.campaign_id),
            "requirement_id": str(p.requirement_id),
            "user_status": p.user_status.value,
            "user_notes": p.user_notes,
            "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
        }
        for p in progress
    ]


@router.post("/campaigns/{campaign_id}/progress", response_model=dict)
async def update_user_progress(campaign_id: UUID, update: dict):
    """Update user's self-reported progress on a requirement."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    requirement_id = update.get("requirement_id")
    user_status = update.get("user_status")
    user_notes = update.get("user_notes")
    completed = update.get("completed", False)
    
    if not requirement_id or not user_status:
        raise HTTPException(status_code=400, detail={"code": "MISSING_FIELDS", "message": "requirement_id and user_status required"})
    
    try:
        progress = user_progress_repository.upsert(UserEligibilityProgress(
            campaign_id=campaign_id,
            requirement_id=requirement_id,
            user_status=user_status,
            user_notes=user_notes,
            completed_at=datetime.utcnow() if completed else None,
        ))
    except ValueError:
        raise HTTPException(status_code=400, detail={"code": "INVALID_STATUS", "message": f"Invalid user_status: {user_status}"})
    
    return {
        "id": str(progress.id),
        "campaign_id": str(progress.campaign_id),
        "requirement_id": str(progress.requirement_id),
        "user_status": progress.user_status.value,
        "user_notes": progress.user_notes,
        "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
        "created_at": progress.created_at.isoformat(),
        "updated_at": progress.updated_at.isoformat(),
    }


# Claims endpoints
@router.get("/campaigns/{campaign_id}/claims", response_model=List[dict])
async def get_campaign_claims(campaign_id: UUID):
    """Get all claims for a campaign."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    claims = claim_repository.get_by_campaign(str(campaign_id))
    return [
        {
            "id": str(c.id),
            "campaign_id": str(c.campaign_id),
            "claim_type": c.claim_type,
            "claim_url": str(c.claim_url) if c.claim_url else None,
            "transaction_hash": c.transaction_hash,
            "block_number": c.block_number,
            "network": c.network,
            "status": c.status.value,
            "claimed_at": c.claimed_at.isoformat() if c.claimed_at else None,
            "confirmed_at": c.confirmed_at.isoformat() if c.confirmed_at else None,
            "user_notes": c.user_notes,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in claims
    ]


@router.post("/campaigns/{campaign_id}/claims", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_claim(campaign_id: UUID, claim_data: dict):
    """Record a claim attempt."""
    campaign = campaign_repository.get_by_id(str(campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Campaign not found"})
    
    required_fields = ["claim_type"]
    for field in required_fields:
        if field not in claim_data:
            raise HTTPException(status_code=400, detail={"code": "MISSING_FIELD", "message": f"Missing required field: {field}"})
    
    claim = claim_repository.create(CampaignClaim(
        campaign_id=campaign_id,
        claim_type=claim_data["claim_type"],
        claim_url=claim_data.get("claim_url"),
        transaction_hash=claim_data.get("transaction_hash"),
        block_number=claim_data.get("block_number"),
        network=claim_data.get("network"),
        user_notes=claim_data.get("user_notes"),
    ))
    
    return {
        "id": str(claim.id),
        "campaign_id": str(claim.campaign_id),
        "claim_type": claim.claim_type,
        "claim_url": str(claim.claim_url) if claim.claim_url else None,
        "transaction_hash": claim.transaction_hash,
        "block_number": claim.block_number,
        "network": claim.network,
        "status": claim.status.value,
        "claimed_at": claim.claimed_at.isoformat() if claim.claimed_at else None,
        "confirmed_at": claim.confirmed_at.isoformat() if claim.confirmed_at else None,
        "user_notes": claim.user_notes,
        "created_at": claim.created_at.isoformat(),
        "updated_at": claim.updated_at.isoformat(),
    }


@router.patch("/campaigns/{campaign_id}/claims/{claim_id}", response_model=dict)
async def update_claim(campaign_id: UUID, claim_id: UUID, update: dict):
    """Update a claim status."""
    claim = claim_repository.get_by_id(str(claim_id))
    if not claim or str(claim.campaign_id) != str(campaign_id):
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Claim not found"})
    
    update_data = update.copy()
    if "status" in update_data:
        update_data["status"] = update_data["status"]
    
    updated = claim_repository.update(str(claim_id), update_data)
    if not updated:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Claim not found"})
    
    return {
        "id": str(updated.id),
        "campaign_id": str(updated.campaign_id),
        "claim_type": updated.claim_type,
        "claim_url": str(updated.claim_url) if updated.claim_url else None,
        "transaction_hash": updated.transaction_hash,
        "block_number": updated.block_number,
        "network": updated.network,
        "status": updated.status.value,
        "claimed_at": updated.claimed_at.isoformat() if updated.claimed_at else None,
        "confirmed_at": updated.confirmed_at.isoformat() if updated.confirmed_at else None,
        "user_notes": updated.user_notes,
        "created_at": updated.created_at.isoformat(),
        "updated_at": updated.updated_at.isoformat(),
    }


from datetime import datetime