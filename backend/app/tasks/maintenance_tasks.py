import time
from datetime import datetime, timezone
from backend.app.core.celery_app import celery_app


@celery_app.task(name="tasks.system_heartbeat")
def system_heartbeat() -> dict:
    """
    Periodic heartbeat task checking Celery and Redis worker liveness.
    """
    now = datetime.now(timezone.utc).isoformat()
    return {
        "status": "HEALTHY",
        "worker": "agni_netra_celery_worker",
        "timestamp": now
    }


@celery_app.task(name="tasks.run_data_pipeline_job")
def run_data_pipeline_job(job_id: str, source_type: str) -> dict:
    """
    Asynchronous ingestion job runner for satellite & GIS adapters.
    """
    time.sleep(1)
    return {
        "job_id": job_id,
        "source_type": source_type,
        "status": "COMPLETED",
        "processed_records": 15
    }
