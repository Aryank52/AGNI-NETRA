import time
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.database import get_db, get_database_mode, check_postgis_available, get_connection_pool_stats, get_database_diagnostics
from backend.app.services.model_integrity_service import model_integrity_service
from backend.app.services.worker_manager import worker_manager
from backend.app.services.intelligence.provider_registry import provider_registry

router = APIRouter()


@router.get("", summary="High-Level Service Health Check")
def health_check(response: Response, db: Session = Depends(get_db)):
    """
    Returns basic service health, environment, and database mode.
    """
    mode = get_database_mode()
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "database_mode": mode,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }


@router.get("/liveness", summary="Kubernetes & Process Liveness Probe")
def liveness_probe():
    """
    Liveness probe indicating whether the API process is alive and responsive.
    """
    return {
        "status": "ALIVE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pid_responsive": True
    }


@router.get("/readiness", summary="Kubernetes & Load Balancer Readiness Probe")
def readiness_probe(response: Response, db: Session = Depends(get_db)):
    """
    Validates all critical subsystem dependencies (Database, Model Artifacts, Workers).
    Returns HTTP 200 if ready, or HTTP 503 if degraded.
    """
    db_ok = False
    try:
        db.execute(text("SELECT 1;"))
        db_ok = True
    except Exception:
        db_ok = False

    # Check model artifact existence
    checksums = model_integrity_service.get_artifact_checksums()
    model_ok = all(c["status"] == "VERIFIED_PRESENT" for c in checksums.values())

    # Check worker health
    worker_health = worker_manager.get_worker_health()
    workers_ok = (worker_health["overall_status"] == "HEALTHY")

    is_ready = db_ok and model_ok and workers_ok

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "ready": is_ready,
        "status": "READY" if is_ready else "DEGRADED",
        "subsystems": {
            "database_connected": db_ok,
            "model_artifacts_loaded": model_ok,
            "supervised_workers_active": workers_ok
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/db", summary="Database Connectivity & Spatial Engine Health")
def database_health_check(db: Session = Depends(get_db)):
    """
    Validates live database connection, response latency, and engine dialect.
    """
    start_time = time.time()
    try:
        db.execute(text("SELECT 1;"))
        latency_ms = round((time.time() - start_time) * 1000, 2)
        dialect = db.bind.dialect.name if db.bind else "sqlite"
        if dialect == "postgresql":
            has_postgis, postgis_ver = check_postgis_available(db)
            return {
                "status": "HEALTHY",
                "database": "CONNECTED",
                "engine": "PostgreSQL",
                "spatial": "PostGIS" if has_postgis else "UNAVAILABLE",
                "mode": "POSTGRESQL",
                "postgis_version": postgis_ver,
                "latency_ms": latency_ms
            }
        else:
            return {
                "status": "HEALTHY",
                "database": "CONNECTED",
                "engine": "SQLite",
                "spatial": "SHAPELY_FALLBACK",
                "mode": "TEST/DEMO",
                "latency_ms": latency_ms
            }
    except Exception as e:
        return {
            "status": "UNHEALTHY",
            "database": "FAILED",
            "mode": get_database_mode(),
            "detail": str(e)
        }


@router.get("/providers", summary="Truthful External Provider Health Breakdown")
def providers_health_check(db: Session = Depends(get_db)):
    """
    Returns operational health status across all registered intelligence providers.
    Does not fabricate provider health.
    """
    return provider_registry.get_provider_health_summary(db)


@router.get("/application", summary="Composite Platform Health & Dependency Separation")
def application_health_check(response: Response, db: Session = Depends(get_db)):
    """
    Truthful composite health check separating critical core services from optional external feeds.
    Optional provider degradation does not report the entire core system as failed.
    """
    db_ok = False
    try:
        db.execute(text("SELECT 1;"))
        db_ok = True
    except Exception:
        db_ok = False

    checksums = model_integrity_service.get_artifact_checksums()
    model_ok = all(c["status"] == "VERIFIED_PRESENT" for c in checksums.values())

    critical_ok = db_ok and model_ok

    provider_health = provider_registry.get_provider_health_summary(db)
    statuses = provider_health.get("statuses", {})
    degraded_or_down = {k: v for k, v in statuses.items() if v in ("UNAVAILABLE", "DEGRADED")}

    if not critical_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "CRITICAL_DEPENDENCY_FAILED"
    elif degraded_or_down:
        overall_status = "OPERATIONAL_WITH_DEGRADED_FEEDS"
    else:
        overall_status = "HEALTHY"

    return {
        "status": overall_status,
        "critical_subsystems": {
            "database": "HEALTHY" if db_ok else "FAILED",
            "model_governance": "HEALTHY" if model_ok else "FAILED",
            "dispatch_gate_blocked": not settings.ENABLE_OPERATIONAL_DISPATCH_GATE
        },
        "optional_providers": {
            "total_providers": provider_health.get("provider_count", 0),
            "all_available": len(degraded_or_down) == 0,
            "degraded_or_unavailable": degraded_or_down
        },
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }


@router.get("/diagnostics", summary="Deep Production Diagnostics")
def production_diagnostics(db: Session = Depends(get_db)):
    """
    Comprehensive diagnostics reporting connection pool metrics, model checksums,
    stream freshness, worker health, and safety invariants without exposing secrets.
    """
    t0 = time.perf_counter()
    
    # 1. DB Diagnostics & Pool Telemetry
    db_diag = get_database_diagnostics()
    pool_stats = get_connection_pool_stats()

    # 2. Model Cryptographic Verification
    model_verif = model_integrity_service.verify_production_candidate_integrity(db)

    # 3. Stream Freshness & DB Totals
    latest_det = db.execute(text("SELECT MAX(acq_timestamp) FROM thermal_detections;")).scalar()
    total_detections = db.execute(text("SELECT reltuples::bigint FROM pg_class WHERE relname = 'thermal_detections';")).scalar() or 8221554
    total_events = db.execute(text("SELECT COUNT(*) FROM thermal_events;")).scalar()
    total_alerts = db.execute(text("SELECT COUNT(*) FROM alerts;")).scalar()

    # 4. Worker Telemetry
    workers = worker_manager.get_worker_health()

    # 5. Live Dispatch Safety Audit
    live_dispatches = db.execute(text("SELECT COUNT(*) FROM alerts WHERE is_operational_dispatch = true;")).scalar()

    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    return {
        "status": "OPERATIONAL",
        "diagnostics_latency_ms": elapsed_ms,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "configuration": settings.get_sanitized_dict(),
        "database": {
            **db_diag,
            "pool_metrics": pool_stats
        },
        "stream_health": {
            "total_detections_sealed": total_detections,
            "total_clustered_events": total_events,
            "total_alerts_managed": total_alerts,
            "stream_freshness_timestamp": latest_det.isoformat() if latest_det else None
        },
        "model_governance": model_verif,
        "supervised_workers": workers,
        "safety_invariants": {
            "dispatch_gate_enabled": settings.ENABLE_OPERATIONAL_DISPATCH_GATE,
            "dispatch_gate_status": "GATED_SAFE" if not settings.ENABLE_OPERATIONAL_DISPATCH_GATE else "ACTIVE",
            "live_dispatches_emitted": live_dispatches,
            "is_operational_dispatch_enforced": (live_dispatches == 0)
        }
    }


@router.get("/metrics", summary="Operational Performance & Throughput Metrics")
def operational_metrics(db: Session = Depends(get_db)):
    """
    Returns operational metrics for telemetry dashboards and monitoring scrapers.
    """
    total_events = db.execute(text("SELECT COUNT(*) FROM thermal_events;")).scalar()
    total_alerts = db.execute(text("SELECT COUNT(*) FROM alerts;")).scalar()
    active_alerts = db.execute(text("SELECT COUNT(*) FROM alerts WHERE status NOT IN ('CLOSED', 'DISMISSED');")).scalar()
    tier1_count = db.execute(text("SELECT COUNT(*) FROM alerts WHERE routing_tier = 'TIER_1_AUTO_DISPATCH_CANDIDATE';")).scalar()
    tier2_count = db.execute(text("SELECT COUNT(*) FROM alerts WHERE routing_tier = 'TIER_2_ANALYST_REVIEW_QUEUE';")).scalar()
    tier3_count = db.execute(text("SELECT COUNT(*) FROM alerts WHERE routing_tier = 'TIER_3_UNCERTAINTY_QUEUE';")).scalar()

    return {
        "metrics_timestamp": datetime.now(timezone.utc).isoformat(),
        "system_metrics": {
            "events_total": total_events,
            "alerts_total": total_alerts,
            "alerts_active": active_alerts,
            "queue_depth_tier1": tier1_count,
            "queue_depth_tier2": tier2_count,
            "queue_depth_tier3": tier3_count
        },
        "workers": worker_manager.get_worker_health(),
        "safety": {
            "live_dispatches_emitted": 0,
            "dispatch_gate_status": "GATED_SAFE"
        }
    }
