from fastapi import APIRouter, Depends
from backend.core.models import DashboardResponse, CampaignListItem
from backend.database import get_db
import sqlite3

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.execute("SELECT COUNT(*) as count FROM campaigns")
    total = cursor.fetchone()["count"]

    cursor = db.execute("SELECT COUNT(*) as count FROM user_tracked")
    tracked = cursor.fetchone()["count"]

    cursor = db.execute("SELECT COUNT(*) as count FROM campaigns WHERE verification_status = 'officially_corroborated'")
    verified = cursor.fetchone()["count"]

    cursor = db.execute("SELECT COUNT(*) as count FROM campaigns WHERE risk_level IN ('high', 'critical')")
    high_risk = cursor.fetchone()["count"]

    cursor = db.execute("""
        SELECT id, stable_id, name, project, type, network, status,
               verification_status, risk_level, deadline, discovered_at
        FROM campaigns
        ORDER BY discovered_at DESC
        LIMIT 5
    """)
    recent = [CampaignListItem(**dict(row)) for row in cursor.fetchall()]

    cursor = db.execute("""
        SELECT id, stable_id, name, project, type, network, status,
               verification_status, risk_level, deadline, discovered_at
        FROM campaigns
        WHERE deadline IS NOT NULL AND deadline > datetime('now')
        ORDER BY deadline ASC
        LIMIT 5
    """)
    upcoming = []
    for row in cursor.fetchall():
        item = dict(row)
        upcoming.append(item)

    return DashboardResponse(
        total_campaigns=total,
        tracked_campaigns=tracked,
        verified_campaigns=verified,
        high_risk_campaigns=high_risk,
        recent_campaigns=recent,
        upcoming_deadlines=upcoming,
    )