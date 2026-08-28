from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form, Body
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.domain import DataSource, DataIngestionJob, IndustrialFacility, ThermalEvent
from data_pipeline.adapters.firms_adapter import firms_adapter, FIRMSAdapter
from data_pipeline.adapters.osm_adapter import osm_adapter, OSMIndustrialAdapter
from data_pipeline.adapters.cea_adapter import cea_adapter
from data_pipeline.adapters.bhuvan_adapter import bhuvan_adapter
from data_pipeline.adapters.sentinel_adapter import sentinel_adapter
from data_pipeline.adapters.landsat_adapter import landsat_adapter
from data_pipeline.adapters.mosdac_adapter import mosdac_adapter
from backend.app.services.facility_resolver import facility_resolver
from backend.app.services.pipeline_service import pipeline_service
from database.seed_data import seed_database

router = APIRouter()


@router.get("/sources")
def list_data_sources(db: Session = Depends(get_db)):
    """
    Lists configured external geospatial & remote sensing data source adapters from database.
    """
    sources = db.query(DataSource).all()
    return sources


@router.get("/sources/status")
def get_all_sources_live_status():
    """
    Control Center Diagnostic API:
    Executes live non-blocking connectivity & authentication tests across all 7 data source adapters.
    """
    statuses = [
        firms_adapter.validate_connection(),
        osm_adapter.validate_connection(),
        cea_adapter.validate_connection(),
        bhuvan_adapter.validate_connection(),
        sentinel_adapter.validate_connection(),
        landsat_adapter.validate_connection(),
        mosdac_adapter.validate_connection()
    ]
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_sources": len(statuses),
        "online_sources": sum(1 for s in statuses if s.get("status") == "HEALTHY"),
        "sources": statuses
    }


@router.get("/jobs/history")
def get_ingestion_jobs_history(db: Session = Depends(get_db), limit: int = 20):
    """
    Retrieves execution history of automated Celery and manual ingestion jobs.
    """
    jobs = db.query(DataIngestionJob).order_by(DataIngestionJob.started_at.desc()).limit(limit).all()
    return jobs


@router.post("/trigger/demo-seed")
def trigger_seed_ingestion(db: Session = Depends(get_db)):
    """
    Triggers re-seeding of realistic Indian thermal observations and intelligence layers.
    """
    seed_database(db)
    return {"status": "SUCCESS", "message": "Demo industrial dataset successfully populated."}


@router.post("/trigger/firms")
def trigger_firms_ingestion(
    country: str = "IND",
    days: int = 1,
    source_type: str = "VIIRS_NOAA20_NRT",
    db: Session = Depends(get_db)
):
    """
    Triggers live ingestion from NASA FIRMS API (using FIRMS_MAP_KEY environment variable).
    """
    if not settings.FIRMS_MAP_KEY:
        return {
            "status": "FALLBACK_DEMO_ACTIVE",
            "message": "FIRMS_MAP_KEY not set. Using verified offline telemetry cache.",
            "data_source_status": "DEMO_FALLBACK"
        }

    observations = firms_adapter.fetch_thermal_observations(country=country, days=days, sensor=source_type)
    if not observations:
        return {"status": "NO_NEW_DATA", "message": "No new thermal anomalies found in the requested window."}

    result = pipeline_service.process_observations(db, observations, source_name=f"NASA FIRMS {source_type}")
    return result


@router.post("/trigger/osm")
def trigger_osm_facility_ingestion(db: Session = Depends(get_db)):
    """
    Ingests and resolves industrial facilities from OpenStreetMap Overpass API.
    """
    facilities = osm_adapter.fetch_facilities()
    result = facility_resolver.resolve_and_sync_facilities(db, facilities)
    return result


@router.post("/trigger/cea")
def trigger_cea_facility_ingestion(db: Session = Depends(get_db)):
    """
    Ingests official thermal power stations from Central Electricity Authority (CEA).
    """
    facilities = cea_adapter.fetch_facilities()
    result = facility_resolver.resolve_and_sync_facilities(db, facilities)
    return result


@router.post("/trigger/sync-all")
def trigger_sync_all_sources(db: Session = Depends(get_db)):
    """
    Executes a multi-source synchronization across FIRMS, OSM, CEA, and Sentinel catalog.
    """
    # 1. Facilities
    facs = osm_adapter.fetch_facilities() + cea_adapter.fetch_facilities()
    fac_res = facility_resolver.resolve_and_sync_facilities(db, facs)

    # 2. Thermal Hotspots
    firms_obs = firms_adapter.fetch_thermal_observations(country="IND", days=1)
    if firms_obs:
        pipe_res = pipeline_service.process_observations(db, firms_obs, source_name="NASA_FIRMS_VIIRS")
    else:
        pipe_res = {"status": "NO_FIRMS_CREDS_DEMO_PRESERVED"}

    return {
        "status": "SUCCESS",
        "facilities_sync": fac_res,
        "thermal_pipeline": pipe_res,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/upload-csv")
async def upload_firms_csv(
    file: UploadFile = File(...),
    source_name: str = Form("VIIRS_CSV_UPLOAD"),
    is_demo: bool = Form(False),
    db: Session = Depends(get_db)
):
    """
    Uploads and processes a local NASA FIRMS CSV file without requiring API keys.
    """
    contents = await file.read()
    csv_text = contents.decode("utf-8", errors="ignore")

    observations = firms_adapter.parse_csv_content(csv_text, source_name=source_name, is_demo=is_demo)
    if not observations:
        raise HTTPException(status_code=400, detail="No valid thermal observations found in CSV.")

    result = pipeline_service.process_observations(db, observations, source_name=f"Uploaded CSV ({file.filename})")
    return result


@router.post("/upload-json")
def upload_thermal_json(
    records: List[Dict[str, Any]] = Body(...),
    source_name: str = "JSON_TELEMETRY",
    is_demo: bool = False,
    db: Session = Depends(get_db)
):
    """
    Directly ingests a JSON list of raw thermal telemetry records.
    """
    observations = firms_adapter.parse_json_content(records, source_name=source_name, is_demo=is_demo)
    if not observations:
        raise HTTPException(status_code=400, detail="No valid coordinates or records in JSON payload.")

    result = pipeline_service.process_observations(db, observations, source_name=source_name)
    return result
