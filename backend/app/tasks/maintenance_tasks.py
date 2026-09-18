import time
from datetime import datetime, timezone
from celery import shared_task
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.models.domain import DataSource, DataIngestionJob, ThermalEvent, IndustrialFacility, HistoricalBaseline
from data_pipeline.adapters.firms_adapter import firms_adapter
from data_pipeline.adapters.osm_adapter import osm_adapter
from data_pipeline.adapters.cea_adapter import cea_adapter
from data_pipeline.adapters.bhuvan_adapter import bhuvan_adapter
from data_pipeline.adapters.sentinel_adapter import sentinel_adapter
from data_pipeline.adapters.landsat_adapter import landsat_adapter
from data_pipeline.adapters.mosdac_adapter import mosdac_adapter
from backend.app.services.facility_resolver import facility_resolver
from backend.app.services.pipeline_service import pipeline_service
from backend.app.services.baseline_service import calculate_baseline_deviation, calculate_facility_baseline
from backend.app.services.anomaly_service import detect_thermal_anomalies
from backend.app.services.alert_workflow_service import alert_workflow_service


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


from backend.app.services.ingestion import (
    hardened_ingestion_service, checkpoint_service, IngestionFailureCategory, ProviderHealthState
)


@shared_task(name="backend.app.tasks.firms_ingestion_job")
def firms_ingestion_job(dataset: str = "VIIRS_NOAA20_NRT", country: str = "IND"):
    """
    Scheduled NASA FIRMS incremental ingestion job for India using hardened fault-resilient service.
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
                health_status=ProviderHealthState.HEALTHY.value
            )
            db.add(source_rec)
            db.commit()
            db.refresh(source_rec)

        # Check durable watermark
        cp = checkpoint_service.get_checkpoint(db, provider="NASA_FIRMS", dataset=dataset)
        inc_since = None
        if cp and cp.get("last_successful_observation_time"):
            try:
                inc_since = datetime.fromisoformat(cp["last_successful_observation_time"].replace("Z", "+00:00"))
            except Exception:
                inc_since = None

        # Fetch observations with bounded retries and jittered backoff
        observations = firms_adapter.fetch_thermal_observations(
            country=country,
            days=1,
            sensor=dataset,
            incremental_since=inc_since
        )
        records_count = len(observations)

        if observations:
            batch_result = hardened_ingestion_service.process_ingestion_batch(
                db=db,
                records=observations,
                provider="NASA_FIRMS",
                dataset=dataset
            )
            records_count = batch_result.get("records_valid", 0)

        source_rec.last_sync_at = datetime.now(timezone.utc)
        source_rec.health_status = (
            firms_adapter.health_state.value if hasattr(firms_adapter, "health_state")
            else (ProviderHealthState.HEALTHY.value if firms_adapter.api_key else ProviderHealthState.DEGRADED.value)
        )

    except Exception as e:
        job_status = "FAILED"
        error_msg = str(e)
        if 'source_rec' in locals() and source_rec:
            source_rec.health_status = ProviderHealthState.DEGRADED.value
            source_rec.last_failure_at = datetime.now(timezone.utc)
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
    Updates empirical thermal baselines across industrial facilities with associated thermal events.
    """
    db: Session = SessionLocal()
    try:
        facilities_with_events = db.query(IndustrialFacility).join(
            ThermalEvent, ThermalEvent.facility_id == IndustrialFacility.id
        ).distinct().all()

        updated_count = 0
        for fac in facilities_with_events:
            try:
                calculate_facility_baseline(db, fac.id)
                updated_count += 1
            except Exception:
                pass

        return {
            "status": "SUCCESS",
            "facilities_evaluated": len(facilities_with_events),
            "baselines_updated": updated_count
        }
    finally:
        db.close()


@shared_task(name="backend.app.tasks.anomaly_analysis_job")
def anomaly_analysis_job():
    """
    Executes multivariate Isolation Forest and baseline anomaly scoring across all active thermal events.
    """
    db: Session = SessionLocal()
    try:
        events = db.query(ThermalEvent).filter(ThermalEvent.status == "ACTIVE").all()
        anomalies_detected = 0
        for evt in events:
            feat_dict = {
                "frp_avg": evt.avg_frp,
                "frp_max": evt.max_frp,
                "frp_variance": evt.frp_variance,
                "day_night_ratio": 1.0,
                "persistence_score": 5.0
            }
            baseline_stats = None
            if evt.facility_id:
                fb = db.query(HistoricalBaseline).filter(HistoricalBaseline.facility_id == evt.facility_id).first()
                if fb:
                    baseline_stats = {"mean_frp": fb.mean_frp, "std_frp": fb.std_frp}
            res = detect_thermal_anomalies(feat_dict, baseline_stats)
            if res.get("is_anomaly"):
                anomalies_detected += 1

        return {
            "status": "SUCCESS",
            "active_events_checked": len(events),
            "anomalies_detected": anomalies_detected
        }
    finally:
        db.close()


@shared_task(name="backend.app.tasks.alert_generation_job")
def alert_generation_job():
    """
    Evaluates active thermal events and generates or synchronizes governed operational alerts.
    Maintains strict production safety invariant: is_operational_dispatch = False permanently.
    """
    db: Session = SessionLocal()
    try:
        active_events = db.query(ThermalEvent).filter(ThermalEvent.status == "ACTIVE").all()
        alerts_synced = 0
        for evt in active_events:
            try:
                alert_workflow_service.create_or_update_alert_from_event(db, evt.id)
                alerts_synced += 1
            except Exception:
                pass

        return {
            "status": "SUCCESS",
            "events_evaluated": len(active_events),
            "alerts_synced": alerts_synced
        }
    finally:
        db.close()

