from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.api.deps import require_admin
from backend.app.models.domain import DataSource, DataIngestionJob, User
from data_pipeline.adapters.firms_adapter import FIRMSAdapter
from database.seed_data import seed_database

router = APIRouter()


@router.get("/sources")
def list_data_sources(db: Session = Depends(get_db)):
    """
    Lists configured external geospatial & remote sensing data source adapters and health statuses.
    """
    sources = db.query(DataSource).all()
    return sources


@router.post("/trigger/demo-seed")
def trigger_seed_ingestion(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Triggers re-seeding / generation of realistic Indian thermal observations and intelligence layers.
    """
    seed_database(db)
    return {"status": "SUCCESS", "message": "Demo industrial dataset successfully populated."}


@router.post("/trigger/firms")
def trigger_firms_ingestion(
    country: str = "IND",
    days: int = 1,
    db: Session = Depends(get_db)
):
    """
    Triggers live ingestion from NASA FIRMS API (falls back gracefully if API key not provided).
    """
    adapter = FIRMSAdapter(api_key=settings.FIRMS_MAP_KEY)
    
    if not settings.FIRMS_MAP_KEY:
        return {
            "status": "FALLBACK_DEMO_ACTIVE",
            "message": "FIRMS API Key not configured. Active demo mode dataset is operational.",
            "data_source_status": "DEMO_FALLBACK"
        }

    obs = adapter.fetch_data(country=country, days=days)
    return {
        "status": "SUCCESS",
        "records_fetched": len(obs),
        "source": "NASA FIRMS NRT"
    }
