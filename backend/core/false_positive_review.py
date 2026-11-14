"""
False Positive Review Queue for Global Airdrop Hunter.
Allows manual review of suspicious campaigns flagged by risk engine.
"""

import sqlite3
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass

from backend.database.connection import get_db


class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    CONFIRMED_LEGITIMATE = "confirmed_legitimate"
    CONFIRMED_SUSPICIOUS = "confirmed_suspicious"
    FALSE_POSITIVE = "false_positive"
    DISMISSED = "dismissed"


class ReviewPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ReviewQueueItem:
    id: str
    campaign_id: str
    risk_score: int
    risk_level: str
    trigger_rules: List[str]
    status: ReviewStatus
    priority: ReviewPriority
    reviewer_notes: Optional[str]
    created_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]


class FalsePositiveReviewQueue:
    """Queue for reviewing false positives from risk engine."""
    
    def __init__(self):
        self._ensure_table()
    
    def _ensure_table(self):
        """Ensure the review queue table exists."""
        with get_db() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS false_positive_review_queue (
                    id TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    risk_level TEXT NOT NULL,
                    trigger_rules TEXT NOT NULL,  -- JSON array
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority TEXT NOT NULL DEFAULT 'medium',
                    reviewer_notes TEXT,
                    created_at TIMESTAMP NOT NULL,
                    reviewed_at TIMESTAMP,
                    reviewed_by TEXT,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
                )
            """)
            # Index for pending items
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_fprq_status_priority 
                ON false_positive_review_queue(status, priority)
            """)
    
    def add_to_queue(
        self,
        campaign_id: str,
        risk_score: int,
        risk_level: str,
        trigger_rules: List[str],
        priority: ReviewPriority = ReviewPriority.MEDIUM
    ) -> str:
        """Add a campaign to the review queue."""
        review_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        with get_db() as db:
            db.execute("""
                INSERT INTO false_positive_review_queue 
                (id, campaign_id, risk_score, risk_level, trigger_rules, status, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                review_id, campaign_id, risk_score, risk_level,
                json.dumps(trigger_rules), ReviewStatus.PENDING.value,
                priority.value, now
            ))
        
        return review_id
    
    def get_pending(self, limit: int = 50, priority: Optional[ReviewPriority] = None) -> List[Dict]:
        """Get pending review items."""
        with get_db() as db:
            if priority:
                rows = db.execute("""
                    SELECT * FROM false_positive_review_queue
                    WHERE status = 'pending' AND priority = ?
                    ORDER BY 
                        CASE priority 
                            WHEN 'critical' THEN 4
                            WHEN 'high' THEN 3
                            WHEN 'medium' THEN 2
                            WHEN 'low' THEN 1
                        END DESC,
                        created_at ASC
                    LIMIT ?
                """, (priority.value, limit)).fetchall()
            else:
                rows = db.execute("""
                    SELECT * FROM false_positive_review_queue
                    WHERE status = 'pending'
                    ORDER BY 
                        CASE priority 
                            WHEN 'critical' THEN 4
                            WHEN 'high' THEN 3
                            WHEN 'medium' THEN 2
                            WHEN 'low' THEN 1
                        END DESC,
                        created_at ASC
                    LIMIT ?
                """, (limit,)).fetchall()
            return [dict(row) for row in rows]
    
    def get_by_campaign(self, campaign_id: str) -> Optional[Dict]:
        """Get review item for a specific campaign."""
        with get_db() as db:
            row = db.execute("""
                SELECT * FROM false_positive_review_queue
                WHERE campaign_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (campaign_id,)).fetchone()
            return dict(row) if row else None
    
    def start_review(self, review_id: str, reviewer: str) -> bool:
        """Mark item as in review."""
        with get_db() as db:
            cursor = db.execute("""
                UPDATE false_positive_review_queue
                SET status = ?, reviewed_by = ?, reviewed_at = ?
                WHERE id = ? AND status = 'pending'
            """, (ReviewStatus.IN_REVIEW.value, reviewer, datetime.utcnow().isoformat(), review_id))
            return cursor.rowcount > 0
    
    def complete_review(
        self,
        review_id: str,
        status: ReviewStatus,
        reviewer: str,
        notes: Optional[str] = None
    ) -> bool:
        """Complete a review with final status."""
        with get_db() as db:
            cursor = db.execute("""
                UPDATE false_positive_review_queue
                SET status = ?, reviewer_notes = ?, reviewed_by = ?, reviewed_at = ?
                WHERE id = ? AND status = 'in_review'
            """, (status.value, notes, reviewer, datetime.utcnow().isoformat(), review_id))
            return cursor.rowcount > 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        with get_db() as db:
            stats = {}
            
            # Count by status
            rows = db.execute("""
                SELECT status, COUNT(*) as count FROM false_positive_review_queue
                GROUP BY status
            """).fetchall()
            stats['by_status'] = {row['status']: row['count'] for row in rows}
            
            # Count by priority
            rows = db.execute("""
                SELECT priority, COUNT(*) as count FROM false_positive_review_queue
                WHERE status = 'pending'
                GROUP BY priority
            """).fetchall()
            stats['pending_by_priority'] = {row['priority']: row['count'] for row in rows}
            
            # Total
            stats['total'] = sum(stats['by_status'].values())
            stats['pending_total'] = stats['by_status'].get('pending', 0)
            
            return stats
    
    def auto_enqueue_high_risk(self, campaign_id: str, risk_score: int, risk_level: str, trigger_rules: List[str]) -> Optional[str]:
        """Auto-enqueue campaigns that exceed risk thresholds."""
        # Only enqueue high/critical risk campaigns
        if risk_level in ('high', 'critical'):
            priority = ReviewPriority.HIGH if risk_level == 'high' else ReviewPriority.CRITICAL
            return self.add_to_queue(campaign_id, risk_score, risk_level, trigger_rules, priority)
        return None


false_positive_review_queue = FalsePositiveReviewQueue()