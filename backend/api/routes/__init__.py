from .health import router as health_router
from .dashboard import router as dashboard_router
from .campaigns import router as campaigns_router
from .sources import router as sources_router
from .discovery import router as discovery_router
from .verification_risk import router as verification_risk_router
from .eligibility import router as eligibility_router
from .category import router as category_router
from .backup import router as backup_router

__all__ = ['health_router', 'dashboard_router', 'campaigns_router', 'sources_router', 'discovery_router', 'verification_risk_router', 'eligibility_router', 'category_router', 'backup_router']