from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form, Body
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.domain import DataSource, DataIngestionJob, IndustrialFacility
from data_pipeline.adapters.firms_adapter import FIRMSAdapter
from data_pipeline.adapters.osm_adapter import OSMIndustrialAdapter
from backend.app.services.pipeline_service import pipeline_service
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
    adapter = FIRMSAdapter(api_key=settings.FIRMS_MAP_KEY)
    
    if not settings.FIRMS_MAP_KEY:
        return {
            "status": "FALLBACK_DEMO_ACTIVE",
            "message": "FIRMS_MAP_KEY not set. Using local offline satellite data cache.",
            "data_source_status": "DEMO_FALLBACK"
        }

    observations = adapter.fetch_data(country=country, days=days, source_type=source_type)
    if not observations:
        return {"status": "NO_NEW_DATA", "message": "No new thermal anomalies found in the requested window."}

    # Process observations through PostGIS spatial enrichment & DBSCAN clustering
    result = pipeline_service.process_observations(db, observations, source_name=f"NASA FIRMS {source_type}")
    return result


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

    adapter = FIRMSAdapter()
    observations = adapter.parse_csv_content(csv_text, source_name=source_name, is_demo=is_demo)
    
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
    adapter = FIRMSAdapter()
    observations = adapter.parse_json_content(records, source_name=source_name, is_demo=is_demo)
    
    if not observations:
        raise HTTPException(status_code=400, detail="No valid coordinates or records in JSON payload.")

    result = pipeline_service.process_observations(db, observations, source_name=source_name)
    return result


@router.post("/trigger/osm")
def trigger_osm_facility_ingestion(db: Session = Depends(get_db)):
    """
    Ingests and normalizes industrial facilities from OpenStreetMap Overpass API.
    """
    adapter = OSMIndustrialAdapter()
    facilities = adapter.fetch_facilities_by_bbox()

    ingested_count = 0
    for fac in facilities:
        existing = db.query(IndustrialFacility).filter(IndustrialFacility.name == fac.name).first()
        if not existing:
            new_fac = IndustrialFacility(
                name=fac.name,
                facility_type=fac.facility_type,
                operator=fac.operator,
                state=fac.state,
                latitude=fac.latitude,
                longitude=fac.longitude,
                source=fac.source,
                source_id=fac.source_id,
                status="VERIFIED",
                raw_tags=fac.raw_tags
            )
            db.add(new_fac)
            ingested_count += 1

    db.commit()
    return {
        "status": "SUCCESS",
        "facilities_ingested": ingested_count,
        "total_facilities_in_registry": db.query(IndustrialFacility).count()
    }
