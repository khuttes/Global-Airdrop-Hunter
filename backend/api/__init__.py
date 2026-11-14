from fastapi import APIRouter
from .routes import health_router, dashboard_router, campaigns_router, sources_router, discovery_router, verification_risk_router, eligibility_router, category_router, backup_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router, tags=["health"])
api_router.include_router(dashboard_router, tags=["dashboard"])
api_router.include_router(campaigns_router, tags=["campaigns"])
api_router.include_router(sources_router, tags=["sources"])
api_router.include_router(discovery_router, tags=["discovery"])
api_router.include_router(verification_risk_router, tags=["verification", "risk"])
api_router.include_router(eligibility_router, tags=["eligibility", "progress", "claims"])
api_router.include_router(category_router, tags=["nft", "testnet", "reward", "events", "notifications"])
api_router.include_router(backup_router, tags=["backup", "restore"])

__all__ = ['api_router']