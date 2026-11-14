"""
Eligibility service for Global Airdrop Hunter.
Extracts and manages eligibility requirements from campaigns.
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse

from backend.database.repositories import eligibility_repository, user_progress_repository, claim_repository
from backend.core.models import (
    EligibilityRequirement, EligibilityStatus, ProgressStatus,
    UserEligibilityProgress, UserProgressStatus,
    CampaignClaim, ClaimStatus
)


class EligibilityService:
    """Service for extracting and managing eligibility requirements."""

    # Common requirement patterns for extraction
    REQUIREMENT_PATTERNS = {
        "region": [
            r"(?:available|eligible|open)\s+(?:to|for)\s+(?:users|residents)\s+(?:in|from)\s+([^,\.]+)",
            r"(?:not\s+)?available\s+(?:to|for)\s+(?:users|residents)\s+(?:in|from)\s+([^,\.]+)",
            r"region\s*(?:lock|restriction|limit)\s*[:=]\s*([^,\.]+)",
            r"geo\s*(?:block|restriction)\s*[:=]\s*([^,\.]+)",
        ],
        "network": [
            r"(?:on|using|via)\s+(ethereum|polygon|arbitrum|optimism|bsc|base|linea|zksync|scroll|avalanche|fantom|solana|cosmos|aptos|sui|sei|monad)",
            r"network\s*[:=]\s*(ethereum|polygon|arbitrum|optimism|bsc|base|linea|zksync|scroll|avalanche|fantom|solana|cosmos|aptos|sui|sei|monad)",
            r"chain\s*[:=]\s*(ethereum|polygon|arbitrum|optimism|bsc|base|linea|zksync|scroll|avalanche|fantom|solana|cosmos|aptos|sui|sei|monad)",
        ],
        "activity": [
            r"(?:minimum|at\s+least)\s+(\d+)\s*(?:transactions?|txs?|transfers?)",
            r"(?:completed|made|performed)\s+(?:at\s+least\s+)?(\d+)\s*(?:transactions?|txs?|actions?)",
            r"(?:bridged|deposited|staked|swapped)\s+(?:at\s+least\s+)?(\d+(?:\.\d+)?)\s*(\w+)",
            r"volume\s*(?:>|>=|of\s+at\s+least)\s*(\d+(?:\.\d+)?)\s*(\w+)",
        ],
        "snapshot": [
            r"snapshot\s*(?:date|taken|at)\s*[:=]\s*([^,\.]+)",
            r"snapshot\s+(?:taken|on)\s+([^,\.]+)",
            r"eligible\s+(?:as\s+of|at)\s+([^,\.]+)",
        ],
        "tasks": [
            r"(?:complete|finish|do)\s+(?:the\s+)?(?:following\s+)?tasks?\s*[:=]\s*([^,\.]+)",
            r"tasks?\s*[:=]\s*([^,\.]+)",
            r"(?:complete|join|follow)\s+(?:on\s+)?(?:twitter|discord|telegram|github|medium|youtube)",
            r"(?:retweet|like|share|comment)\s+(?:on\s+)?(?:twitter|x)",
        ],
        "deadline": [
            r"deadline\s*[:=]\s*([^,\.]+)",
            r"ends?\s+(?:on|at)\s+([^,\.]+)",
            r"until\s+([^,\.]+)",
            r"claim\s+(?:by|before)\s+([^,\.]+)",
        ],
        "holding": [
            r"hold(?:ing)?\s+(?:at\s+least\s+)?(\d+(?:\.\d+)?)\s*(\w+)",
            r"minimum\s+(?:balance|holding)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(\w+)",
            r"(?:must|need\s+to)\s+hold\s+(\d+(?:\.\d+)?)\s*(\w+)",
        ],
        "nft": [
            r"own\s+(?:at\s+least\s+)?(\d+)\s+(?:nfts?|tokens?)",
            r"(?:holder|owner)\s+of\s+([^,\.]+)\s+(?:collection|nft)",
            r"(?:mint|minted)\s+(\d+)\s+(?:nfts?|tokens?)",
        ],
    }

    def __init__(self):
        pass

    def extract_requirements(self, campaign) -> List[Dict[str, Any]]:
        """
        Extract eligibility requirements from campaign text content.
        Returns list of requirement dicts ready for database insertion.
        """
        requirements = []
        text = self._get_campaign_text(campaign)

        for category, patterns in self.REQUIREMENT_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    requirement_text = match.group(0).strip()
                    extracted_value = match.group(1) if match.groups() else None

                    requirement = {
                        "category": category,
                        "requirement": requirement_text,
                        "extracted_value": extracted_value,
                        "status": "unknown",
                        "evidence_url": None,
                        "source": "auto_extracted",
                        "notes": f"Auto-extracted from campaign text using pattern: {pattern}",
                    }
                    requirements.append(requirement)

        # Deduplicate similar requirements
        requirements = self._deduplicate_requirements(requirements)
        return requirements

    def _get_campaign_text(self, campaign) -> str:
        """Combine all campaign text fields for extraction."""
        parts = []
        if campaign.description:
            parts.append(campaign.description)
        if campaign.name:
            parts.append(campaign.name)
        if campaign.project:
            parts.append(campaign.project)
        for evidence in campaign.evidence:
            if evidence.snippet:
                parts.append(evidence.snippet)
            if evidence.title:
                parts.append(evidence.title)
        return " ".join(parts)

    def _deduplicate_requirements(self, requirements: List[Dict]) -> List[Dict]:
        """Remove duplicate requirements based on category and requirement text."""
        seen = set()
        unique = []
        for req in requirements:
            key = (req["category"].lower(), req["requirement"].lower())
            if key not in seen:
                seen.add(key)
                unique.append(req)
        return unique

    def save_requirements(self, campaign_id: str, requirements: List[Dict]) -> List:
        """Save extracted requirements to database."""
        saved = []
        for req_data in requirements:
            from backend.core.models import EligibilityRequirement, EligibilityStatus, ProgressStatus
            req = EligibilityRequirement(
                category=req_data["category"],
                requirement=req_data["requirement"],
                status=EligibilityStatus(req_data.get("status", "unknown")),
                evidence_url=req_data.get("evidence_url"),
                source=req_data.get("source", "auto_extracted"),
                notes=req_data.get("notes"),
            )
            saved.append(eligibility_repository.create_for_campaign(campaign_id, req))
        return saved

    def get_campaign_eligibility(self, campaign_id: str) -> List:
        """Get all eligibility requirements for a campaign."""
        return eligibility_repository.get_by_campaign(campaign_id)

    def update_requirement(self, requirement_id: str, update_data: Dict) -> Optional[Any]:
        """Update an eligibility requirement."""
        return eligibility_repository.update(requirement_id, update_data)

    def set_progress_status(self, requirement_id: str, progress_status: str) -> Optional[Any]:
        """Update the progress status of a requirement."""
        from backend.core.models import ProgressStatus
        return eligibility_repository.update(requirement_id, {"progress_status": ProgressStatus(progress_status)})

    def get_user_progress(self, campaign_id: str) -> List:
        """Get user progress for a campaign."""
        return user_progress_repository.get_by_campaign(campaign_id)

    def update_user_progress(self, campaign_id: str, requirement_id: str, user_status: str, user_notes: str = None, completed: bool = False) -> Optional[Any]:
        """Update user's self-reported progress on a requirement."""
        from backend.core.models import UserProgressStatus, UserEligibilityProgress
        from datetime import datetime
        import uuid

        existing = user_progress_repository.get_by_campaign_and_requirement(campaign_id, requirement_id)
        update_data = {
            "user_status": UserProgressStatus(user_status),
            "user_notes": None,
            "completed_at": datetime.utcnow() if completed else None,
        }
        return user_progress_repository.upsert(UserEligibilityProgress(
            id=uuid.uuid4(),
            campaign_id=uuid.UUID(campaign_id),
            requirement_id=uuid.UUID(requirement_id),
            user_status=UserProgressStatus(user_status),
            user_notes=None,
            completed_at=datetime.utcnow() if completed else None,
        ))

    def add_claim(self, campaign_id: str, claim_type: str, claim_url: str = None, transaction_hash: str = None, network: str = None, user_notes: str = None) -> Any:
        """Record a claim attempt for a campaign."""
        from backend.core.models import CampaignClaim, ClaimStatus
        import uuid

        claim = CampaignClaim(
            id=uuid.uuid4(),
            campaign_id=uuid.UUID(campaign_id),
            claim_type=claim_type,
            claim_url=claim_url,
            transaction_hash=transaction_hash,
            network=network,
            status=ClaimStatus.PENDING,
            claimed_at=datetime.utcnow(),
            user_notes=user_notes,
        )
        return claim_repository.create(claim)

    def update_claim_status(self, claim_id: str, status: str, transaction_hash: str = None, block_number: int = None) -> Optional[Any]:
        """Update claim status."""
        from backend.core.models import ClaimStatus
        from datetime import datetime

        update_data = {"status": ClaimStatus(status)}
        if status == "confirmed":
            update_data["confirmed_at"] = datetime.utcnow()
        if transaction_hash:
            update_data["transaction_hash"] = transaction_hash
        if block_number:
            update_data["block_number"] = block_number
        return claim_repository.update(claim_id, update_data)

    def get_claims(self, campaign_id: str) -> List:
        """Get all claims for a campaign."""
        return claim_repository.get_by_campaign(campaign_id)

    def get_campaign_with_eligibility(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign with eligibility requirements and user progress."""
        from backend.database.repositories import campaign_repository
        from backend.database.repositories import user_progress_repository as upr

        campaign = campaign_repository.get_by_id(campaign_id)
        if not campaign:
            return None

        requirements = self.get_campaign_eligibility(campaign_id)
        user_progress = upr.get_by_campaign(campaign_id)
        claims = self.get_claims(campaign_id)

        # Combine requirements with user progress
        progress_map = {str(p.requirement_id): p for p in user_progress}

        requirements_with_progress = []
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
            requirements_with_progress.append(req_dict)

        return {
            "campaign": {
                "id": str(campaign.id),
                "name": campaign.name,
                "project": campaign.project,
                "type": campaign.type.value,
                "network": campaign.network,
                "status": campaign.status.value,
            },
            "requirements": requirements_with_progress,
            "claims": [
                {
                    "id": str(c.id),
                    "claim_type": c.claim_type,
                    "claim_url": str(c.claim_url) if c.claim_url else None,
                    "transaction_hash": c.transaction_hash,
                    "block_number": c.block_number,
                    "network": c.network,
                    "status": c.status.value,
                    "claimed_at": c.claimed_at.isoformat() if c.claimed_at else None,
                    "confirmed_at": c.confirmed_at.isoformat() if c.confirmed_at else None,
                    "user_notes": c.user_notes,
                }
                for c in claims
            ],
        }


eligibility_service = EligibilityService()