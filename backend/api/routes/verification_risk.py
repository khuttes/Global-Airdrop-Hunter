from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID

from backend.core.verification import domain_verification_service
from backend.core.verification_assessment import verification_service
from backend.core.risk import risk_engine
from backend.core.models import VerificationStatus, RiskLevel
from backend.database.repositories import campaign_repository

router = APIRouter()


@router.get("/campaigns/{campaign_id}/verification", response_model=dict)
async def get_campaign_verification(campaign_id: UUID):
    """Get verification assessment for a campaign."""
    verification = await verification_service.assess_verification(str(campaign_id))
    if "error" in verification:
        raise HTTPException(status_code=404, detail=verification)
    return verification


@router.post("/campaigns/{campaign_id}/verify", response_model=dict)
async def verify_campaign(campaign_id: UUID):
    """Trigger verification assessment for a campaign."""
    verification = await verification_service.assess_verification(str(campaign_id))
    if "error" in verification:
        raise HTTPException(status_code=404, detail=verification)
    return verification


@router.get("/campaigns/{campaign_id}/risk", response_model=dict)
async def get_campaign_risk(campaign_id: UUID):
    """Get risk assessment for a campaign."""
    assessment = risk_engine.assess_campaign(str(campaign_id))
    if "error" in assessment:
        raise HTTPException(status_code=404, detail=assessment)
    return assessment


@router.post("/campaigns/{campaign_id}/assess-risk", response_model=dict)
async def assess_campaign_risk(campaign_id: UUID):
    """Trigger risk assessment for a campaign."""
    assessment = risk_engine.assess_campaign(str(campaign_id))
    if "error" in assessment:
        raise HTTPException(status_code=404, detail=assessment)
    return assessment


@router.get("/domain/verify", response_model=dict)
async def verify_domain(url: str = Query(..., description="URL to verify")):
    """Verify a domain's authenticity."""
    result = await domain_verification_service.verify_domain(url)
    return result


@router.get("/risk/rules", response_model=List[dict])
async def list_risk_rules(
    category: Optional[str] = None,
    severity: Optional[str] = None,
    active_only: bool = Query(True)
):
    """List all risk rules."""
    from backend.database.connection import get_db
    with get_db() as db:
        where = []
        params = []
        if active_only:
            where.append("is_active = 1")
        if category:
            where.append("category = ?")
            params.append(category)
        if severity:
            where.append("severity = ?")
            params.append(severity)
        
        where_sql = "WHERE " + " AND ".join(where) if where else ""
        rows = db.execute(f"SELECT * FROM risk_rules {where_sql} ORDER BY weight DESC", params).fetchall()
        return [dict(row) for row in rows]


@router.get("/risk/rules/{rule_id}", response_model=dict)
async def get_risk_rule(rule_id: str):
    """Get a specific risk rule."""
    from backend.database.connection import get_db
    with get_db() as db:
        row = db.execute("SELECT * FROM risk_rules WHERE rule_id = ?", (rule_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Risk rule not found"})
        return dict(row)


@router.post("/risk/rules", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_risk_rule(rule: dict):
    """Create a new risk rule."""
    import uuid
    from backend.database.connection import get_db
    
    required_fields = ["rule_id", "name", "description", "category", "severity", "weight", "logic_type", "logic_config"]
    for field in required_fields:
        if field not in rule:
            raise HTTPException(status_code=400, detail={"code": "MISSING_FIELD", "message": f"Missing required field: {field}"})
    
    # Check if rule_id exists
    from backend.database.connection import get_db
    with get_db() as db:
        existing = db.execute("SELECT 1 FROM risk_rules WHERE rule_id = ?", (rule["rule_id"],)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail={"code": "DUPLICATE_RULE", "message": "Rule ID already exists"})
        
        rule_id = str(uuid.uuid4())
        db.execute("""
            INSERT INTO risk_rules (id, rule_id, version, name, description, category, severity, weight, is_critical_override, logic_type, logic_config)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rule_id,
            rule["rule_id"],
            rule.get("version", 1),
            rule["name"],
            rule["description"],
            rule["category"],
            rule["severity"],
            rule["weight"],
            int(rule.get("is_critical_override", False)),
            rule["logic_type"],
            json.dumps(rule["logic_config"])
        ))
        db.commit()
    
    return {"id": rule_id, "message": "Risk rule created"}


@router.patch("/risk/rules/{rule_id}", response_model=dict)
async def update_risk_rule(rule_id: str, update: dict):
    """Update a risk rule."""
    from backend.database.connection import get_db
    with get_db() as db:
        existing = db.execute("SELECT * FROM risk_rules WHERE rule_id = ?", (rule_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Risk rule not found"})
        
        fields = []
        params = []
        
        allowed_fields = ["name", "description", "category", "severity", "weight", "is_critical_override", "logic_type", "logic_config", "is_active"]
        for field in allowed_fields:
            if field in update:
                fields.append(f"{field} = ?")
                if field == "logic_config":
                    params.append(json.dumps(update[field]))
                else:
                    params.append(update[field])
        
        if fields:
            fields.append("updated_at = CURRENT_TIMESTAMP")
            params.append(rule_id)
            db.execute(f"UPDATE risk_rules SET {', '.join(fields)} WHERE rule_id = ?", params)
            db.commit()
    
    return {"message": "Risk rule updated"}


import json