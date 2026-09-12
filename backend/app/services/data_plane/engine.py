"""
AGNI-NETRA JARVIS Phase 16: Unified Data-Plane Ingestion & Governance Engine
Coordinates the complete pipeline:
Acquisition -> Validation -> Normalization -> Quality Control -> Deduplication -> Provenance -> Storage / Quarantine -> Checkpointing -> Downstream Feeds.
Strictly provider-neutral, audit-safe, and without background loops.
"""

import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.models.domain import (
    IngestionBatchModel, IngestionRecordModel, IngestionQuarantineModel,
    DatasetRegistryModel, IngestionCheckpointModel
)
from backend.app.services.data_plane.models import (
    IngestionBatchStatus, IngestionMode, IngestionProcessingState,
    QualityStatus, DedupStatus, RecordLifecycleState
)
from backend.app.services.data_plane.normalization import normalization_engine
from backend.app.services.data_plane.validation import validation_engine
from backend.app.services.data_plane.quality_control import quality_control_engine
from backend.app.services.data_plane.deduplication import deduplication_engine
from backend.app.services.data_plane.quarantine import quarantine_manager
from backend.app.services.intelligence.provenance import SourceProvenance


class DataPlaneEngine:
    """
    Singleton Data-Plane Engine governing global ingestion jobs.
    """

    _instance: Optional["DataPlaneEngine"] = None

    def __new__(cls) -> "DataPlaneEngine":
        if cls._instance is None:
            cls._instance = super(DataPlaneEngine, cls).__new__(cls)
        return cls._instance

    def run_ingestion_batch(
        self,
        db: Session,
        provider: str,
        dataset: str,
        records: List[Dict[str, Any]],
        mode: IngestionMode = IngestionMode.INCREMENTAL,
        schema_version: str = "1.0.0",
        normalization_version: str = "1.0.0",
        country: str = "GLOBAL",
        jurisdiction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a deterministic ingestion batch across raw records.
        """
        batch_id = f"BATCH-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        started_at = datetime.now(timezone.utc)

        # 1. Initialize IngestionBatchModel
        batch_model = IngestionBatchModel(
            id=str(uuid.uuid4()),
            batch_id=batch_id,
            provider=provider.upper(),
            dataset=dataset.upper(),
            mode=mode.value if hasattr(mode, "value") else str(mode),
            started_at=started_at,
            records_received=len(records),
            schema_version=schema_version,
            normalization_version=normalization_version,
            status=IngestionBatchStatus.RUNNING.value
        )
        db.add(batch_model)
        db.flush()

        # Load recent records for deduplication check
        recent_records = (
            db.query(IngestionRecordModel)
            .filter(IngestionRecordModel.provider == provider.upper())
            .order_by(IngestionRecordModel.received_at.desc())
            .limit(1000)
            .all()
        )
        existing_dicts = [
            {
                "ingestion_id": r.ingestion_id,
                "provider": r.provider,
                "dataset": r.dataset,
                "source_record_id": r.source_record_id,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "observation_time": r.observation_time.isoformat() if r.observation_time else None
            }
            for r in recent_records
        ]

        accepted_count = 0
        rejected_count = 0
        quarantined_count = 0
        duplicated_count = 0
        failed_count = 0

        accepted_record_ids = []
        batch_hasher = hashlib.sha256()

        latest_obs_dt: Optional[datetime] = None
        last_src_id: Optional[str] = None

        for raw_item in records:
            # Ensure provider & dataset populated
            raw_item["provider"] = raw_item.get("provider") or provider.upper()
            raw_item["dataset"] = raw_item.get("dataset") or dataset.upper()

            # Hash into batch checksum
            batch_hasher.update(str(raw_item).encode("utf-8"))

            # Step 1: Raw Validation
            v_res = validation_engine.validate_record(raw_item)
            if not v_res.is_valid:
                if v_res.should_quarantine:
                    quarantined_count += 1
                    quarantine_manager.quarantine_record(
                        db=db,
                        provider=provider.upper(),
                        dataset=dataset.upper(),
                        source_record_id=raw_item.get("source_record_id"),
                        reason=v_res.error_message or "Validation failed",
                        error_code=v_res.error_code or "VALIDATION_FAILURE",
                        raw_payload=raw_item,
                        batch_id=batch_id
                    )
                else:
                    rejected_count += 1
                continue

            # Step 2: Normalization
            c_ok, norm_lat, norm_lon, c_err = normalization_engine.normalize_coordinates(
                raw_item.get("latitude"), raw_item.get("longitude")
            )
            t_ok, norm_dt, norm_iso, t_err = normalization_engine.normalize_timestamp(
                raw_item.get("observation_time") or raw_item.get("acq_timestamp"),
                raw_item.get("acq_date"),
                raw_item.get("acq_time")
            )
            g_ok, norm_geom, g_err = normalization_engine.normalize_geometry(
                raw_item.get("geometry"), norm_lat, norm_lon
            )

            # Step 3: Deduplication Evaluation
            candidate_dict = {
                "provider": provider.upper(),
                "dataset": dataset.upper(),
                "source_record_id": raw_item.get("source_record_id"),
                "latitude": norm_lat,
                "longitude": norm_lon,
                "observation_time": norm_iso
            }
            dedup_res = deduplication_engine.evaluate(candidate_dict, existing_dicts)
            is_dup = (dedup_res.status != DedupStatus.UNIQUE)
            if is_dup:
                duplicated_count += 1

            # Step 4: Quality Control
            qc_res = quality_control_engine.evaluate(
                record=candidate_dict,
                is_duplicate=is_dup,
                provenance_present=True,
                provider_known=True
            )

            # Step 5: Construct Canonical Provenance Lineage
            ingestion_id = f"ING-{uuid.uuid4().hex[:8].upper()}"
            src_prov = SourceProvenance(
                provider=provider.upper(),
                dataset=dataset.upper(),
                source_record_id=raw_item.get("source_record_id"),
                observation_time=norm_iso,
                geographic_coverage=country,
                spatial_resolution=raw_item.get("spatial_resolution", "375m"),
                source_type=raw_item.get("source_type", "REAL_PROVIDER"),
                evidence_nature="OBSERVED",
                quality="HIGH" if qc_res.status == QualityStatus.PASS else "MEDIUM",
                latitude=norm_lat,
                longitude=norm_lon,
                ingestion_batch_id=batch_id,
                normalization_version=normalization_version,
                schema_version=schema_version,
                calibration_status="OPERATIONAL_CALIBRATED",
                transformation_lineage=[
                    f"SOURCE:{provider.upper()}",
                    "RAW_RECORD",
                    f"NORMALIZED:{normalization_version}",
                    f"DEDUP:{dedup_res.status.value}",
                    "STORED"
                ]
            )

            # Step 6: Persist Canonical Ingestion Record
            rec_model = IngestionRecordModel(
                id=str(uuid.uuid4()),
                ingestion_id=ingestion_id,
                batch_id=batch_id,
                provider=provider.upper(),
                dataset=dataset.upper(),
                source_record_id=raw_item.get("source_record_id"),
                received_at=datetime.now(timezone.utc),
                observation_time=norm_dt,
                country=raw_item.get("country") or country,
                jurisdiction=raw_item.get("jurisdiction") or jurisdiction,
                latitude=norm_lat,
                longitude=norm_lon,
                geometry=norm_geom,
                schema_version=schema_version,
                source_type=raw_item.get("source_type", "REAL_PROVIDER"),
                quality_status=qc_res.status.value,
                quality_reasons=qc_res.reasons,
                dedup_status=dedup_res.status.value,
                duplicate_of_id=dedup_res.matched_record_id,
                provenance_id=src_prov.source_record_id or ingestion_id,
                processing_status=IngestionProcessingState.STORED.value,
                lifecycle_state=RecordLifecycleState.ORIGINAL.value,
                raw_payload=raw_item,
                normalized_payload={
                    "normalized_lat": norm_lat,
                    "normalized_lon": norm_lon,
                    "observation_time_iso": norm_iso,
                    "frp_mw": normalization_engine.normalize_unit("frp", raw_item.get("frp")),
                    "provenance": src_prov.model_dump()
                }
            )
            db.add(rec_model)
            accepted_count += 1
            accepted_record_ids.append(ingestion_id)

            # Update track variables for checkpoint
            if norm_dt and (latest_obs_dt is None or norm_dt > latest_obs_dt):
                latest_obs_dt = norm_dt
            if raw_item.get("source_record_id"):
                last_src_id = str(raw_item.get("source_record_id"))

            # Keep in-memory cache for subsequent batch deduplication
            existing_dicts.append(candidate_dict)

        completed_at = datetime.now(timezone.utc)
        batch_checksum = batch_hasher.hexdigest()

        # Update batch model
        batch_model.completed_at = completed_at
        batch_model.records_accepted = accepted_count
        batch_model.records_rejected = rejected_count
        batch_model.records_quarantined = quarantined_count
        batch_model.records_duplicated = duplicated_count
        batch_model.records_failed = failed_count
        batch_model.checksum = batch_checksum
        batch_model.status = (
            IngestionBatchStatus.COMPLETED.value
            if (rejected_count == 0 and quarantined_count == 0)
            else (IngestionBatchStatus.PARTIAL.value if accepted_count > 0 else IngestionBatchStatus.FAILED.value)
        )

        # 7. Update Dataset Registry Metadata & Freshness
        ds_reg = db.query(DatasetRegistryModel).filter(DatasetRegistryModel.dataset_id == dataset.upper()).first()
        if ds_reg:
            ds_reg.last_ingestion_time = completed_at
            if latest_obs_dt:
                ds_reg.last_observation_time = latest_obs_dt
            ds_reg.record_count = (ds_reg.record_count or 0) + accepted_count

        # 8. Update Ingestion Checkpoint
        cp_key = f"{provider.upper()}:{dataset.upper()}"
        checkpoint = db.query(IngestionCheckpointModel).filter(IngestionCheckpointModel.checkpoint_key == cp_key).first()
        if not checkpoint:
            checkpoint = IngestionCheckpointModel(
                id=str(uuid.uuid4()),
                checkpoint_key=cp_key,
                provider=provider.upper(),
                dataset=dataset.upper(),
                last_successful_observation_time=latest_obs_dt,
                last_successful_source_record_id=last_src_id,
                last_successful_batch_id=batch_id,
                updated_at=completed_at
            )
            db.add(checkpoint)
        else:
            if latest_obs_dt:
                checkpoint.last_successful_observation_time = latest_obs_dt
            if last_src_id:
                checkpoint.last_successful_source_record_id = last_src_id
            checkpoint.last_successful_batch_id = batch_id
            checkpoint.updated_at = completed_at

        db.commit()

        return {
            "batch_id": batch_id,
            "provider": provider.upper(),
            "dataset": dataset.upper(),
            "status": batch_model.status,
            "records_received": len(records),
            "records_accepted": accepted_count,
            "records_rejected": rejected_count,
            "records_quarantined": quarantined_count,
            "records_duplicated": duplicated_count,
            "checksum": batch_checksum,
            "accepted_record_ids": accepted_record_ids[:10],
            "checkpoint_updated": cp_key
        }

    def create_batch(
        self,
        db: Session,
        provider: str,
        dataset: str,
        mode: IngestionMode = IngestionMode.INITIAL_LOAD,
        schema_version: str = "1.0.0",
        normalization_version: str = "1.0.0"
    ) -> IngestionBatchModel:
        """Initializes a new ingestion batch."""
        batch_id = f"BATCH-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        batch = IngestionBatchModel(
            id=str(uuid.uuid4()),
            batch_id=batch_id,
            provider=provider.upper(),
            dataset=dataset.upper(),
            mode=mode.value if hasattr(mode, "value") else str(mode),
            started_at=datetime.now(timezone.utc),
            schema_version=schema_version,
            normalization_version=normalization_version,
            status=IngestionBatchStatus.RUNNING.value
        )
        db.add(batch)
        db.commit()
        return batch

    def save_checkpoint(
        self,
        db: Session,
        provider: str,
        dataset: str,
        checkpoint_value: str,
        records_ingested: int = 0
    ) -> IngestionCheckpointModel:
        """Creates or updates an ingestion checkpoint."""
        cp_key = f"{provider.upper()}:{dataset.upper()}"
        checkpoint = db.query(IngestionCheckpointModel).filter(IngestionCheckpointModel.checkpoint_key == cp_key).first()
        now_utc = datetime.now(timezone.utc)
        if not checkpoint:
            checkpoint = IngestionCheckpointModel(
                id=str(uuid.uuid4()),
                checkpoint_key=cp_key,
                provider=provider.upper(),
                dataset=dataset.upper(),
                last_successful_source_record_id=checkpoint_value,
                updated_at=now_utc
            )
            db.add(checkpoint)
        else:
            checkpoint.last_successful_source_record_id = checkpoint_value
            checkpoint.updated_at = now_utc
        db.commit()
        return checkpoint

    def get_checkpoint(
        self,
        db: Session,
        provider: str,
        dataset: str
    ) -> Optional[str]:
        """Retrieves checkpoint value for provider and dataset."""
        cp_key = f"{provider.upper()}:{dataset.upper()}"
        checkpoint = db.query(IngestionCheckpointModel).filter(IngestionCheckpointModel.checkpoint_key == cp_key).first()
        if checkpoint:
            return checkpoint.last_successful_source_record_id or (checkpoint.last_successful_observation_time.isoformat() if checkpoint.last_successful_observation_time else None)
        return None

    def get_provider_summary(self, db: Optional[Session] = None) -> Dict[str, Any]:
        """Returns factual availability and metadata for all governed providers."""
        return {
            "NASA_FIRMS": {
                "name": "NASA FIRMS Telemetry",
                "operational_status": "OPERATIONAL",
                "coverage_scope": "GLOBAL",
                "reliability_tier": "TIER_1",
                "sensor_types": ["VIIRS", "MODIS"],
                "spatial_resolution": "375m / 1km"
            },
            "ECMWF_ERA5": {
                "name": "ECMWF ERA5 Atmospheric Reanalysis",
                "operational_status": "NOT_CONFIGURED",
                "coverage_scope": "GLOBAL",
                "reliability_tier": "TIER_1",
                "sensor_types": ["Numerical Reanalysis"],
                "spatial_resolution": "0.25 deg (~31km)"
            },
            "NOAA_GFS": {
                "name": "NOAA GFS Weather Forecasts",
                "operational_status": "NOT_CONFIGURED",
                "coverage_scope": "GLOBAL",
                "reliability_tier": "TIER_2",
                "sensor_types": ["Numerical Weather Prediction"],
                "spatial_resolution": "0.25 deg"
            },
            "COPERNICUS_CAMS": {
                "name": "Copernicus CAMS Atmospheric Composition",
                "operational_status": "NOT_CONFIGURED",
                "coverage_scope": "GLOBAL",
                "reliability_tier": "TIER_2",
                "sensor_types": ["Atmospheric Model"],
                "spatial_resolution": "0.4 deg"
            },
            "ESA_SENTINEL_2": {
                "name": "ESA Sentinel-2 Multi-Spectral Optical",
                "operational_status": "NOT_CONFIGURED",
                "coverage_scope": "GLOBAL",
                "reliability_tier": "TIER_1",
                "sensor_types": ["MSI Optical"],
                "spatial_resolution": "10m / 20m / 60m"
            },
            "ESA_SENTINEL_1": {
                "name": "ESA Sentinel-1 C-Band SAR",
                "operational_status": "NOT_CONFIGURED",
                "coverage_scope": "GLOBAL",
                "reliability_tier": "TIER_1",
                "sensor_types": ["C-Band SAR Radar"],
                "spatial_resolution": "5m x 20m"
            },
            "PLANET_WORLDVIEW": {
                "name": "PlanetScope / WorldView Optical",
                "operational_status": "NOT_CONFIGURED",
                "coverage_scope": "GLOBAL",
                "reliability_tier": "TIER_3",
                "sensor_types": ["Ultra-High-Resolution Optical"],
                "spatial_resolution": "0.3m - 3m"
            }
        }


data_plane_engine = DataPlaneEngine()
