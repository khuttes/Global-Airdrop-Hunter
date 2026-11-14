import sqlite3
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from backend.database.connection import get_db
from backend.core.models import (
    EligibilityRequirement, EligibilityStatus, ProgressStatus,
    UserEligibilityProgress, UserProgressStatus,
    CampaignClaim, ClaimStatus
)


class EligibilityRepository:
    def __init__(self):
        pass

    def _row_to_eligibility(self, row: sqlite3.Row) -> EligibilityRequirement:
        return EligibilityRequirement(
            id=uuid.UUID(row["id"]),
            campaign_id=uuid.UUID(row["campaign_id"]),
            category=row["category"],
            requirement=row["requirement"],
            status=EligibilityStatus(row["status"]),
            evidence_url=row["evidence_url"],
            source=row["source"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            notes=row["notes"],
            progress_status=ProgressStatus(row["progress_status"]),
            user_notes=row["user_notes"],
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
        )

    def create(self, requirement: EligibilityRequirement) -> EligibilityRequirement:
        with get_db() as db:
            req_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            db.execute("""
                INSERT INTO campaign_eligibility (
                    id, campaign_id, category, requirement, status,
                    evidence_url, source, timestamp, notes,
                    progress_status, user_notes, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                req_id,
                str(requirement.campaign_id) if hasattr(requirement, 'campaign_id') and requirement.campaign_id else None,
                requirement.category,
                requirement.requirement,
                requirement.status.value,
                str(requirement.evidence_url) if requirement.evidence_url else None,
                requirement.source,
                requirement.timestamp.isoformat() if requirement.timestamp else now,
                requirement.notes,
                requirement.progress_status.value,
                requirement.user_notes,
                requirement.completed_at.isoformat() if requirement.completed_at else None,
            ))
            return self.get_by_id(req_id)

    def create_for_campaign(self, campaign_id: str, requirement: EligibilityRequirement) -> EligibilityRequirement:
        with get_db() as db:
            req_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            db.execute("""
                INSERT INTO campaign_eligibility (
                    id, campaign_id, category, requirement, status,
                    evidence_url, source, timestamp, notes,
                    progress_status, user_notes, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                req_id,
                campaign_id,
                requirement.category,
                requirement.requirement,
                requirement.status.value,
                str(requirement.evidence_url) if requirement.evidence_url else None,
                requirement.source,
                requirement.timestamp.isoformat() if requirement.timestamp else now,
                requirement.notes,
                requirement.progress_status.value,
                requirement.user_notes,
                requirement.completed_at.isoformat() if requirement.completed_at else None,
            ))
            return self.get_by_id(req_id)

    def get_by_id(self, requirement_id: str) -> Optional[EligibilityRequirement]:
        with get_db() as db:
            row = db.execute("SELECT * FROM campaign_eligibility WHERE id = ?", (requirement_id,)).fetchone()
            if not row:
                return None
            return self._row_to_eligibility(row)

    def get_by_campaign(self, campaign_id: str) -> List[EligibilityRequirement]:
        with get_db() as db:
            rows = db.execute("SELECT * FROM campaign_eligibility WHERE campaign_id = ? ORDER BY timestamp", (campaign_id,)).fetchall()
            return [self._row_to_eligibility(row) for row in rows]

    def update(self, requirement_id: str, update_data: Dict[str, Any]) -> Optional[EligibilityRequirement]:
        with get_db() as db:
            existing = db.execute("SELECT * FROM campaign_eligibility WHERE id = ?", (requirement_id,)).fetchone()
            if not existing:
                return None

            updates = []
            params = []

            field_mapping = {
                "category": "category",
                "requirement": "requirement",
                "status": "status",
                "evidence_url": "evidence_url",
                "source": "source",
                "notes": "notes",
                "progress_status": "progress_status",
                "user_notes": "user_notes",
                "completed_at": "completed_at",
            }

            for field, db_field in field_mapping.items():
                if field in update_data and update_data[field] is not None:
                    value = update_data[field]
                    if hasattr(value, 'value'):
                        value = value.value
                    elif isinstance(value, datetime):
                        value = value.isoformat()
                    elif hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool)):
                        value = str(value)
                    updates.append(f"{db_field} = ?")
                    params.append(value)

            if updates:
                params.append(requirement_id)
                db.execute(f"UPDATE campaign_eligibility SET {', '.join(updates)} WHERE id = ?", params)

            return self.get_by_id(requirement_id)

    def delete(self, requirement_id: str) -> bool:
        with get_db() as db:
            cursor = db.execute("DELETE FROM campaign_eligibility WHERE id = ?", (requirement_id,))
            return cursor.rowcount > 0

    def bulk_create_for_campaign(self, campaign_id: str, requirements: List[EligibilityRequirement]) -> List[EligibilityRequirement]:
        created = []
        for req in requirements:
            created.append(self.create_for_campaign(campaign_id, req))
        return created


class UserProgressRepository:
    def __init__(self):
        pass

    def create(self, progress: UserEligibilityProgress) -> UserEligibilityProgress:
        with get_db() as db:
            progress_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            db.execute("""
                INSERT INTO user_eligibility_progress (
                    id, campaign_id, requirement_id, user_status, user_notes, completed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                progress_id,
                str(progress.campaign_id),
                str(progress.requirement_id),
                progress.user_status.value,
                progress.user_notes,
                progress.completed_at.isoformat() if progress.completed_at else None,
                now, now
            ))
            return self.get_by_id(progress_id)

    def get_by_id(self, progress_id: str) -> Optional[UserEligibilityProgress]:
        with get_db() as db:
            row = db.execute("SELECT * FROM user_eligibility_progress WHERE id = ?", (progress_id,)).fetchone()
            if not row:
                return None
            return UserEligibilityProgress(
                id=uuid.UUID(row["id"]),
                campaign_id=uuid.UUID(row["campaign_id"]),
                requirement_id=uuid.UUID(row["requirement_id"]),
                user_status=UserProgressStatus(row["user_status"]),
                user_notes=row["user_notes"],
                completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    def get_by_campaign(self, campaign_id: str) -> List[UserEligibilityProgress]:
        with get_db() as db:
            rows = db.execute("SELECT * FROM user_eligibility_progress WHERE campaign_id = ?", (campaign_id,)).fetchall()
            return [
                UserEligibilityProgress(
                    id=uuid.UUID(row["id"]),
                    campaign_id=uuid.UUID(row["campaign_id"]),
                    requirement_id=uuid.UUID(row["requirement_id"]),
                    user_status=UserProgressStatus(row["user_status"]),
                    user_notes=row["user_notes"],
                    completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
                for row in rows
            ]

    def get_by_campaign_and_requirement(self, campaign_id: str, requirement_id: str) -> Optional[UserEligibilityProgress]:
        with get_db() as db:
            row = db.execute(
                "SELECT * FROM user_eligibility_progress WHERE campaign_id = ? AND requirement_id = ?",
                (campaign_id, requirement_id)
            ).fetchone()
            if not row:
                return None
            return UserEligibilityProgress(
                id=uuid.UUID(row["id"]),
                campaign_id=uuid.UUID(row["campaign_id"]),
                requirement_id=uuid.UUID(row["requirement_id"]),
                user_status=UserProgressStatus(row["user_status"]),
                user_notes=row["user_notes"],
                completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    def update(self, campaign_id: str, requirement_id: str, update_data: Dict[str, Any]) -> Optional[UserEligibilityProgress]:
        with get_db() as db:
            existing = db.execute(
                "SELECT * FROM user_eligibility_progress WHERE campaign_id = ? AND requirement_id = ?",
                (campaign_id, requirement_id)
            ).fetchone()
            if not existing:
                return None

            updates = []
            params = []

            field_mapping = {
                "user_status": "user_status",
                "user_notes": "user_notes",
                "completed_at": "completed_at",
            }

            for field, db_field in field_mapping.items():
                if field in update_data and update_data[field] is not None:
                    value = update_data[field]
                    if hasattr(value, 'value'):
                        value = value.value
                    elif isinstance(value, datetime):
                        value = value.isoformat()
                    updates.append(f"{db_field} = ?")
                    params.append(value)

            if updates:
                updates.append("updated_at = ?")
                params.append(datetime.utcnow().isoformat())
                params.extend([campaign_id, requirement_id])
                db.execute(f"UPDATE user_eligibility_progress SET {', '.join(updates)} WHERE campaign_id = ? AND requirement_id = ?", params)

            return self.get_by_campaign_and_requirement(campaign_id, requirement_id)

    def upsert(self, progress: UserEligibilityProgress) -> UserEligibilityProgress:
        existing = self.get_by_campaign_and_requirement(str(progress.campaign_id), str(progress.requirement_id))
        if existing:
            return self.update(str(progress.campaign_id), str(progress.requirement_id), {
                "user_status": progress.user_status,
                "user_notes": progress.user_notes,
                "completed_at": progress.completed_at,
            })
        return self.create(progress)


class ClaimRepository:
    def __init__(self):
        pass

    def create(self, claim: CampaignClaim) -> CampaignClaim:
        with get_db() as db:
            claim_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            db.execute("""
                INSERT INTO campaign_claims (
                    id, campaign_id, claim_type, claim_url, transaction_hash,
                    block_number, network, status, claimed_at, confirmed_at,
                    user_notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                claim_id,
                str(claim.campaign_id),
                claim.claim_type,
                str(claim.claim_url) if claim.claim_url else None,
                claim.transaction_hash,
                claim.block_number,
                claim.network,
                claim.status.value,
                claim.claimed_at.isoformat() if claim.claimed_at else None,
                claim.confirmed_at.isoformat() if claim.confirmed_at else None,
                claim.user_notes,
                now, now
            ))
            return self.get_by_id(claim_id)

    def get_by_id(self, claim_id: str) -> Optional[CampaignClaim]:
        with get_db() as db:
            row = db.execute("SELECT * FROM campaign_claims WHERE id = ?", (claim_id,)).fetchone()
            if not row:
                return None
            return CampaignClaim(
                id=uuid.UUID(row["id"]),
                campaign_id=uuid.UUID(row["campaign_id"]),
                claim_type=row["claim_type"],
                claim_url=row["claim_url"],
                transaction_hash=row["transaction_hash"],
                block_number=row["block_number"],
                network=row["network"],
                status=ClaimStatus(row["status"]),
                claimed_at=datetime.fromisoformat(row["claimed_at"]) if row["claimed_at"] else None,
                confirmed_at=datetime.fromisoformat(row["confirmed_at"]) if row["confirmed_at"] else None,
                user_notes=row["user_notes"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    def get_by_campaign(self, campaign_id: str) -> List[CampaignClaim]:
        with get_db() as db:
            rows = db.execute("SELECT * FROM campaign_claims WHERE campaign_id = ? ORDER BY created_at DESC", (campaign_id,)).fetchall()
            return [
                CampaignClaim(
                    id=uuid.UUID(row["id"]),
                    campaign_id=uuid.UUID(row["campaign_id"]),
                    claim_type=row["claim_type"],
                    claim_url=row["claim_url"],
                    transaction_hash=row["transaction_hash"],
                    block_number=row["block_number"],
                    network=row["network"],
                    status=ClaimStatus(row["status"]),
                    claimed_at=datetime.fromisoformat(row["claimed_at"]) if row["claimed_at"] else None,
                    confirmed_at=datetime.fromisoformat(row["confirmed_at"]) if row["confirmed_at"] else None,
                    user_notes=row["user_notes"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
                for row in rows
            ]

    def update(self, claim_id: str, update_data: Dict[str, Any]) -> Optional[CampaignClaim]:
        with get_db() as db:
            existing = db.execute("SELECT * FROM campaign_claims WHERE id = ?", (claim_id,)).fetchone()
            if not existing:
                return None

            updates = []
            params = []

            field_mapping = {
                "claim_type": "claim_type",
                "claim_url": "claim_url",
                "transaction_hash": "transaction_hash",
                "block_number": "block_number",
                "network": "network",
                "status": "status",
                "claimed_at": "claimed_at",
                "confirmed_at": "confirmed_at",
                "user_notes": "user_notes",
            }

            for field, db_field in field_mapping.items():
                if field in update_data and update_data[field] is not None:
                    value = update_data[field]
                    if hasattr(value, 'value'):
                        value = value.value
                    elif isinstance(value, datetime):
                        value = value.isoformat()
                    updates.append(f"{db_field} = ?")
                    params.append(value)

            if updates:
                updates.append("updated_at = ?")
                params.append(datetime.utcnow().isoformat())
                params.append(claim_id)
                db.execute(f"UPDATE campaign_claims SET {', '.join(updates)} WHERE id = ?", params)

            return self.get_by_id(claim_id)


eligibility_repository = EligibilityRepository()
user_progress_repository = UserProgressRepository()
claim_repository = ClaimRepository()