"""
AGNI-NETRA — WP3 Unified Hardened Ingestion Engine
Coordinates real external-data ingestion with:
- Structured failure classification and provider health monitoring
- Deterministic SHA-256 idempotency & duplicate suppression
- Durable checkpoint watermark tracking
- Dead-letter quarantine capture (zero silent loss)
- Atomic partial batch resilience
- Seamless bridging to WP1 Proactive Intelligence Core & JARVIS Observer
"""

import time
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.models.domain import (
    DataSource, IngestionBatchModel, IngestionRecordModel,
    ThermalDetection, ThermalEvent
)
from backend.app.services.ingestion.failure_taxonomy import (
    IngestionFailureCategory, ProviderHealthState, IngestionException,
    sanitize_error_message
)
from backend.app.services.ingestion.idempotency_service import (
    compute_deterministic_fingerprint, idempotency_service
)
from backend.app.services.ingestion.checkpoint_service import checkpoint_service
from backend.app.services.ingestion.dead_letter_service import dead_letter_service
from backend.app.services.pipeline_service import pipeline_service
from data_pipeline.adapters.base import NormalizedThermalObservation

logger = logging.getLogger("agni_netra.ingestion_service")

# Geodetic limits for Indian sovereign territory & territorial waters
INDIA_LAT_MIN, INDIA_LAT_MAX = 6.0, 38.0
INDIA_LON_MIN, INDIA_LON_MAX = 68.0, 98.0


class HardenedIngestionService:
    """
    Production ingestion orchestrator fulfilling WP3 resilience and fault-tolerance requirements.
    """

    def __init__(self):
        self.default_source = "NASA_FIRMS"
        self.default_dataset = "VIIRS_NOAA20_NRT"

    def validate_observation(
        self,
        record: Dict[str, Any],
        db: Optional[Session] = None
    ) -> Tuple[bool, Optional[IngestionFailureCategory], Optional[str]]:
        """
        Validates telemetry physics, coordinate envelope, mandatory identity fields,
        and authoritative sovereign India boundary containment.
        """
        # 1. Mandatory Coordinates & Timestamp
        if "latitude" not in record or "longitude" not in record:
            return False, IngestionFailureCategory.SCHEMA_MISMATCH, "Missing latitude or longitude"

        try:
            lat = float(record["latitude"])
            lon = float(record["longitude"])
        except (ValueError, TypeError):
            return False, IngestionFailureCategory.INVALID_COORDINATE, "Non-numeric coordinate values"

        import math
        if math.isnan(lat) or math.isnan(lon) or math.isinf(lat) or math.isinf(lon):
            return False, IngestionFailureCategory.INVALID_COORDINATE, "NaN or infinite coordinate values"

        # Check geodetic coordinate bounds (-90 to 90, -180 to 180)
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return False, IngestionFailureCategory.INVALID_COORDINATE, f"Coordinates ({lat}, {lon}) exceed global geodetic bounds"

        # Coarse geographic box check
        if not (INDIA_LAT_MIN <= lat <= INDIA_LAT_MAX and INDIA_LON_MIN <= lon <= INDIA_LON_MAX):
            from backend.app.services.india_boundary_service import india_boundary_service
            neighbor = india_boundary_service.detect_neighboring_country(lat, lon)
            return False, IngestionFailureCategory.INVALID_COORDINATE, f"SOVEREIGN_OUT_OF_DOMAIN: Coordinates ({lat}, {lon}) outside India operational bounds ({neighbor})"

        # Authoritative Sovereign India Boundary Containment Check
        from backend.app.services.india_boundary_service import india_boundary_service
        is_inside, state_name, district_name, _ = india_boundary_service.is_point_inside_india(lat, lon, db=db)
        if not is_inside:
            neighbor = india_boundary_service.detect_neighboring_country(lat, lon)
            return False, IngestionFailureCategory.INVALID_COORDINATE, f"SOVEREIGN_OUT_OF_DOMAIN: Point ({lat}, {lon}) lies outside sovereign India boundary (identified as {neighbor})"

        if isinstance(record, dict):
            record["admin_state"] = state_name
            record["admin_district"] = district_name or "UNKNOWN"
            record["country"] = "India"
            record["sovereign_filter"] = "PASS_SOVEREIGN_INDIA"

        # 2. Timestamp Validation
        ts_val = record.get("acq_timestamp") or record.get("observation_time")
        if not ts_val:
            return False, IngestionFailureCategory.INVALID_TIMESTAMP, "Missing acquisition timestamp"

        # 3. Physical Ranges for Thermal Telemetry
        frp = float(record.get("frp", 0.0) or 0.0)
        if frp < 0.0 or frp > 15000.0:
            return False, IngestionFailureCategory.PHYSICAL_OUT_OF_RANGE, f"FRP value {frp} MW outside physical limits [0, 15000]"

        bright = float(record.get("brightness", 300.0) or record.get("bright_ti4", 300.0) or 300.0)
        if bright < 150.0 or bright > 650.0:
            return False, IngestionFailureCategory.PHYSICAL_OUT_OF_RANGE, f"Brightness {bright}K outside operational sensor range [150, 650]"

        return True, None, None

    def process_ingestion_batch(
        self,
        db: Session,
        records: List[Union[Dict[str, Any], NormalizedThermalObservation]],
        provider: str = "NASA_FIRMS",
        dataset: str = "VIIRS_NOAA20_NRT",
        is_replay: bool = False,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a hardened ingestion cycle with:
        1. Batch metadata tracking in `ingestion_batches`
        2. Strict validation & dead-letter quarantine of malformed rows
        3. Deterministic SHA-256 fingerprint deduplication
        4. Replay safety (no duplicate downstream events/alerts)
        5. Checkpoint watermark updates in `ingestion_checkpoints`
        6. Forwarding accepted observations to WP1 proactive intelligence engine
        7. Atomic partial batch failure handling
        """
        t_start = time.perf_counter()
        batch_id = f"BATCH-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        corr_id = correlation_id or f"ing-{uuid.uuid4().hex[:8]}"
        processing_id = f"proc-{uuid.uuid4().hex[:8]}"
        started_at = datetime.now(timezone.utc)

        # 1. Initialize IngestionBatchModel
        batch_record = IngestionBatchModel(
            id=str(uuid.uuid4()),
            batch_id=batch_id,
            provider=provider.upper(),
            dataset=dataset.upper(),
            mode="REPLAY" if is_replay else "INCREMENTAL",
            started_at=started_at,
            records_received=len(records),
            status="RUNNING"
        )
        db.add(batch_record)
        db.flush()

        # Update or get DataSource record
        data_source = db.query(DataSource).filter(DataSource.source_name == provider.upper()).first()
        if not data_source:
            data_source = DataSource(
                id=str(uuid.uuid4()),
                source_name=provider.upper(),
                adapter_class="FIRMSAdapter" if "FIRMS" in provider.upper() else "ThermalSourceAdapter",
                category="THERMAL_HOTSPOTS",
                configured=True,
                is_active=True,
                health_status=ProviderHealthState.HEALTHY.value
            )
            db.add(data_source)
            db.flush()

        accepted_observations: List[Dict[str, Any]] = []
        quarantined_count = 0
        duplicate_count = 0
        failed_count = 0
        latest_obs_time: Optional[datetime] = None
        last_record_id: Optional[str] = None

        for item in records:
            # Normalize item to dictionary
            if isinstance(item, NormalizedThermalObservation):
                rec_dict = {
                    "source_record_id": item.source_record_id,
                    "source": item.source,
                    "sensor": item.sensor,
                    "satellite": item.satellite,
                    "latitude": item.latitude,
                    "longitude": item.longitude,
                    "acq_timestamp": item.acq_timestamp,
                    "brightness": item.brightness,
                    "bright_t31": item.bright_t31,
                    "frp": item.frp,
                    "confidence": item.confidence,
                    "day_night": item.day_night,
                    "metadata": item.metadata,
                    "is_demo": item.is_demo
                }
            else:
                rec_dict = dict(item)

            # Step 1: Physical and Geodetic Validation (including Authoritative Sovereign Containment)
            is_valid, err_cat, err_msg = self.validate_observation(rec_dict, db=db)

            if not is_valid:
                quarantined_count += 1
                dead_letter_service.record_quarantine(
                    db=db,
                    provider=provider,
                    dataset=dataset,
                    reason=err_msg or "Validation rejected",
                    error_category=err_cat or IngestionFailureCategory.UNKNOWN_FAILURE,
                    source_record_id=rec_dict.get("source_record_id"),
                    raw_payload=rec_dict,
                    batch_id=batch_id
                )
                continue

            # Parse acquisition timestamp cleanly
            acq_ts = rec_dict["acq_timestamp"]
            if isinstance(acq_ts, str):
                try:
                    acq_dt = datetime.fromisoformat(acq_ts.replace("Z", "+00:00"))
                except ValueError:
                    acq_dt = datetime.strptime(acq_ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            elif isinstance(acq_ts, datetime):
                acq_dt = acq_ts
            else:
                acq_dt = datetime.now(timezone.utc)

            rec_dict["acq_timestamp"] = acq_dt
            lat = float(rec_dict["latitude"])
            lon = float(rec_dict["longitude"])
            sensor = str(rec_dict.get("sensor", "VIIRS_NOAA20"))

            # Step 2: Deterministic SHA-256 Fingerprint Deduplication
            fingerprint = compute_deterministic_fingerprint(provider, sensor, lat, lon, acq_dt)
            rec_dict["fingerprint"] = fingerprint

            # Check DB for duplicate
            is_dup, existing_id = idempotency_service.check_database_duplicate(
                db=db, latitude=lat, longitude=lon, acq_timestamp=acq_dt, sensor=sensor, fingerprint=fingerprint
            )

            if is_dup or (is_replay and is_dup):
                duplicate_count += 1
                continue

            # Unique accepted record
            accepted_observations.append(rec_dict)

            # Checkpoint cursor tracking
            if latest_obs_time is None or acq_dt > latest_obs_time:
                latest_obs_time = acq_dt
            if rec_dict.get("source_record_id"):
                last_record_id = str(rec_dict["source_record_id"])

        # Step 3: Atomic Downstream Forwarding to WP1 Proactive Intelligence Core
        downstream_result = None
        events_created = 0
        if accepted_observations:
            try:
                # Forward to WP1 pipeline service
                downstream_result = pipeline_service.process_observations(
                    db=db,
                    observations=accepted_observations,
                    source_name=f"{provider}_{dataset}"
                )
                events_created = downstream_result.get("events_created", 0)
            except Exception as e:
                failed_count = len(accepted_observations)
                logger.error(f"[INGESTION FAILURE] Downstream processing failed: {e}", exc_info=True)
                # Dead-letter failed records
                for failed_rec in accepted_observations:
                    dead_letter_service.record_quarantine(
                        db=db,
                        provider=provider,
                        dataset=dataset,
                        reason=f"Downstream engine failure: {sanitize_error_message(str(e))}",
                        error_category=IngestionFailureCategory.DOWNSTREAM_PROCESSING_FAILURE,
                        source_record_id=failed_rec.get("source_record_id"),
                        raw_payload=failed_rec,
                        batch_id=batch_id
                    )
                # Rollback broken transaction safely
                db.rollback()
                # Re-add batch status
                batch_record.status = "FAILED"
                batch_record.error_message = sanitize_error_message(str(e))
                db.add(batch_record)
                db.commit()
                raise IngestionException(
                    category=IngestionFailureCategory.DOWNSTREAM_PROCESSING_FAILURE,
                    message=f"Downstream intelligence engine failure: {e}",
                    provider=provider
                )

        # Step 4: Update Checkpoint Watermark if observations were accepted
        if latest_obs_time and not is_replay:
            checkpoint_service.update_checkpoint(
                db=db,
                provider=provider,
                dataset=dataset,
                latest_observation_time=latest_obs_time,
                last_source_record_id=last_record_id,
                batch_id=batch_id,
                cursor_metadata={"records_accepted": len(accepted_observations)}
            )

        # Step 5: Update Provider Health Status
        completed_at = datetime.now(timezone.utc)
        duration_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

        data_source.last_sync_at = completed_at
        data_source.last_success_at = completed_at
        data_source.health_status = ProviderHealthState.HEALTHY.value
        data_source.latency_ms = duration_ms

        batch_record.completed_at = completed_at
        batch_record.records_accepted = len(accepted_observations)
        batch_record.records_rejected = quarantined_count
        batch_record.records_quarantined = quarantined_count
        batch_record.records_duplicated = duplicate_count
        batch_record.records_failed = failed_count
        batch_record.status = (
            "COMPLETED" if (quarantined_count == 0 and failed_count == 0)
            else ("PARTIAL_SUCCESS" if len(accepted_observations) > 0 else "FAILED")
        )

        db.commit()

        return {
            "ingestion_id": batch_id,
            "batch_id": batch_id,
            "correlation_id": corr_id,
            "processing_id": processing_id,
            "source": f"{provider}_{dataset}",
            "provider": provider,
            "dataset": dataset,
            "mode": "REPLAY" if is_replay else "INCREMENTAL",
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "records_received": len(records),
            "records_valid": len(accepted_observations),
            "records_accepted": len(accepted_observations),
            "records_rejected": quarantined_count,
            "records_quarantined": quarantined_count,
            "records_duplicate": duplicate_count,

            "records_failed": failed_count,
            "records_processed": len(accepted_observations),
            "events_created": events_created,
            "duration_ms": duration_ms,
            "provider_status": data_source.health_status,
            "status": batch_record.status,
            "downstream_summary": downstream_result
        }


hardened_ingestion_service = HardenedIngestionService()
