"""
AGNI-NETRA JARVIS Phase 16: Data Ingestion & Governance API Endpoints
Provides read-only observational data-governance visibility, batch tracking,
quarantine inspection, and provenance lookup.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.core.database import get_db
from backend.app.api.deps import get_optional_current_user, require_analyst, require_admin
from backend.app.models.domain import (
    User, IngestionBatchModel, IngestionRecordModel, IngestionQuarantineModel,
    DatasetRegistryModel, IngestionCheckpointModel
)
from backend.app.services.intelligence.provider_registry import provider_registry
from backend.app.services.data_plane.freshness import freshness_engine
from backend.app.services.data_plane.coverage import coverage_compiler
from backend.app.services.data_plane.quarantine import quarantine_manager
from backend.app.services.data_plane.engine import data_plane_engine
from backend.app.services.data_plane.live_provider_service import live_provider_service
from backend.app.services.data_plane.models import IngestionMode

router = APIRouter()


class RunBatchRequest(BaseModel):
    provider: str = Field(..., description="Provider identifier (e.g. NASA_FIRMS)")
    dataset: str = Field(..., description="Dataset identifier (e.g. NASA_FIRMS_VIIRS_NRT)")
    records: List[Dict[str, Any]] = Field(default_factory=list, description="Raw observations payload")
    mode: str = Field("INCREMENTAL", description="INITIAL_LOAD, INCREMENTAL, REPLAY, BACKFILL")
    country: str = Field("GLOBAL", description="Country or scope")
    jurisdiction: Optional[str] = Field(None)


@router.get("/providers")
def get_data_providers(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> Dict[str, Any]:
    """
    Returns registered intelligence providers with truthful availability, coverage, and capabilities.
    """
    role = current_user.role if current_user else "PUBLIC"
    providers = provider_registry.list_providers(role=role)
    health_summary = provider_registry.get_provider_health_summary(db)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_providers": len(providers),
        "health_summary": health_summary,
        "providers": providers
    }


@router.get("/datasets")
def get_governed_datasets(
    db: Session = Depends(get_db),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    coverage_scope: Optional[str] = Query(None, description="Filter by coverage scope: GLOBAL, REGIONAL, NATIONAL, PARTIAL, NOT_CONFIGURED")
) -> List[Dict[str, Any]]:
    """
    Lists registered intelligence datasets from governed_dataset_registry with official licenses and resolution.
    """
    query = db.query(DatasetRegistryModel)
    if provider:
        query = query.filter(DatasetRegistryModel.provider == provider.upper())
    if coverage_scope:
        query = query.filter(DatasetRegistryModel.coverage_scope == coverage_scope.upper())
    datasets = query.order_by(DatasetRegistryModel.provider, DatasetRegistryModel.name).all()
    return [
        {
            "dataset_id": d.dataset_id,
            "provider": d.provider,
            "name": d.name,
            "version": d.version,
            "license_reference": d.license_reference,
            "coverage_scope": d.coverage_scope,
            "country": d.country,
            "spatial_resolution": d.spatial_resolution,
            "temporal_resolution": d.temporal_resolution,
            "retention_policy": d.retention_policy,
            "schema_version": d.schema_version,
            "quality_policy": d.quality_policy,
            "provenance_policy": d.provenance_policy,
            "status": d.status,
            "freshness_threshold_seconds": d.freshness_threshold_seconds,
            "last_observation_time": d.last_observation_time.isoformat() if d.last_observation_time else None,
            "last_ingestion_time": d.last_ingestion_time.isoformat() if d.last_ingestion_time else None,
            "record_count": d.record_count or 0,
            "metadata_info": d.metadata_info or {}
        }
        for d in datasets
    ]


@router.get("/coverage")
def get_data_coverage(
    db: Session = Depends(get_db),
    region: Optional[str] = Query("GLOBAL", description="Target region (e.g. GLOBAL, INDIA)")
) -> Dict[str, Any]:
    """
    Returns compiled multi-tier coverage analysis distinguishing global capabilities from regional profiles.
    """
    return coverage_compiler.get_coverage_report(db=db, target_region=region)


@router.get("/ingestion/status")
def get_ingestion_status(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns real-time data-plane ingestion telemetry, latest batches, and failure indicators.
    """
    total_batches = db.query(IngestionBatchModel).count()
    last_batch = db.query(IngestionBatchModel).order_by(IngestionBatchModel.started_at.desc()).first()
    last_success = (
        db.query(IngestionBatchModel)
        .filter(IngestionBatchModel.status == "COMPLETED")
        .order_by(IngestionBatchModel.completed_at.desc())
        .first()
    )
    last_failure = (
        db.query(IngestionBatchModel)
        .filter(IngestionBatchModel.status == "FAILED")
        .order_by(IngestionBatchModel.started_at.desc())
        .first()
    )
    total_quarantined = db.query(IngestionQuarantineModel).count()
    total_records = db.query(IngestionRecordModel).count()

    return {
        "status": "INGESTION_IDLE" if (not last_batch or last_batch.status != "RUNNING") else "INGESTION_RUNNING",
        "total_batches": total_batches,
        "total_records_ingested": total_records,
        "total_records_quarantined": total_quarantined,
        "latest_batch": {
            "batch_id": last_batch.batch_id if last_batch else None,
            "provider": last_batch.provider if last_batch else None,
            "dataset": last_batch.dataset if last_batch else None,
            "status": last_batch.status if last_batch else None,
            "started_at": last_batch.started_at.isoformat() if last_batch and last_batch.started_at else None,
            "completed_at": last_batch.completed_at.isoformat() if last_batch and last_batch.completed_at else None,
            "records_received": last_batch.records_received if last_batch else 0,
            "records_accepted": last_batch.records_accepted if last_batch else 0,
            "records_quarantined": last_batch.records_quarantined if last_batch else 0
        } if last_batch else None,
        "last_successful_batch": {
            "batch_id": last_success.batch_id,
            "completed_at": last_success.completed_at.isoformat() if last_success.completed_at else None
        } if last_success else None,
        "last_failed_batch": {
            "batch_id": last_failure.batch_id,
            "started_at": last_failure.started_at.isoformat() if last_failure.started_at else None,
            "error": last_failure.error_message
        } if last_failure else None
    }


@router.get("/ingestion/batches")
def list_ingestion_batches(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    provider: Optional[str] = Query(None)
) -> List[Dict[str, Any]]:
    """
    Returns execution history of recent ingestion batches with throughput metrics.
    """
    query = db.query(IngestionBatchModel)
    if provider:
        query = query.filter(IngestionBatchModel.provider == provider.upper())
    batches = query.order_by(IngestionBatchModel.started_at.desc()).limit(limit).all()
    return [
        {
            "batch_id": b.batch_id,
            "provider": b.provider,
            "dataset": b.dataset,
            "mode": b.mode,
            "started_at": b.started_at.isoformat() if b.started_at else None,
            "completed_at": b.completed_at.isoformat() if b.completed_at else None,
            "records_received": b.records_received,
            "records_accepted": b.records_accepted,
            "records_rejected": b.records_rejected,
            "records_quarantined": b.records_quarantined,
            "records_duplicated": b.records_duplicated,
            "checksum": b.checksum,
            "status": b.status,
            "error_message": b.error_message
        }
        for b in batches
    ]


@router.get("/ingestion/batches/{batch_id}")
def get_batch_details(
    batch_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retrieves full execution audit and checksum for a specific ingestion batch.
    """
    batch = db.query(IngestionBatchModel).filter(IngestionBatchModel.batch_id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail=f"Ingestion batch '{batch_id}' not found")

    sample_records = (
        db.query(IngestionRecordModel)
        .filter(IngestionRecordModel.batch_id == batch_id)
        .limit(10)
        .all()
    )

    return {
        "batch_id": batch.batch_id,
        "provider": batch.provider,
        "dataset": batch.dataset,
        "mode": batch.mode,
        "started_at": batch.started_at.isoformat() if batch.started_at else None,
        "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
        "records_received": batch.records_received,
        "records_accepted": batch.records_accepted,
        "records_rejected": batch.records_rejected,
        "records_quarantined": batch.records_quarantined,
        "records_duplicated": batch.records_duplicated,
        "schema_version": batch.schema_version,
        "normalization_version": batch.normalization_version,
        "checksum": batch.checksum,
        "status": batch.status,
        "error_message": batch.error_message,
        "sample_records": [
            {
                "ingestion_id": r.ingestion_id,
                "source_record_id": r.source_record_id,
                "observation_time": r.observation_time.isoformat() if r.observation_time else None,
                "quality_status": r.quality_status,
                "dedup_status": r.dedup_status
            }
            for r in sample_records
        ]
    }


@router.get("/freshness")
def get_data_freshness(
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Evaluates dataset-level observation age and SLA freshness status.
    """
    return freshness_engine.get_all_datasets_freshness(db)


@router.get("/quarantine")
def get_quarantined_records(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    provider: Optional[str] = Query(None)
) -> List[Dict[str, Any]]:
    """
    Returns quarantined records with sanitized inspection snippets.
    """
    return quarantine_manager.list_quarantined(db, limit=limit, provider=provider)


@router.get("/provenance/{source_record_id}")
def get_observation_provenance(
    source_record_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Looks up full ingestion provenance, transformation lineage, and batch association by source_record_id.
    """
    rec = (
        db.query(IngestionRecordModel)
        .filter(IngestionRecordModel.source_record_id == source_record_id)
        .order_by(IngestionRecordModel.received_at.desc())
        .first()
    )
    if not rec:
        # Fallback: check if source_record_id was actually an ingestion_id
        rec = db.query(IngestionRecordModel).filter(IngestionRecordModel.ingestion_id == source_record_id).first()

    if not rec:
        raise HTTPException(status_code=404, detail=f"No provenance record found for identifier '{source_record_id}'")

    payload_norm = rec.normalized_payload or {}
    prov_dict = payload_norm.get("provenance", {})

    return {
        "source_record_id": rec.source_record_id,
        "ingestion_id": rec.ingestion_id,
        "batch_id": rec.batch_id,
        "provider": rec.provider,
        "dataset": rec.dataset,
        "received_at": rec.received_at.isoformat() if rec.received_at else None,
        "observation_time": rec.observation_time.isoformat() if rec.observation_time else None,
        "quality_status": rec.quality_status,
        "quality_reasons": rec.quality_reasons,
        "dedup_status": rec.dedup_status,
        "lifecycle_state": rec.lifecycle_state,
        "provenance": prov_dict,
        "transformation_lineage": prov_dict.get("transformation_lineage", [
            f"SOURCE:{rec.provider}",
            "RAW_RECORD",
            f"NORMALIZED:{rec.schema_version}",
            f"DEDUP:{rec.dedup_status}",
            "STORED"
        ])
    }


@router.post("/ingestion/run-batch")
def trigger_manual_batch(
    req: RunBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
) -> Dict[str, Any]:
    """
    RBAC-governed endpoint allowing authenticated analysts to execute a controlled ingestion batch.
    """
    if not req.records:
        raise HTTPException(status_code=400, detail="No observations provided in payload")

    mode_enum = IngestionMode(req.mode.upper()) if req.mode.upper() in IngestionMode.__members__ else IngestionMode.INCREMENTAL

    res = data_plane_engine.run_ingestion_batch(
        db=db,
        provider=req.provider,
        dataset=req.dataset,
        records=req.records,
        mode=mode_enum,
        country=req.country,
        jurisdiction=req.jurisdiction
    )
    return res


# =============================================================================
# PHASE 17: LIVE DATA PROVIDER ACTIVATION ENDPOINTS (Section 23)
# =============================================================================

@router.get("/providers/live-status")
def get_live_providers_status(
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Returns verified live capability status across all 7 upstream providers:
    NASA_FIRMS, ISRO_BHUVAN, CEA_REGISTRY, IBM_PORTAL, MOEFCC_PARIVESH,
    COPERNICUS, COMMERCIAL_OPTICAL_SAR.
    Strictly adheres to the 9 Provider Availability Rules.
    """
    capabilities = live_provider_service.audit_all_providers(db)
    return [c.model_dump() for c in capabilities]


@router.get("/providers/{provider}/status")
def get_single_provider_status(
    provider: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns detailed capability status and reachability diagnostics for a specific provider.
    """
    capabilities = live_provider_service.audit_all_providers(db)
    match = [c for c in capabilities if c.provider.upper() == provider.upper()]
    if not match:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider}' not found in governed registry."
        )
    return match[0].model_dump()


@router.get("/providers/{provider}/sample")
@router.post("/providers/{provider}/sample")
def get_live_provider_sample(
    provider: str,
    dataset: str = Query("VIIRS_SNPP_NRT", description="Sensor/product dataset"),
    limit: int = Query(20, ge=1, le=50, description="Bounded sample limit (max 50)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
) -> Dict[str, Any]:
    """
    RBAC-governed endpoint allowing authenticated analysts to execute an on-demand
    bounded live retrieval from an active external provider through the Phase 16 Data-Plane.
    """
    result = live_provider_service.retrieve_and_ingest_live_sample(
        db=db,
        provider=provider,
        dataset=dataset,
        limit=limit
    )
    return result


@router.get("/live/latest")
def get_latest_live_observations(
    limit: int = Query(20, ge=1, le=100, description="Maximum observations to return"),
    provider: Optional[str] = Query(None, description="Optional provider filter"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Returns latest successfully ingested real-time live observations (data_tier='LIVE').
    Clearly distinguished from historical archives, backfill, or simulation data.
    """
    query = (
        db.query(IngestionRecordModel)
        .filter(IngestionRecordModel.source_type == "LIVE")
    )
    if provider:
        query = query.filter(IngestionRecordModel.provider == provider.upper())

    records = query.order_by(IngestionRecordModel.observation_time.desc()).limit(limit).all()

    results = []
    for r in records:
        norm = r.normalized_payload or {}
        results.append({
            "source_record_id": r.source_record_id,
            "ingestion_id": r.ingestion_id,
            "provider": r.provider,
            "dataset": r.dataset,
            "source_type": r.source_type,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "observation_time": r.observation_time.isoformat() if r.observation_time else None,
            "temperature_kelvin": norm.get("temperature"),
            "frp_megawatts": norm.get("frp"),
            "confidence": norm.get("confidence"),
            "day_night": norm.get("day_night"),
            "satellite": norm.get("satellite"),
            "sensor": norm.get("sensor"),
            "quality_status": r.quality_status,
            "dedup_status": r.dedup_status,
            "batch_id": r.batch_id
        })
    return results


@router.get("/live/freshness")
def get_live_stream_freshness(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Calculates observation-time freshness for live feeds against SLA limits.
    """
    return live_provider_service.get_live_freshness(db)


@router.get("/live/coverage")
def get_live_stream_coverage(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns actual observed spatial and temporal extent computed from real live records.
    """
    return live_provider_service.get_live_coverage(db)


@router.get("/live/provenance/{source_record_id}")
def get_live_record_provenance(
    source_record_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns the complete end-to-end lineage for a live observation record.
    """
    prov = live_provider_service.get_live_provenance(db, source_record_id)
    if not prov:
        raise HTTPException(
            status_code=404,
            detail=f"Live provenance record not found for '{source_record_id}'."
        )
    return prov

