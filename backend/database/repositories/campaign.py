import sqlite3
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Generator, Tuple
from contextlib import contextmanager

from backend.database.connection import get_db
from backend.core.models import (
    Campaign, CampaignCreate, CampaignUpdate, CampaignListItem,
    CampaignsResponse, CampaignFilters, PaginationParams,
    CampaignType, CampaignStatus, VerificationStatus, RiskLevel,
    Evidence, RiskFinding, EligibilityRequirement
)
from backend.core.deduplication import (
    normalize_url, generate_stable_id, find_potential_duplicates
)


class CampaignRepository:
    def __init__(self):
        pass

    def _row_to_campaign(self, row: sqlite3.Row) -> Campaign:
        return Campaign(
            id=uuid.UUID(row["id"]),
            stable_id=row["stable_id"],
            name=row["name"],
            project=row["project"],
            type=CampaignType(row["type"]),
            network=row["network"],
            description=row["description"],
            official_url=row["official_url"],
            campaign_url=row["campaign_url"],
            status=CampaignStatus(row["status"]),
            verification_status=VerificationStatus(row["verification_status"]),
            risk_level=RiskLevel(row["risk_level"]),
            risk_score=row["risk_score"],
            deadline=datetime.fromisoformat(row["deadline"]) if row["deadline"] else None,
            snapshot_date=datetime.fromisoformat(row["snapshot_date"]) if row["snapshot_date"] else None,
            discovered_at=datetime.fromisoformat(row["discovered_at"]),
            last_seen_at=datetime.fromisoformat(row["last_seen_at"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_list_item(self, row: sqlite3.Row) -> CampaignListItem:
        return CampaignListItem(
            id=uuid.UUID(row["id"]),
            stable_id=row["stable_id"],
            name=row["name"],
            project=row["project"],
            type=CampaignType(row["type"]),
            network=row["network"],
            status=CampaignStatus(row["status"]),
            verification_status=VerificationStatus(row["verification_status"]),
            risk_level=RiskLevel(row["risk_level"]),
            deadline=datetime.fromisoformat(row["deadline"]) if row["deadline"] else None,
            discovered_at=datetime.fromisoformat(row["discovered_at"]),
        )

    def create(self, campaign: CampaignCreate, source_id: Optional[str] = None) -> Campaign:
        with get_db() as db:
            now = datetime.utcnow().isoformat()
            campaign_id = str(uuid.uuid4())
            stable_id = self._generate_stable_id(campaign)

            db.execute("""
                INSERT INTO campaigns (
                    id, stable_id, name, project, type, network, description,
                    official_url, campaign_url, status, verification_status,
                    risk_level, risk_score, deadline, snapshot_date,
                    discovered_at, last_seen_at, created_at, updated_at, source_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                campaign_id, stable_id, campaign.name, campaign.project,
                campaign.type.value, campaign.network, campaign.description,
                str(campaign.official_url) if campaign.official_url else None,
                str(campaign.campaign_url) if campaign.campaign_url else None,
                campaign.status.value, campaign.verification_status.value,
                campaign.risk_level.value, campaign.risk_score,
                campaign.deadline.isoformat() if campaign.deadline else None,
                campaign.snapshot_date.isoformat() if campaign.snapshot_date else None,
                now, now, now, now, source_id
            ))

            for evidence_url in campaign.evidence_urls:
                evidence_id = str(uuid.uuid4())
                db.execute("""
                    INSERT INTO campaign_evidence (id, campaign_id, url, source_type, content_hash, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (evidence_id, campaign_id, str(evidence_url), "manual", "", now))

            return self.get_by_id(campaign_id)

    def _generate_stable_id(self, campaign: CampaignCreate) -> str:
        return generate_stable_id(
            campaign.project,
            campaign.name,
            campaign.network,
            campaign.deadline,
            str(campaign.official_url) if campaign.official_url else None
        )
        content = "|".join(parts)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_by_id(self, campaign_id: str) -> Optional[Campaign]:
        with get_db() as db:
            row = db.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
            if not row:
                return None
            campaign = self._row_to_campaign(row)
            campaign.evidence = self._get_evidence(campaign_id)
            campaign.risk_findings = self._get_risk_findings(campaign_id)
            campaign.eligibility = self._get_eligibility(campaign_id)
            return campaign

    def get_by_stable_id(self, stable_id: str) -> Optional[Campaign]:
        with get_db() as db:
            row = db.execute("SELECT * FROM campaigns WHERE stable_id = ?", (stable_id,)).fetchone()
            if not row:
                return None
            return self.get_by_id(row["id"])

    def _get_evidence(self, campaign_id: str) -> List[Evidence]:
        with get_db() as db:
            rows = db.execute("SELECT * FROM campaign_evidence WHERE campaign_id = ?", (campaign_id,)).fetchall()
            return [
                Evidence(
                    id=uuid.UUID(row["id"]),
                    campaign_id=uuid.UUID(row["campaign_id"]),
                    url=row["url"],
                    source_type=row["source_type"],
                    content_hash=row["content_hash"],
                    title=row["title"],
                    snippet=row["snippet"],
                    fetched_at=datetime.fromisoformat(row["fetched_at"]),
                    verified=bool(row["verified"])
                )
                for row in rows
            ]

    def _get_risk_findings(self, campaign_id: str) -> List[RiskFinding]:
        with get_db() as db:
            rows = db.execute("SELECT * FROM campaign_risk_findings WHERE campaign_id = ?", (campaign_id,)).fetchall()
            return [
                RiskFinding(
                    id=uuid.UUID(row["id"]),
                    campaign_id=uuid.UUID(row["campaign_id"]),
                    rule_id=row["rule_id"],
                    rule_version=row["rule_version"],
                    finding=row["finding"],
                    severity=RiskLevel(row["severity"]),
                    description=row["description"],
                    evidence_url=row["evidence_url"],
                    timestamp=datetime.fromisoformat(row["timestamp"])
                )
                for row in rows
            ]

    def _get_eligibility(self, campaign_id: str) -> List[EligibilityRequirement]:
        with get_db() as db:
            rows = db.execute("SELECT * FROM campaign_eligibility WHERE campaign_id = ?", (campaign_id,)).fetchall()
            return [
                EligibilityRequirement(
                    id=uuid.UUID(row["id"]),
                    campaign_id=uuid.UUID(row["campaign_id"]),
                    category=row["category"],
                    requirement=row["requirement"],
                    status=row["status"],
                    evidence_url=row["evidence_url"],
                    source=row["source"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    notes=row["notes"]
                )
                for row in rows
            ]

    def update(self, campaign_id: str, update: CampaignUpdate) -> Optional[Campaign]:
        with get_db() as db:
            existing = db.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
            if not existing:
                return None

            now = datetime.utcnow().isoformat()
            updates = []
            params = []

            fields = {
                "name": update.name,
                "project": update.project,
                "type": update.type.value if update.type else None,
                "network": update.network,
                "description": update.description,
                "official_url": str(update.official_url) if update.official_url else None,
                "campaign_url": str(update.campaign_url) if update.campaign_url else None,
                "status": update.status.value if update.status else None,
                "verification_status": update.verification_status.value if update.verification_status else None,
                "risk_level": update.risk_level.value if update.risk_level else None,
                "risk_score": update.risk_score,
                "deadline": update.deadline.isoformat() if update.deadline else None,
                "snapshot_date": update.snapshot_date.isoformat() if update.snapshot_date else None,
            }

            for field, value in fields.items():
                if value is not None:
                    updates.append(f"{field} = ?")
                    params.append(value)

            if updates:
                updates.append("updated_at = ?")
                params.append(now)
                params.append(campaign_id)
                db.execute(f"UPDATE campaigns SET {', '.join(updates)} WHERE id = ?", params)

            return self.get_by_id(campaign_id)

    def delete(self, campaign_id: str) -> bool:
        with get_db() as db:
            cursor = db.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
            return cursor.rowcount > 0

    def list(self, filters: CampaignFilters, pagination: PaginationParams) -> CampaignsResponse:
        with get_db() as db:
            where_clauses = []
            params = []

            if filters.type:
                where_clauses.append("type = ?")
                params.append(filters.type.value)
            if filters.network:
                where_clauses.append("network = ?")
                params.append(filters.network)
            if filters.status:
                where_clauses.append("status = ?")
                params.append(filters.status.value)
            if filters.verification_status:
                where_clauses.append("verification_status = ?")
                params.append(filters.verification_status.value)
            if filters.risk_level:
                where_clauses.append("risk_level = ?")
                params.append(filters.risk_level.value)
            if filters.search:
                where_clauses.append("(name LIKE ? OR project LIKE ? OR description LIKE ?)")
                search_term = f"%{filters.search}%"
                params.extend([search_term, search_term, search_term])

            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            order_by = filters.sort_by or "discovered_at"
            order_dir = filters.sort_order or "desc"
            if order_by not in ["name", "project", "type", "network", "status", "verification_status", "risk_level", "deadline", "discovered_at", "created_at"]:
                order_by = "discovered_at"
            if order_dir.lower() not in ["asc", "desc"]:
                order_dir = "desc"

            count_sql = f"SELECT COUNT(*) as count FROM campaigns {where_sql}"
            total = db.execute(count_sql, params).fetchone()["count"]

            offset = (pagination.page - 1) * pagination.page_size
            limit = pagination.page_size

            sql = f"""
                SELECT * FROM campaigns {where_sql}
                ORDER BY {order_by} {order_dir}
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            rows = db.execute(sql, params).fetchall()

            items = [self._row_to_list_item(row) for row in rows]
            total_pages = (total + pagination.page_size - 1) // pagination.page_size

            return CampaignsResponse(
                items=items,
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
                total_pages=total_pages
            )

    def get_recent(self, limit: int = 5) -> List[CampaignListItem]:
        with get_db() as db:
            rows = db.execute(
                "SELECT * FROM campaigns ORDER BY discovered_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [self._row_to_list_item(row) for row in rows]

    def get_upcoming_deadlines(self, limit: int = 5) -> List[Dict[str, Any]]:
        with get_db() as db:
            rows = db.execute("""
                SELECT id, stable_id, name, project, type, network, status,
                       verification_status, risk_level, deadline, discovered_at
                FROM campaigns
                WHERE deadline IS NOT NULL AND deadline > datetime('now')
                ORDER BY deadline ASC
                LIMIT ?
            """, (limit,)).fetchall()
            return [dict(row) for row in rows]

    def get_stats(self) -> Dict[str, int]:
        with get_db() as db:
            total = db.execute("SELECT COUNT(*) as count FROM campaigns").fetchone()["count"]
            tracked = db.execute("SELECT COUNT(*) as count FROM user_tracked").fetchone()["count"]
            verified = db.execute("SELECT COUNT(*) as count FROM campaigns WHERE verification_status = 'officially_corroborated'").fetchone()["count"]
            high_risk = db.execute("SELECT COUNT(*) as count FROM campaigns WHERE risk_level IN ('high', 'critical')").fetchone()["count"]
            return {
                "total_campaigns": total,
                "tracked_campaigns": tracked,
                "verified_campaigns": verified,
                "high_risk_campaigns": high_risk
            }

    def add_evidence(self, campaign_id: str, evidence: Evidence) -> Evidence:
        with get_db() as db:
            now = datetime.utcnow().isoformat()
            evidence_id = str(uuid.uuid4())
            db.execute("""
                INSERT INTO campaign_evidence (id, campaign_id, url, source_type, content_hash, title, snippet, fetched_at, verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evidence_id, campaign_id, str(evidence.url), evidence.source_type.value,
                evidence.content_hash, evidence.title, evidence.snippet, now, evidence.verified
            ))
            evidence.id = uuid.UUID(evidence_id)
            evidence.fetched_at = datetime.fromisoformat(now)
            return evidence

    def add_risk_finding(self, campaign_id: str, finding: RiskFinding) -> RiskFinding:
        with get_db() as db:
            finding_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            db.execute("""
                INSERT INTO campaign_risk_findings (id, campaign_id, rule_id, rule_version, finding, severity, description, evidence_url, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                finding_id, campaign_id, finding.rule_id, finding.rule_version,
                finding.finding, finding.severity.value, finding.description,
                str(finding.evidence_url) if finding.evidence_url else None, now
            ))
            finding.id = uuid.UUID(finding_id)
            finding.timestamp = datetime.fromisoformat(now)
            return finding

    def add_eligibility(self, campaign_id: str, eligibility: EligibilityRequirement) -> EligibilityRequirement:
        with get_db() as db:
            eligibility_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            db.execute("""
                INSERT INTO campaign_eligibility (id, campaign_id, category, requirement, status, evidence_url, source, timestamp, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                eligibility_id, campaign_id, eligibility.category, eligibility.requirement,
                eligibility.status, str(eligibility.evidence_url) if eligibility.evidence_url else None,
                eligibility.source, now, eligibility.notes
            ))
            eligibility.id = uuid.UUID(eligibility_id)
            eligibility.timestamp = datetime.fromisoformat(now)
            return eligibility

    def find_duplicates(self, campaign: CampaignCreate, threshold: float = 0.85) -> List[Tuple[Campaign, float, str]]:
        """Find potential duplicates for a campaign."""
        with get_db() as db:
            # Get all existing campaigns for comparison
            rows = db.execute("SELECT * FROM campaigns").fetchall()
            existing = [dict(row) for row in rows]
            
            # Convert campaign to dict for comparison
            campaign_dict = {
                'name': campaign.name,
                'project': campaign.project,
                'network': campaign.network,
                'official_url': str(campaign.official_url) if campaign.official_url else None,
                'campaign_url': str(campaign.campaign_url) if campaign.campaign_url else None,
                'deadline': campaign.deadline.isoformat() if campaign.deadline else None,
                'stable_id': self._generate_stable_id(campaign)
            }
            
            duplicates = find_potential_duplicates(campaign_dict, existing, threshold)
            results = []
            for existing_camp, score, reason in duplicates:
                existing_campaign = self.get_by_id(existing_camp['id'])
                if existing_campaign:
                    results.append((existing_campaign, score, reason))
            return results

    def get_or_create_deduplicated(self, campaign: CampaignCreate, source_id: Optional[str] = None, threshold: float = 0.85) -> Tuple[Campaign, bool, Optional[Dict]]:
        """
        Get existing campaign if duplicate found, otherwise create new.
        Returns: (campaign, is_new, duplicate_info)
        """
        duplicates = self.find_duplicates(campaign, threshold)
        
        if duplicates:
            # Use the highest scoring duplicate
            existing_campaign, score, reason = duplicates[0]
            
            # Update last_seen_at and record the discovery
            with get_db() as db:
                now = datetime.utcnow().isoformat()
                db.execute("""
                    UPDATE campaigns SET last_seen_at = ?, updated_at = ? WHERE id = ?
                """, (now, now, str(existing_campaign.id)))
                
                # Record field change history for last_seen_at
                db.execute("""
                    INSERT INTO campaign_field_history (id, campaign_id, field_name, old_value, new_value, changed_at, change_source, source_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), str(existing_campaign.id), 'last_seen_at',
                    existing_campaign.last_seen_at.isoformat() if existing_campaign.last_seen_at else None,
                    now, now, 'discovery', source_id
                ))
                
                # Record lifecycle event
                db.execute("""
                    INSERT INTO campaign_lifecycle_events (id, campaign_id, event_type, old_status, new_status, event_data, detected_by, source_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), str(existing_campaign.id), 'updated',
                    None, None,
                    json.dumps({'reason': 'rediscovered', 'source_id': source_id, 'similarity': score}),
                    'discovery', source_id, now
                ))
            
            duplicate_info = {
                'matched_campaign_id': str(existing_campaign.id),
                'similarity': duplicates[0][1],
                'reason': duplicates[0][2],
                'action': 'updated_existing'
            }
            return self.get_by_id(str(existing_campaign.id)), False, duplicate_info
        
        # No duplicate found, create new
        new_campaign = self.create(campaign, source_id)
        
        # Record lifecycle event for new campaign
        with get_db() as db:
            now = datetime.utcnow().isoformat()
            db.execute("""
                INSERT INTO campaign_lifecycle_events (id, campaign_id, event_type, old_status, new_status, event_data, detected_by, source_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), str(new_campaign.id), 'created',
                None, new_campaign.status.value,
                json.dumps({'source_id': source_id}),
                'discovery', source_id, now
            ))
        
        return new_campaign, True, None

    def record_field_change(self, campaign_id: str, field_name: str, old_value: Any, new_value: Any, change_source: str = 'discovery', source_id: Optional[str] = None) -> None:
        """Record a field change in the audit history."""
        with get_db() as db:
            now = datetime.utcnow().isoformat()
            db.execute("""
                INSERT INTO campaign_field_history (id, campaign_id, field_name, old_value, new_value, changed_at, change_source, source_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), campaign_id, field_name,
                str(old_value) if old_value is not None else None,
                str(new_value) if new_value is not None else None,
                now, change_source, source_id
            ))

    def record_lifecycle_event(self, campaign_id: str, event_type: str, old_status: Optional[str] = None, new_status: Optional[str] = None, event_data: Optional[Dict] = None, detected_by: str = 'system', source_id: Optional[str] = None) -> None:
        """Record a lifecycle event for a campaign."""
        with get_db() as db:
            now = datetime.utcnow().isoformat()
            db.execute("""
                INSERT INTO campaign_lifecycle_events (id, campaign_id, event_type, old_status, new_status, event_data, detected_by, source_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), campaign_id, event_type,
                old_status, new_status,
                json.dumps(event_data) if event_data else None,
                detected_by, source_id, now
            ))

    def merge_campaigns(self, surviving_id: str, merged_id: str, similarity: float, reasons: List[str], field_comparison: Dict, merged_by: str = 'system', source_id: Optional[str] = None) -> Campaign:
        """Merge two campaigns, keeping the surviving one and archiving the merged one."""
        with get_db() as db:
            now = datetime.utcnow().isoformat()
            
            # Get both campaigns
            surviving = self.get_by_id(surviving_id)
            merged = self.get_by_id(merged_id)
            
            if not surviving or not merged:
                raise ValueError("One or both campaigns not found")
            
            # Merge evidence, risk findings, eligibility from merged into surviving
            for evidence in merged.evidence:
                self.add_evidence(surviving_id, evidence)
            
            for finding in merged.risk_findings:
                self.add_risk_finding(surviving_id, finding)
            
            for eligibility in merged.eligibility:
                self.add_eligibility(surviving_id, eligibility)
            
            # Record merge audit
            merge_id = str(uuid.uuid4())
            db.execute("""
                INSERT INTO campaign_merge_audit (id, surviving_campaign_id, merged_campaign_id, merged_campaign_stable_id, match_reasons, similarity_score, field_comparison, merged_by, merged_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                merge_id, surviving_id, merged_id, merged.stable_id,
                json.dumps(reasons), similarity, json.dumps(field_comparison), merged_by, now
            ))
            
            # Record field changes for merged fields
            merged_fields = ['evidence', 'risk_findings', 'eligibility']
            for field in merged_fields:
                merged_count = len(getattr(merged, field, []))
                if merged_count > 0:
                    self.record_field_change(
                        surviving_id, field, None, f"Merged {merged_count} items from {merged_id}",
                        'merge', source_id
                    )
            
            # Record lifecycle events
            self.record_lifecycle_event(surviving_id, 'merged', None, None, 
                {'merged_campaign_id': merged_id, 'similarity': similarity, 'reasons': reasons}, 'merge', source_id)
            self.record_lifecycle_event(merged_id, 'merged', None, None,
                {'surviving_campaign_id': surviving_id, 'merged_into': surviving_id}, 'merge', source_id)
            
            # Delete the merged campaign (cascades to evidence, risk_findings, eligibility)
            db.execute("DELETE FROM campaigns WHERE id = ?", (merged_id,))
            
            return self.get_by_id(surviving_id)

    def get_merge_history(self, campaign_id: str) -> List[Dict]:
        """Get merge history for a campaign."""
        with get_db() as db:
            rows = db.execute("""
                SELECT * FROM campaign_merge_audit 
                WHERE surviving_campaign_id = ? OR merged_campaign_id = ?
                ORDER BY merged_at DESC
            """, (campaign_id, campaign_id)).fetchall()
            return [dict(row) for row in rows]

    def get_field_history(self, campaign_id: str, field_name: Optional[str] = None) -> List[Dict]:
        """Get field change history for a campaign."""
        with get_db() as db:
            if field_name:
                rows = db.execute("""
                    SELECT * FROM campaign_field_history 
                    WHERE campaign_id = ? AND field_name = ?
                    ORDER BY changed_at DESC
                """, (campaign_id, field_name)).fetchall()
            else:
                rows = db.execute("""
                    SELECT * FROM campaign_field_history 
                    WHERE campaign_id = ?
                    ORDER BY changed_at DESC
                """, (campaign_id,)).fetchall()
            return [dict(row) for row in rows]

    def get_lifecycle_events(self, campaign_id: str) -> List[Dict]:
        """Get lifecycle events for a campaign."""
        with get_db() as db:
            rows = db.execute("""
                SELECT * FROM campaign_lifecycle_events 
                WHERE campaign_id = ?
                ORDER BY created_at DESC
            """, (campaign_id,)).fetchall()
            return [dict(row) for row in rows]

    def detect_lifecycle_changes(self) -> Dict[str, int]:
        """Detect campaigns that have changed lifecycle status (expired, withdrawn, etc.)."""
        with get_db() as db:
            now = datetime.utcnow().isoformat()
            changes = {'expired': 0, 'withdrawn': 0, 'revived': 0}
            
            # Find campaigns that should be expired (deadline passed, still active)
            expired_campaigns = db.execute("""
                SELECT id, status FROM campaigns 
                WHERE deadline IS NOT NULL 
                AND deadline < ? 
                AND status = 'active'
            """, (now,)).fetchall()
            
            for campaign in expired_campaigns:
                campaign_id = campaign['id']
                old_status = campaign['status']
                self.record_lifecycle_event(campaign_id, 'status_changed', old_status, 'expired', 
                    {'reason': 'deadline_passed'}, 'system')
                
                db.execute("UPDATE campaigns SET status = ?, updated_at = ? WHERE id = ?", 
                          ('expired', datetime.utcnow().isoformat(), campaign_id))
                self.record_field_change(campaign_id, 'status', old_status, 'expired', 'system')
                changes['expired'] += 1
            
            # Find campaigns that should be revived (were expired, now have future deadline)
            revived_campaigns = db.execute("""
                SELECT id, status FROM campaigns 
                WHERE deadline IS NOT NULL 
                AND deadline > ? 
                AND status = 'expired'
            """, (now,)).fetchall()
            
            for campaign in revived_campaigns:
                campaign_id = campaign['id']
                old_status = campaign['status']
                self.record_lifecycle_event(campaign_id, 'status_changed', old_status, 'active', 
                    {'reason': 'deadline_extended'}, 'system')
                
                db.execute("UPDATE campaigns SET status = ?, updated_at = ? WHERE id = ?", 
                          ('active', datetime.utcnow().isoformat(), campaign_id))
                self.record_field_change(campaign_id, 'status', old_status, 'active', 'system')
                changes['revived'] += 1
            
            return changes


campaign_repository = CampaignRepository()