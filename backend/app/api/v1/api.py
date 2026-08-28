from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    auth, events, facilities, candidates, anomalies,
    risk, alerts, verification, analytics, reports,
    ingestion, ml, admin, baselines, portals
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(events.router, prefix="/events", tags=["Thermal Events"])
api_router.include_router(facilities.router, prefix="/facilities", tags=["Industrial Facilities"])
api_router.include_router(candidates.router, prefix="/candidates", tags=["Candidate Discovery"])
api_router.include_router(baselines.router, prefix="/baselines", tags=["Thermal Baselines"])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["Anomalies"])
api_router.include_router(risk.router, prefix="/risk", tags=["Risk Intelligence"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(verification.router, prefix="/verification", tags=["Human-in-the-Loop Verification"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & KPIs"])
api_router.include_router(reports.router, prefix="/reports", tags=["PDF Reports & Exports"])
api_router.include_router(portals.router, prefix="/portals", tags=["Research, Industry & Public Portals"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["Data Ingestion"])
api_router.include_router(ml.router, prefix="/ml", tags=["Machine Learning & SHAP"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin & Audit"])
