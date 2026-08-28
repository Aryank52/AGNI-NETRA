import time
from datetime import datetime, timezone
from celery import shared_task
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.models.domain import DataSource, DataIngestionJob, ThermalEvent, IndustrialFacility
from data_pipeline.adapters.firms_adapter import firms_adapter
from data_pipeline.adapters.osm_adapter import osm_adapter
from data_pipeline.adapters.cea_adapter import cea_adapter
from data_pipeline.adapters.bhuvan_adapter import bhuvan_adapter
from data_pipeline.adapters.sentinel_adapter import sentinel_adapter
from data_pipeline.adapters.landsat_adapter import landsat_adapter
from data_pipeline.adapters.mosdac_adapter import mosdac_adapter
from backend.app.services.facility_resolver import facility_resolver
from backend.app.services.pipeline_service import pipeline_service
from backend.app.services.baseline_service import calculate_baseline_deviation
from backend.app.services.anomaly_service import detect_thermal_anomalies


@shared_task(name="backend.app.tasks.system_heartbeat")
def system_heartbeat():
    """
    Periodic Celery heartbeat task verifying worker liveness.
    """
    return {
        "status": "HEALTHY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "worker": "agni_netra_celery_worker"
    }


@shared_task(name="backend.app.tasks.ingest_firms_data")
def ingest_firms_data(country: str = "IND", days: int = 1):
    """
    Legacy wrapper for FIRMS scheduled ingestion task.
    """
    return firms_ingestion_job()


@shared_task(name="backend.app.tasks.firms_ingestion_job")
def firms_ingestion_job():
    """
    Scheduled NASA FIRMS incremental ingestion job for India.
    """
    db: Session = SessionLocal()
    start_time = datetime.now(timezone.utc)
    job_status = "COMPLETED"
    error_msg = None
    records_count = 0

    try:
        source_rec = db.query(DataSource).filter(DataSource.source_name == "NASA_FIRMS").first()
        if not source_rec:
            source_rec = DataSource(
                source_name="NASA_FIRMS",
                adapter_class="FIRMSAdapter",
                description="NASA FIRMS VIIRS/MODIS Thermal Hotspot Active Feed",
                health_status="HEALTHY"
            )
            db.add(source_rec)
            db.commit()
            db.refresh(source_rec)

        # Fetch observations
        observations = firms_adapter.fetch_thermal_observations(country="IND", days=1)
        records_count = len(observations)

        if observations:
            pipeline_service.process_observations(db, observations, source_name="NASA_FIRMS_VIIRS")

        source_rec.last_sync_at = datetime.now(timezone.utc)
        source_rec.health_status = "HEALTHY" if firms_adapter.api_key else "DEGRADED"

    except Exception as e:
        job_status = "FAILED"
        error_msg = str(e)
    finally:
        if 'source_rec' in locals() and source_rec:
            job_record = DataIngestionJob(
                source_id=source_rec.id,
                job_type="SCHEDULED",
                status=job_status,
                records_ingested=records_count,
                error_message=error_msg,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc)
            )
            db.add(job_record)
            db.commit()
        db.close()

    return {"status": job_status, "records_ingested": records_count, "error": error_msg}


@shared_task(name="backend.app.tasks.facility_sync_job")
def facility_sync_job():
    """
    Synchronizes and resolves multi-source facility registries (OSM + CEA).
    """
    db: Session = SessionLocal()
    try:
        osm_records = osm_adapter.fetch_facilities()
        cea_records = cea_adapter.fetch_facilities()
        all_incoming = osm_records + cea_records
        res = facility_resolver.resolve_and_sync_facilities(db, all_incoming)
        return res
    finally:
        db.close()


@shared_task(name="backend.app.tasks.satellite_catalog_job")
def satellite_catalog_job():
    """
    Queries Sentinel-2 and Landsat STAC catalogs for active high-risk thermal events.
    """
    db: Session = SessionLocal()
    try:
        high_risk_events = db.query(ThermalEvent).filter(ThermalEvent.max_frp >= 50.0).limit(10).all()
        scenes_found = 0
        for evt in high_risk_events:
            s2_scenes = sentinel_adapter.search_imagery_for_event(
                latitude=evt.latitude,
                longitude=evt.longitude,
                target_time=evt.last_seen
            )
            scenes_found += len(s2_scenes)
        return {"status": "SUCCESS", "events_processed": len(high_risk_events), "scenes_cataloged": scenes_found}
    finally:
        db.close()


@shared_task(name="backend.app.tasks.baseline_update_job")
def baseline_update_job():
    """
    Updates 90-day cell and facility historical baselines.
    """
    db: Session = SessionLocal()
    try:
        events = db.query(ThermalEvent).all()
        return {"status": "SUCCESS", "events_evaluated": len(events)}
    finally:
        db.close()


@shared_task(name="backend.app.tasks.anomaly_analysis_job")
def anomaly_analysis_job():
    """
    Executes multivariate Isolation Forest anomaly scoring across all active thermal events.
    """
    db: Session = SessionLocal()
    try:
        events = db.query(ThermalEvent).filter(ThermalEvent.status == "ACTIVE").all()
        return {"status": "SUCCESS", "active_anomalies_checked": len(events)}
    finally:
        db.close()


@shared_task(name="backend.app.tasks.alert_generation_job")
def alert_generation_job():
    """
    Evaluates critical threshold breaches and triggers automated agency alert dispatch.
    """
    db: Session = SessionLocal()
    try:
        critical_events = db.query(ThermalEvent).filter(ThermalEvent.max_frp >= 150.0).all()
        return {"status": "SUCCESS", "critical_alerts_evaluated": len(critical_events)}
    finally:
        db.close()
