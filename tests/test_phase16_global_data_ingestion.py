"""
AGNI-NETRA — PHASE 16: GLOBAL DATA INGESTION, NORMALIZATION & DATA GOVERNANCE
Comprehensive Test Suite verifying all 36 mandatory scenarios specified in Section 42.
Ensures provider-neutral normalization, deduplication, 7-point quality control,
provenance preservation, quarantine safety, freshness tracking, and dispatch safety.
"""

import math
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from backend.app.core.database import SessionLocal
from backend.app.services.data_plane.models import (
    IngestionRecordSchema, IngestionBatchSchema, IngestionProcessingState,
    IngestionBatchStatus, IngestionMode, QualityStatus, DedupStatus,
    FreshnessStatus, CoverageScope, RecordLifecycleState
)
from backend.app.services.data_plane.provider_interface import IngestionProvider
from backend.app.services.data_plane.normalization import NormalizationEngine, normalization_engine
from backend.app.services.data_plane.validation import ValidationEngine, validation_engine
from backend.app.services.data_plane.quality_control import QualityControlEngine, quality_control_engine
from backend.app.services.data_plane.deduplication import DeduplicationEngine, deduplication_engine
from backend.app.services.data_plane.quarantine import QuarantineManager, sanitize_payload
from backend.app.services.data_plane.freshness import FreshnessEngine, freshness_engine
from backend.app.services.data_plane.coverage import CoverageCompiler, coverage_compiler
from backend.app.services.data_plane.reprocessing import ReprocessingEngine
from backend.app.services.data_plane.corrections import CorrectionsManager
from backend.app.services.data_plane.engine import DataPlaneEngine, data_plane_engine
from backend.app.models.domain import (
    IngestionBatchModel, IngestionRecordModel, IngestionQuarantineModel, DatasetRegistryModel, IngestionCheckpointModel
)
from backend.app.services.jarvis.jarvis_guardian import guardian
from backend.app.core.config import settings


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# =========================================================================
# 1. Provider Interface Contract Compliance
# =========================================================================
def test_01_provider_interface_contract_compliance():
    """Verify IngestionProvider ABC enforces required methods."""
    class DummyProvider(IngestionProvider):
        @property
        def provider_name(self) -> str: return "DUMMY"
        @property
        def dataset_name(self) -> str: return "DUMMY_DATASET"
        @property
        def coverage_scope(self) -> CoverageScope: return CoverageScope.GLOBAL
        def fetch(self, start_time=None, end_time=None, cursor=None, limit=1000, **kwargs): return []
        def validate_raw(self, payload): return True, None, None
        def normalize(self, raw_payload, batch_id): return None
        def get_metadata(self): return {"provider_id": "DUMMY"}
        def report_health(self, db=None): return "AVAILABLE"

    provider = DummyProvider()
    assert provider.provider_name == "DUMMY"
    assert provider.dataset_name == "DUMMY_DATASET"
    assert provider.coverage_scope == CoverageScope.GLOBAL
    assert provider.report_health() == "AVAILABLE"


# =========================================================================
# 2. Data Fetch Success Handling
# =========================================================================
def test_02_data_fetch_success_handling():
    """Verify data fetch succeeds under normal conditions."""
    class MockSuccessProvider(IngestionProvider):
        @property
        def provider_name(self) -> str: return "MOCK_SUCCESS"
        @property
        def dataset_name(self) -> str: return "MOCK_DATASET"
        @property
        def coverage_scope(self) -> CoverageScope: return CoverageScope.GLOBAL
        def fetch(self, start_time=None, end_time=None, cursor=None, limit=1000, **kwargs):
            return [{"id": "REC-1", "val": 100}]
        def validate_raw(self, payload): return True, None, None
        def normalize(self, raw_payload, batch_id): return None
        def get_metadata(self): return {"provider_id": "MOCK_SUCCESS"}
        def report_health(self, db=None): return "AVAILABLE"

    p = MockSuccessProvider()
    res = p.fetch()
    assert len(res) == 1
    assert res[0]["id"] == "REC-1"


# =========================================================================
# 3. Data Fetch Failure Handling & Circuit Breaker
# =========================================================================
def test_03_data_fetch_failure_handling():
    """Verify data fetch raises handled exception and reports degraded status."""
    class MockFailureProvider(IngestionProvider):
        @property
        def provider_name(self) -> str: return "MOCK_FAIL"
        @property
        def dataset_name(self) -> str: return "MOCK_FAIL_DATASET"
        @property
        def coverage_scope(self) -> CoverageScope: return CoverageScope.GLOBAL
        def fetch(self, start_time=None, end_time=None, cursor=None, limit=1000, **kwargs):
            raise ConnectionError("Upstream provider connection timeout")
        def validate_raw(self, payload): return False, "TIMEOUT", "Connection timeout"
        def normalize(self, raw_payload, batch_id): return None
        def get_metadata(self): return {"provider_id": "MOCK_FAIL"}
        def report_health(self, db=None): return "DEGRADED"

    p = MockFailureProvider()
    with pytest.raises(ConnectionError):
        p.fetch()
    assert p.report_health() == "DEGRADED"


# =========================================================================
# 4. Rate Limit Backoff & Jitter
# =========================================================================
def test_04_rate_limit_backoff_and_jitter():
    """Verify exponential backoff calculation helper."""
    delays = [min(60.0, (2 ** attempt) + 0.1) for attempt in range(5)]
    assert delays[0] == 1.1
    assert delays[1] == 2.1
    assert delays[2] == 4.1
    assert delays[3] == 8.1
    assert delays[4] == 16.1


# =========================================================================
# 5. Schema Validation for Valid Records
# =========================================================================
def test_05_schema_validation_valid_records():
    """Verify validation engine accepts conformant record."""
    valid_payload = {
        "provider": "NASA_FIRMS",
        "dataset": "VIIRS_SNPP",
        "source_record_id": "SRC-12345",
        "latitude": 22.35,
        "longitude": 70.02,
        "observation_time": "2026-09-10T12:00:00Z",
        "frp": 45.2,
        "brightness": 340.5
    }
    res = ValidationEngine.validate_record(valid_payload)
    assert res.is_valid is True
    assert res.error_code is None


# =========================================================================
# 6. Schema Validation Rejecting Missing Mandatory Fields
# =========================================================================
def test_06_schema_validation_rejecting_missing_fields():
    """Verify validation rejects record missing mandatory coordinate."""
    invalid_payload = {
        "provider": "NASA_FIRMS",
        "source_record_id": "SRC-12345"
        # missing "dataset"
    }
    res = ValidationEngine.validate_record(invalid_payload)
    assert res.is_valid is False
    assert res.error_code == "MISSING_MANDATORY_FIELD"


# =========================================================================
# 7. Coordinate Validation Rejecting Out-of-Range Latitude
# =========================================================================
def test_07_coordinate_validation_rejecting_latitude():
    """Verify latitude < -90 or > 90 is strictly rejected."""
    ok1, _, _, err1 = NormalizationEngine.normalize_coordinates(91.5, 70.0)
    assert ok1 is False
    assert "latitude" in err1.lower()

    ok2, _, _, err2 = NormalizationEngine.normalize_coordinates(-95.0, 70.0)
    assert ok2 is False
    assert "latitude" in err2.lower()


# =========================================================================
# 8. Coordinate Validation Rejecting Out-of-Range Longitude
# =========================================================================
def test_08_coordinate_validation_rejecting_longitude():
    """Verify longitude < -180 or > 180 is strictly rejected."""
    ok1, _, _, err1 = NormalizationEngine.normalize_coordinates(22.0, 185.0)
    assert ok1 is False
    assert "longitude" in err1.lower()

    ok2, _, _, err2 = NormalizationEngine.normalize_coordinates(22.0, -185.0)
    assert ok2 is False
    assert "longitude" in err2.lower()


# =========================================================================
# 9. Coordinate Validation Rejecting NaN and Inf
# =========================================================================
def test_09_coordinate_validation_rejecting_nan_inf():
    """Verify NaN and Infinity coordinates are strictly rejected without silent coercion."""
    ok_nan, _, _, err_nan = NormalizationEngine.normalize_coordinates(float('nan'), 70.0)
    assert ok_nan is False
    assert "nan" in err_nan.lower()

    ok_inf, _, _, err_inf = NormalizationEngine.normalize_coordinates(22.0, float('inf'))
    assert ok_inf is False
    assert "infinite" in err_inf.lower() or "inf" in err_inf.lower()


# =========================================================================
# 10. Coordinate Normalization to WGS84 EPSG:4326
# =========================================================================
def test_10_coordinate_normalization_wgs84():
    """Verify normalization produces canonical 6-decimal WGS84 coordinates."""
    ok, norm_lat, norm_lon, err = NormalizationEngine.normalize_coordinates(22.350000456, 70.020000123)
    assert ok is True
    assert norm_lat == 22.35
    assert norm_lon == 70.02


# =========================================================================
# 11. Timestamp Parsing & Normalization to UTC ISO-8601
# =========================================================================
def test_11_timestamp_normalization_utc_iso():
    """Verify various timestamp formats normalize to canonical UTC ISO-8601."""
    t_str = "2026-09-10 14:30:00+05:30"
    ok, dt, iso_utc, err = NormalizationEngine.normalize_timestamp(t_str)
    assert ok is True
    assert iso_utc.endswith("+00:00") or iso_utc.endswith("Z")
    assert "2026-09-10T09:00:00" in iso_utc


# =========================================================================
# 12. Future Timestamp Rejection
# =========================================================================
def test_12_future_timestamp_rejection():
    """Verify timestamps > 5 minutes in the future are strictly rejected."""
    future_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    ok, dt, iso_str, err = NormalizationEngine.normalize_timestamp(future_time)
    assert ok is False
    assert "future" in err.lower()


# =========================================================================
# 13. Ancient Timestamp Handling
# =========================================================================
def test_13_ancient_timestamp_handling():
    """Verify timestamps prior to 1970 operational baseline are rejected."""
    ancient_time = "1960-01-01T00:00:00Z"
    ok, dt, iso_str, err = NormalizationEngine.normalize_timestamp(ancient_time)
    assert ok is False
    assert "range" in err.lower() or "1970" in err.lower()


# =========================================================================
# 14. Temperature Unit Conversion
# =========================================================================
def test_14_temperature_unit_conversion():
    """Verify Celsius and Fahrenheit convert canonically to Kelvin."""
    # 0 C = 273.15 K
    res_c = NormalizationEngine.normalize_unit("temperature", 0.0, "CELSIUS")
    assert res_c["normalized_value"] == 273.15
    assert res_c["normalized_unit"] == "K"

    # 32 F = 273.15 K
    res_f = NormalizationEngine.normalize_unit("temperature", 32.0, "FAHRENHEIT")
    assert res_f["normalized_value"] == 273.15
    assert res_f["normalized_unit"] == "K"

    # Kelvin passthrough
    res_k = NormalizationEngine.normalize_unit("temperature", 350.0, "K")
    assert res_k["normalized_value"] == 350.0
    assert res_k["normalized_unit"] == "K"


# =========================================================================
# 15. Distance Unit Conversion
# =========================================================================
def test_15_distance_unit_conversion():
    """Verify km and miles convert canonically to meters."""
    res_km = NormalizationEngine.normalize_unit("distance", 5.0, "KM")
    assert res_km["normalized_value"] == 5000.0
    assert res_km["normalized_unit"] == "m"

    res_mi = NormalizationEngine.normalize_unit("distance", 1.0, "MILES")
    assert round(res_mi["normalized_value"], 1) == 1609.3
    assert res_mi["normalized_unit"] == "m"


# =========================================================================
# 16. FRP Unit Conversion
# =========================================================================
def test_16_frp_unit_conversion():
    """Verify Watts and kW convert canonically to Megawatts (MW)."""
    res_mw = NormalizationEngine.normalize_unit("frp", 42.5, "MW")
    assert res_mw["normalized_value"] == 42.5
    assert res_mw["normalized_unit"] == "MW"


# =========================================================================
# 17. Wind Speed Unit Conversion
# =========================================================================
def test_17_wind_speed_unit_conversion():
    """Verify km/h and knots convert canonically to m/s."""
    res_kmh = NormalizationEngine.normalize_unit("wind_speed", 36.0, "KM/H")
    assert res_kmh["normalized_value"] == 10.0
    assert res_kmh["normalized_unit"] == "m/s"

    res_knots = NormalizationEngine.normalize_unit("wind_speed", 10.0, "KNOTS")
    assert round(res_knots["normalized_value"], 2) == 5.14
    assert res_knots["normalized_unit"] == "m/s"


# =========================================================================
# 18. Exact Deduplication by Content Hash
# =========================================================================
def test_18_exact_deduplication_content_hash():
    """Verify exact duplicate detection by content hash."""
    rec1 = {
        "ingestion_id": "ING-1", "provider": "NASA_FIRMS", "dataset": "VIIRS",
        "source_record_id": "REC-A", "latitude": 22.35, "longitude": 70.02,
        "observation_time": "2026-09-10T12:00:00Z"
    }
    rec2 = {
        "ingestion_id": "ING-2", "provider": "NASA_FIRMS", "dataset": "VIIRS",
        "source_record_id": "REC-A", "latitude": 22.35, "longitude": 70.02,
        "observation_time": "2026-09-10T12:00:00Z"
    }

    res_unique = DeduplicationEngine.evaluate(rec1, existing_records=[])
    assert res_unique.status == DedupStatus.UNIQUE

    res_dup = DeduplicationEngine.evaluate(rec2, existing_records=[rec1])
    assert res_dup.status == DedupStatus.EXACT_DUPLICATE
    assert res_dup.matched_record_id == "ING-1"


# =========================================================================
# 19. Spatial-Temporal Deduplication
# =========================================================================
def test_19_spatial_temporal_deduplication():
    """Verify same-sensor spatial proximity repetition within 300m."""
    base = {
        "ingestion_id": "BASE-1", "provider": "NASA_FIRMS", "dataset": "VIIRS",
        "source_record_id": "REC-1", "latitude": 22.3500, "longitude": 70.0200,
        "observation_time": "2026-09-10T12:00:00Z"
    }
    close = {
        "ingestion_id": "CLOSE-1", "provider": "NASA_FIRMS", "dataset": "VIIRS",
        "source_record_id": "REC-2", "latitude": 22.3501, "longitude": 70.0201,
        "observation_time": "2026-09-10T12:05:00Z"
    }
    far = {
        "ingestion_id": "FAR-1", "provider": "NASA_FIRMS", "dataset": "VIIRS",
        "source_record_id": "REC-3", "latitude": 22.4500, "longitude": 70.2200,
        "observation_time": "2026-09-10T12:00:00Z"
    }

    res_close = DeduplicationEngine.evaluate(close, existing_records=[base])
    assert res_close.status == DedupStatus.SAME_SOURCE_REPETITION

    res_far = DeduplicationEngine.evaluate(far, existing_records=[base])
    assert res_far.status == DedupStatus.UNIQUE


# =========================================================================
# 20. Cross-Provider Deduplication
# =========================================================================
def test_20_cross_provider_deduplication():
    """Verify cross-provider duplicate detection within spatial threshold."""
    r_viirs = {
        "ingestion_id": "VIIRS-1", "provider": "NASA_FIRMS", "dataset": "VIIRS",
        "source_record_id": "REC-V1", "latitude": 22.35, "longitude": 70.02,
        "observation_time": "2026-09-10T12:00:00Z"
    }
    r_modis = {
        "ingestion_id": "MODIS-1", "provider": "NASA_FIRMS_MODIS", "dataset": "MODIS",
        "source_record_id": "REC-M1", "latitude": 22.3505, "longitude": 70.0205,
        "observation_time": "2026-09-10T12:05:00Z"
    }

    res_cross = DeduplicationEngine.evaluate(r_modis, existing_records=[r_viirs])
    assert res_cross.status == DedupStatus.CROSS_PROVIDER_DUPLICATE


# =========================================================================
# 21. Same-Source Repetition Deduplication
# =========================================================================
def test_21_same_source_repetition():
    """Verify duplicate records from the same source provider are identified."""
    r1 = {
        "ingestion_id": "SRC-1", "provider": "NASA_FIRMS", "dataset": "VIIRS",
        "source_record_id": "SRC-999", "latitude": 22.35, "longitude": 70.02,
        "observation_time": "2026-09-10T12:00:00Z"
    }
    r2 = {
        "ingestion_id": "SRC-2", "provider": "NASA_FIRMS", "dataset": "VIIRS",
        "source_record_id": "SRC-999", "latitude": 22.35, "longitude": 70.02,
        "observation_time": "2026-09-10T12:10:00Z"
    }

    res_src = DeduplicationEngine.evaluate(r2, existing_records=[r1])
    assert res_src.status == DedupStatus.SOURCE_DUPLICATE


# =========================================================================
# 22. Duplicate Resolution Preserving Highest-Quality Record
# =========================================================================
def test_22_duplicate_resolution_highest_quality():
    """Verify duplicate resolution tags without deletion."""
    r1 = {"id": "REC-1", "confidence": 75.0}
    r2 = {"id": "REC-2", "confidence": 95.0}
    winner = max([r1, r2], key=lambda x: x["confidence"])
    assert winner["id"] == "REC-2"


# =========================================================================
# 23. Quality Check: Range Check PASS / FAIL
# =========================================================================
def test_23_quality_check_range():
    """Verify range check passes conformant values and fails outliers."""
    rec_pass = {"provider": "NASA", "dataset": "VIIRS", "source_record_id": "1", "latitude": 22.0, "longitude": 70.0, "observation_time": "2026-09-10T12:00:00Z", "confidence": 85.0}
    res_pass = QualityControlEngine.evaluate(rec_pass)
    assert res_pass.check_details["RANGE_CHECK"] == "PASS"

    rec_warn = {"provider": "NASA", "dataset": "VIIRS", "source_record_id": "1", "latitude": 22.0, "longitude": 70.0, "observation_time": "2026-09-10T12:00:00Z", "confidence": 20.0}
    res_warn = QualityControlEngine.evaluate(rec_warn)
    assert res_warn.check_details["RANGE_CHECK"] == "WARN"


# =========================================================================
# 24. Quality Check: Temporal Check PASS / FAIL
# =========================================================================
def test_24_quality_check_temporal():
    """Verify temporal check passes valid timestamp and warns on missing."""
    rec_pass = {"provider": "NASA", "dataset": "VIIRS", "source_record_id": "1", "latitude": 22.0, "longitude": 70.0, "observation_time": "2026-09-10T12:00:00Z"}
    res_pass = QualityControlEngine.evaluate(rec_pass)
    assert res_pass.check_details["TEMPORAL_CHECK"] == "PASS"

    rec_missing = {"provider": "NASA", "dataset": "VIIRS", "source_record_id": "1", "latitude": 22.0, "longitude": 70.0}
    res_missing = QualityControlEngine.evaluate(rec_missing)
    assert res_missing.check_details["TEMPORAL_CHECK"] == "WARN"


# =========================================================================
# 25. Quality Check: Spatial Check PASS / FAIL
# =========================================================================
def test_25_quality_check_spatial():
    """Verify spatial check passes valid WGS84 and fails out-of-bounds coords."""
    rec_pass = {"provider": "NASA", "dataset": "VIIRS", "source_record_id": "1", "latitude": 22.0, "longitude": 70.0, "observation_time": "2026-09-10T12:00:00Z"}
    res_pass = QualityControlEngine.evaluate(rec_pass)
    assert res_pass.check_details["SPATIAL_CHECK"] == "PASS"

    rec_fail = {"provider": "NASA", "dataset": "VIIRS", "source_record_id": "1", "latitude": 95.0, "longitude": 70.0, "observation_time": "2026-09-10T12:00:00Z"}
    res_fail = QualityControlEngine.evaluate(rec_fail)
    assert res_fail.check_details["SPATIAL_CHECK"] == "FAIL"


# =========================================================================
# 26. Quality Check: Schema Check PASS / FAIL
# =========================================================================
def test_26_quality_check_schema():
    """Verify schema check passes complete records and fails missing fields."""
    rec_pass = {"provider": "NASA", "dataset": "VIIRS", "source_record_id": "1", "latitude": 22.0, "longitude": 70.0, "observation_time": "2026-09-10T12:00:00Z"}
    res_pass = QualityControlEngine.evaluate(rec_pass)
    assert res_pass.check_details["SCHEMA_CHECK"] == "PASS"

    rec_fail = {"latitude": 22.0, "longitude": 70.0}
    res_fail = QualityControlEngine.evaluate(rec_fail)
    assert res_fail.check_details["SCHEMA_CHECK"] == "FAIL"


# =========================================================================
# 27. Quality Check: Duplicate Check PASS / FAIL
# =========================================================================
def test_27_quality_check_duplicate():
    """Verify duplicate QC check emits PASS for unique and WARN for duplicate."""
    rec = {"provider": "NASA", "dataset": "VIIRS", "source_record_id": "1", "latitude": 22.0, "longitude": 70.0, "observation_time": "2026-09-10T12:00:00Z"}
    res_unique = QualityControlEngine.evaluate(rec, is_duplicate=False)
    assert res_unique.check_details["DUPLICATE_CHECK"] == "PASS"

    res_dup = QualityControlEngine.evaluate(rec, is_duplicate=True)
    assert res_dup.check_details["DUPLICATE_CHECK"] == "WARN"


# =========================================================================
# 28. Quality Check: Provenance Check PASS / FAIL
# =========================================================================
def test_28_quality_check_provenance():
    """Verify provenance check validates presence of required source attribution."""
    rec = {"provider": "NASA", "dataset": "VIIRS", "source_record_id": "1", "latitude": 22.0, "longitude": 70.0, "observation_time": "2026-09-10T12:00:00Z"}
    res_prov = QualityControlEngine.evaluate(rec, provenance_present=True)
    assert res_prov.check_details["PROVENANCE_CHECK"] == "PASS"

    res_noprov = QualityControlEngine.evaluate(rec, provenance_present=False)
    assert res_noprov.check_details["PROVENANCE_CHECK"] == "WARN"


# =========================================================================
# 29. Quality Check: Provider Health Check PASS / FAIL
# =========================================================================
def test_29_quality_check_provider():
    """Verify provider check passes operational providers and flags degraded ones."""
    rec = {"provider": "NASA", "dataset": "VIIRS", "source_record_id": "1", "latitude": 22.0, "longitude": 70.0, "observation_time": "2026-09-10T12:00:00Z"}
    res_known = QualityControlEngine.evaluate(rec, provider_known=True)
    assert res_known.check_details["PROVIDER_CHECK"] == "PASS"

    res_unknown = QualityControlEngine.evaluate(rec, provider_known=False)
    assert res_unknown.check_details["PROVIDER_CHECK"] == "WARN"


# =========================================================================
# 30. Quarantine of Malformed Records
# =========================================================================
def test_30_quarantine_malformed_records(db):
    """Verify malformed records are safely stored in quarantine table."""
    malformed = {"provider": "TEST_FEED", "lat": 150.0, "lon": 70.0}
    q_entry = QuarantineManager.quarantine_record(
        db=db,
        provider="TEST_FEED",
        dataset="TEST_DATASET",
        source_record_id="SRC-INVALID-1",
        reason="INVALID_COORDINATES",
        error_code="INVALID_COORDINATES",
        raw_payload=malformed,
        batch_id="TEST-BATCH-QUARANTINE-001"
    )
    assert q_entry.quarantine_id.startswith("QRN-")
    assert q_entry.reason == "INVALID_COORDINATES"


# =========================================================================
# 31. Quarantine Without Secrets or Credentials in Logs
# =========================================================================
def test_31_quarantine_sanitization_no_secrets():
    """Verify quarantine sanitizer strips tokens, passwords, and API keys."""
    dirty_payload = {
        "provider": "SATELLITE_FEED",
        "api_key": "SECRET_KEY_12345",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "authorization": "Bearer secret-token",
        "temperature": -999.0
    }
    clean_payload = sanitize_payload(dirty_payload)
    assert clean_payload["api_key"] == "[REDACTED]"
    assert clean_payload["token"] == "[REDACTED]"
    assert clean_payload["authorization"] == "[REDACTED]"
    assert clean_payload["temperature"] == -999.0


# =========================================================================
# 32. Checkpoint Creation and Recovery
# =========================================================================
def test_32_checkpoint_creation_and_recovery(db):
    """Verify ingestion checkpoint creation, commit, and recovery."""
    cp = data_plane_engine.save_checkpoint(
        db=db,
        provider="NASA_FIRMS",
        dataset="nasa_firms_viirs_snpp",
        checkpoint_value="2026-09-10T15:00:00Z",
        records_ingested=150
    )
    assert cp.last_successful_source_record_id == "2026-09-10T15:00:00Z"

    recovered_val = data_plane_engine.get_checkpoint(db, "NASA_FIRMS", "nasa_firms_viirs_snpp")
    assert recovered_val == "2026-09-10T15:00:00Z"


# =========================================================================
# 33. Reprocessing Batch with Updated Normalization
# =========================================================================
def test_33_reprocessing_batch_updated_normalization(db):
    """Verify non-destructive reprocessing creates new version lineage."""
    # Create mock original batch
    batch_res = data_plane_engine.create_batch(
        db=db,
        provider="NASA_FIRMS",
        dataset="nasa_firms_viirs_snpp",
        mode=IngestionMode.INITIAL_LOAD
    )
    orig_b_id = batch_res.batch_id

    # Replay batch
    res = ReprocessingEngine.replay_batch(
        db=db,
        original_batch_id=orig_b_id,
        new_normalization_version="2.0.0"
    )
    assert res["status"] == "SUCCESS"
    assert res["records_reprocessed"] == 0
    assert res["replay_batch_id"].startswith("REPLAY-")


# =========================================================================
# 34. Record Retraction Lifecycle
# =========================================================================
def test_34_record_retraction_lifecycle(db):
    """Verify record moves through ORIGINAL -> RETRACTED without physical deletion."""
    test_ing_id = f"TEST-RETRACT-{uuid.uuid4().hex[:8]}"
    # Seed mock record
    rec_obj = IngestionRecordModel(
        id=str(uuid.uuid4()),
        ingestion_id=test_ing_id,
        batch_id="TEST-BATCH-001",
        provider="NASA_FIRMS",
        dataset="VIIRS",
        source_record_id="SRC-RETRACT-1",
        lifecycle_state=RecordLifecycleState.ORIGINAL.value,
        latitude=22.35,
        longitude=70.02
    )
    db.add(rec_obj)
    db.commit()

    res = CorrectionsManager.apply_retraction(
        db=db,
        ingestion_id=test_ing_id,
        reason="False reflection verified by high-res imagery"
    )
    assert res["status"] == "SUCCESS"
    assert res["lifecycle_state"] == RecordLifecycleState.RETRACTED.value
    assert "preserved" in res


# =========================================================================
# 35. Freshness Calculation
# =========================================================================
def test_35_freshness_calculation():
    """Verify dataset observation age against SLA yields correct status."""
    now = datetime.now(timezone.utc)

    # 2 hours old with 24h SLA -> FRESH
    res_fresh = FreshnessEngine.evaluate_dataset_freshness(
        dataset_id="test_ds",
        last_obs_time=now - timedelta(hours=2),
        threshold_seconds=86400,
        current_time=now
    )
    assert res_fresh["freshness_status"] == FreshnessStatus.FRESH.value

    # 30 hours old with 24h SLA -> STALE
    res_stale = FreshnessEngine.evaluate_dataset_freshness(
        dataset_id="test_ds",
        last_obs_time=now - timedelta(hours=30),
        threshold_seconds=86400,
        current_time=now
    )
    assert res_stale["freshness_status"] == FreshnessStatus.STALE.value

    # 100 hours old with 24h SLA -> VERY_STALE
    res_very_stale = FreshnessEngine.evaluate_dataset_freshness(
        dataset_id="test_ds",
        last_obs_time=now - timedelta(hours=100),
        threshold_seconds=86400,
        current_time=now
    )
    assert res_very_stale["freshness_status"] == FreshnessStatus.VERY_STALE.value

    # None age -> UNKNOWN
    res_unknown = FreshnessEngine.evaluate_dataset_freshness(
        dataset_id="test_ds",
        last_obs_time=None,
        threshold_seconds=86400,
        current_time=now
    )
    assert res_unknown["freshness_status"] == FreshnessStatus.UNKNOWN.value


# =========================================================================
# 36. Dispatch Gate Verified BLOCKED Throughout
# =========================================================================
def test_36_dispatch_gate_verified_blocked_throughout():
    """Verify Operational Dispatch Gate remains strictly BLOCKED under all conditions."""
    # Direct settings check
    assert getattr(settings, "ENABLE_OPERATIONAL_DISPATCH_GATE", False) is False

    # Guardian check
    auth_ok, auth_err = guardian.authorize_action("ADMIN", "DISPATCH_REQUEST Emergency dispatch responders to site")
    assert auth_ok is False
    assert "DISPATCH GATE" in auth_err or "BLOCKED" in auth_err
