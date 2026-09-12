"""
AGNI-NETRA JARVIS Phase 16: Global Data Ingestion & Governance Data-Plane Models
Pydantic schemas and enums for Canonical Ingestion Records, Batches, Quarantine,
Dataset Registry, and Checkpoints.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class IngestionProcessingState(str, Enum):
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    NORMALIZED = "NORMALIZED"
    DEDUPLICATED = "DEDUPLICATED"
    STORED = "STORED"
    QUARANTINED = "QUARANTINED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    REPLAYED = "REPLAYED"


class IngestionBatchStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class IngestionMode(str, Enum):
    INITIAL_LOAD = "INITIAL_LOAD"
    INCREMENTAL = "INCREMENTAL"
    REPLAY = "REPLAY"
    BACKFILL = "BACKFILL"


class QualityStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class DedupStatus(str, Enum):
    UNIQUE = "UNIQUE"
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    SOURCE_DUPLICATE = "SOURCE_DUPLICATE"
    CROSS_PROVIDER_DUPLICATE = "CROSS_PROVIDER_DUPLICATE"
    SAME_SOURCE_REPETITION = "SAME_SOURCE_REPETITION"


class FreshnessStatus(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    VERY_STALE = "VERY_STALE"
    UNKNOWN = "UNKNOWN"


class CoverageScope(str, Enum):
    GLOBAL = "GLOBAL"
    REGIONAL = "REGIONAL"
    NATIONAL = "NATIONAL"
    PARTIAL = "PARTIAL"
    NOT_CONFIGURED = "NOT_CONFIGURED"


class RecordLifecycleState(str, Enum):
    ORIGINAL = "ORIGINAL"
    CORRECTED = "CORRECTED"
    RETRACTED = "RETRACTED"


class IngestionRecordSchema(BaseModel):
    """
    Canonical Ingestion Record representing a single raw-to-normalized observation.
    Maintains recoverable source record identity, quality scores, and dedup state.
    """
    ingestion_id: str = Field(..., description="Unique ingestion record identifier")
    provider: str = Field(..., description="Upstream intelligence provider identifier")
    dataset: str = Field(..., description="Underlying dataset / sensor stream")
    source_record_id: Optional[str] = Field(None, description="Native source identifier from upstream provider")
    batch_id: str = Field(..., description="Associated IngestionBatch ID")
    received_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    observation_time: Optional[str] = Field(None, description="Normalized ISO-8601 UTC observation timestamp")
    country: str = Field("GLOBAL", description="Country or global scope")
    jurisdiction: Optional[str] = Field(None, description="State, province, or sub-national boundary")
    latitude: Optional[float] = Field(None, description="WGS84 latitude [-90.0, 90.0]")
    longitude: Optional[float] = Field(None, description="WGS84 longitude [-180.0, 180.0]")
    geometry: Optional[Dict[str, Any]] = Field(None, description="Canonical GeoJSON geometry")
    schema_version: str = Field("1.0.0", description="Record schema specification version")
    source_type: str = Field("REAL_PROVIDER", description="REAL_PROVIDER, LOCAL_DATASET, TEST_FIXTURE, etc.")
    quality_status: QualityStatus = Field(QualityStatus.PASS, description="Quality status (PASS, WARN, FAIL)")
    quality_reasons: List[str] = Field(default_factory=list, description="Reasons for quality status")
    dedup_status: DedupStatus = Field(DedupStatus.UNIQUE, description="Deduplication state")
    duplicate_of_id: Optional[str] = Field(None, description="Ingestion ID of matching master record if duplicate")
    provenance_id: Optional[str] = Field(None, description="Linked SourceProvenance ID")
    processing_status: IngestionProcessingState = Field(IngestionProcessingState.RECEIVED)
    lifecycle_state: RecordLifecycleState = Field(RecordLifecycleState.ORIGINAL)
    error_code: Optional[str] = Field(None, description="Standardized error code if failed/quarantined")
    error_message_safe: Optional[str] = Field(None, description="Sanitized error description")
    raw_payload: Dict[str, Any] = Field(default_factory=dict, description="Raw source fields without credentials")
    normalized_payload: Dict[str, Any] = Field(default_factory=dict, description="Canonicalized key-value payload")

    model_config = {"from_attributes": True}


class IngestionBatchSchema(BaseModel):
    """
    Ingestion Batch tracking atomic execution, throughput metrics, and checksum verification.
    """
    batch_id: str = Field(..., description="Unique batch identifier (e.g. BATCH-20260912-A1B2)")
    provider: str = Field(..., description="Provider name")
    dataset: str = Field(..., description="Dataset name")
    mode: IngestionMode = Field(IngestionMode.INCREMENTAL)
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = Field(None)
    records_received: int = Field(0)
    records_accepted: int = Field(0)
    records_rejected: int = Field(0)
    records_quarantined: int = Field(0)
    records_duplicated: int = Field(0)
    records_failed: int = Field(0)
    schema_version: str = Field("1.0.0")
    normalization_version: str = Field("1.0.0")
    checksum: Optional[str] = Field(None, description="SHA-256 batch integrity checksum")
    status: IngestionBatchStatus = Field(IngestionBatchStatus.RUNNING)
    error_message: Optional[str] = Field(None)
    checkpoint: Dict[str, Any] = Field(default_factory=dict)
    metadata_payload: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class IngestionQuarantineSchema(BaseModel):
    """
    Quarantine storage for malformed or rejected records, preventing poisoning of intelligence tables.
    """
    quarantine_id: str = Field(..., description="Unique quarantine entry identifier")
    batch_id: Optional[str] = Field(None)
    provider: str = Field(...)
    dataset: str = Field(...)
    source_record_id: Optional[str] = Field(None)
    reason: str = Field(..., description="Rejection / quarantine reason")
    error_code: str = Field("VALIDATION_FAILURE")
    raw_safe_reference: Dict[str, Any] = Field(default_factory=dict, description="Safe snippet of raw data without secrets")
    detected_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = Field(None)
    resolution: str = Field("UNRESOLVED", description="UNRESOLVED, REPROCESSED, DISCARDED, OVERRIDDEN")
    resolved_by: Optional[str] = Field(None)

    model_config = {"from_attributes": True}


class DatasetRegistrySchema(BaseModel):
    """
    Factual metadata and governance contract for an integrated intelligence dataset.
    """
    dataset_id: str = Field(..., description="Unique dataset identifier (e.g. NASA_FIRMS_VIIRS_NRT)")
    provider: str = Field(..., description="Provider identifier")
    name: str = Field(..., description="Human-readable dataset name")
    version: str = Field("v1.0")
    license_reference: str = Field("LICENSE_INFO_UNVERIFIED", description="Official license or reference")
    coverage_scope: CoverageScope = Field(CoverageScope.GLOBAL)
    country: Optional[str] = Field(None)
    spatial_resolution: Optional[str] = Field(None)
    temporal_resolution: Optional[str] = Field(None)
    retention_policy: str = Field("INDEFINITE")
    schema_version: str = Field("1.0.0")
    quality_policy: str = Field("STANDARD_RANGE_AND_GEO_VALIDATION")
    provenance_policy: str = Field("IMMUTABLE_SOURCE_LINEAGE")
    status: str = Field("AVAILABLE", description="AVAILABLE, PARTIAL, STALE, DEGRADED, UNAVAILABLE, NOT_CONFIGURED")
    freshness_threshold_seconds: int = Field(86400, description="Freshness threshold in seconds (e.g. 24h = 86400)")
    last_observation_time: Optional[str] = Field(None)
    last_ingestion_time: Optional[str] = Field(None)
    record_count: int = Field(0)
    spatial_extent: Dict[str, Any] = Field(default_factory=dict)
    temporal_extent: Dict[str, Any] = Field(default_factory=dict)
    metadata_info: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class IngestionCheckpointSchema(BaseModel):
    """
    Deterministic checkpoint enabling safe restart and deduplication across batches.
    """
    checkpoint_key: str = Field(..., description="Unique key, e.g. PROVIDER:DATASET")
    provider: str = Field(...)
    dataset: str = Field(...)
    last_successful_observation_time: Optional[str] = Field(None)
    last_successful_source_record_id: Optional[str] = Field(None)
    last_successful_batch_id: Optional[str] = Field(None)
    cursor_state: Dict[str, Any] = Field(default_factory=dict)
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = {"from_attributes": True}
