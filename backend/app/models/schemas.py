from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ------------------------------------------------------------------------------
# Auth & User Schemas
# ------------------------------------------------------------------------------

class UserBase(BaseModel):
    email: str
    full_name: str
    organization: Optional[str] = None
    role: str = "PUBLIC"  # PUBLIC, RESEARCHER, INDUSTRY, ANALYST, AGENCY, ADMIN


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    facility_id: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(UserBase):
    id: str
    facility_id: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None


# ------------------------------------------------------------------------------
# Detections & Events Schemas
# ------------------------------------------------------------------------------

class ThermalDetectionOut(BaseModel):
    id: str
    source: str
    sensor: str
    satellite: Optional[str]
    latitude: float
    longitude: float
    acq_timestamp: datetime
    brightness: Optional[float]
    bright_t31: Optional[float]
    frp: float
    confidence: float
    day_night: str

    class Config:
        from_attributes = True


class ModelPredictionOut(BaseModel):
    predicted_class: str
    confidence: float
    class_probabilities: Dict[str, float]
    shap_values: Dict[str, Any]
    explanation_summary: Optional[str]
    predicted_at: datetime

    class Config:
        from_attributes = True


class RiskScoreOut(BaseModel):
    risk_score: float
    risk_level: str
    intensity_subscore: float
    abnormality_subscore: float
    persistence_subscore: float
    exposure_subscore: float
    context_subscore: float
    risk_reasons: List[str]
    evaluated_at: datetime

    class Config:
        from_attributes = True


class EventFeatureOut(BaseModel):
    frp_max: float
    frp_avg: float
    dist_to_facility_m: float
    dist_to_forest_m: float
    dist_to_agriculture_m: float
    dist_to_settlement_m: float
    persistence_score: float
    recurrence_rate: float
    day_night_ratio: float
    baseline_deviation_ratio: float
    industrial_context_score: float

    class Config:
        from_attributes = True


class ThermalEventOut(BaseModel):
    id: str
    event_code: str
    latitude: float
    longitude: float
    bounding_box: Optional[List[float]] = None
    first_seen: datetime
    last_seen: datetime
    detection_count: int
    avg_frp: float
    max_frp: float
    min_frp: float
    frp_variance: float
    avg_brightness: float
    satellite_count: int
    facility_id: Optional[str]
    candidate_facility_id: Optional[str]
    facility_status: str
    nearest_facility_distance_m: Optional[float]
    landcover_class: str
    state: str
    district: Optional[str]
    status: str
    is_demo: bool
    created_at: datetime
    
    # Nested Intelligence
    prediction: Optional[ModelPredictionOut] = None
    risk: Optional[RiskScoreOut] = None
    features: Optional[EventFeatureOut] = None

    class Config:
        from_attributes = True


class ThermalEventGeoJSON(BaseModel):
    type: str = "FeatureCollection"
    features: List[Dict[str, Any]]


class PaginatedEventsOut(BaseModel):
    total_count: int
    page: int
    limit: int
    total_pages: int
    items: List[ThermalEventOut]


# ------------------------------------------------------------------------------
# Facility Schemas
# ------------------------------------------------------------------------------

class HistoricalBaselineOut(BaseModel):
    id: str
    mean_frp: float
    median_frp: float
    std_frp: float
    max_historical_frp: float
    detection_frequency_monthly: float
    day_night_ratio: float
    monthly_pattern: Dict[str, float]
    baseline_status: str

    class Config:
        from_attributes = True


class FacilityBaselineOut(BaseModel):
    id: str
    facility_id: str
    mean_frp: float
    median_frp: float
    variance_frp: float
    max_historical_frp: float
    frp_distribution: Dict[str, float]
    frequency_days: int
    day_night_ratio: float
    status_band: str
    notes: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class IndustrialFacilityOut(BaseModel):
    id: str
    name: str
    facility_type: str
    status: str
    source: str
    state: str
    district: Optional[str]
    latitude: float
    longitude: float
    confidence_score: float
    operating_hours: str
    contact_info: Dict[str, Any]
    baselines: List[HistoricalBaselineOut] = []
    facility_baseline: Optional[FacilityBaselineOut] = None

    class Config:
        from_attributes = True


class CandidateFacilityOut(BaseModel):
    id: str
    name_label: str
    status: str
    latitude: float
    longitude: float
    state: str
    district: Optional[str]
    industrial_context_score: float
    persistence_days: int
    detection_count: int
    first_detected_at: datetime
    last_detected_at: datetime
    evidence_summary: Dict[str, Any]

    class Config:
        from_attributes = True


# ------------------------------------------------------------------------------
# Alerts & Verification Schemas
# ------------------------------------------------------------------------------

class AlertOut(BaseModel):
    id: str
    event_id: str
    alert_level: str
    alert_type: str
    title: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertUpdate(BaseModel):
    status: str  # NEW, ACKNOWLEDGED, UNDER_REVIEW, VERIFIED, RESOLVED


class VerificationCreate(BaseModel):
    event_id: str
    verified_label: str
    verification_action: str  # CONFIRM, CORRECT, MARK_UNCERTAIN, FALSE_POSITIVE
    notes: Optional[str] = None
    evidence_reviewed: Optional[Dict[str, Any]] = None


class VerificationRecordOut(BaseModel):
    id: str
    event_id: str
    analyst_id: str
    original_prediction: str
    verified_label: str
    verification_action: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ------------------------------------------------------------------------------
# Model Registry & Dataset Schemas
# ------------------------------------------------------------------------------

class MLModelRegistryOut(BaseModel):
    id: str
    model_name: str
    version: str
    dataset_version: str
    algorithm: str
    metrics: Dict[str, Any]
    artifact_path: str
    status: str
    is_active: bool
    trained_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class MLModelStatusUpdate(BaseModel):
    status: str  # TRAINING, VALIDATION, CANDIDATE, APPROVED, ACTIVE, RETIRED
    notes: Optional[str] = None


class DatasetRegistryOut(BaseModel):
    id: str
    name: str
    version: str
    dataset_type: str
    source: str
    record_count: int
    verified_count: int
    class_distribution: Dict[str, int]
    training_eligible: bool
    manifest_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ------------------------------------------------------------------------------
# Event Data Lineage (Trace Data) Schemas
# ------------------------------------------------------------------------------

class EventTraceStep(BaseModel):
    step_number: int
    stage: str
    title: str
    status: str  # COMPLETED, WARNING, INFO
    timestamp: str
    details: Dict[str, Any]
    provenance_source: str


class EventTraceLineageOut(BaseModel):
    event_id: str
    event_code: str
    origin_type: Optional[str] = "REAL SATELLITE DATA"
    generated_at: str
    total_steps: int
    stages: List[EventTraceStep]


# ------------------------------------------------------------------------------
# Analytics & Reports Schemas
# ------------------------------------------------------------------------------

class DashboardKPIs(BaseModel):
    active_events_count: int
    industrial_candidates_count: int
    persistent_sources_count: int
    abnormal_anomalies_count: int
    critical_alerts_count: int
    verification_queue_count: int


class ClassDistributionItem(BaseModel):
    label: str
    count: int
    percentage: float


class RiskDistributionItem(BaseModel):
    level: str
    count: int
    color: str


class StateAnalyticsItem(BaseModel):
    state: str
    event_count: int
    avg_frp: float
    high_risk_count: int


class ReportOut(BaseModel):
    id: str
    event_id: str
    report_title: str
    file_path: str
    file_size_bytes: int
    summary_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ------------------------------------------------------------------------------
# Data Source Registry & Ingestion Schemas
# ------------------------------------------------------------------------------

class DataSourceOut(BaseModel):
    id: str
    source_name: str
    adapter_class: str
    category: str
    endpoint: Optional[str] = None
    auth_type: str = "NONE"
    configured: bool = False
    description: Optional[str] = None
    is_active: bool = True
    health_status: str = "HEALTHY"
    last_sync_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    latency_ms: float = 0.0
    record_count: int = 0
    provenance_info: Dict[str, Any] = {}
    terms_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ThermalHistoryOut(BaseModel):
    id: str
    source: str
    sensor: str
    satellite: Optional[str] = None
    latitude: float
    longitude: float
    acq_date: str
    acq_time: str
    acq_timestamp: datetime
    brightness: Optional[float] = None
    bright_t31: Optional[float] = None
    frp: float
    confidence: float
    day_night: str
    processing_type: str = "NRT"
    state: Optional[str] = None
    district: Optional[str] = None
    source_record_id: Optional[str] = None
    raw_metadata: Dict[str, Any] = {}
    is_demo: bool = False

    class Config:
        from_attributes = True


# ------------------------------------------------------------------------------
# Evidence & Human Verification Schemas
# ------------------------------------------------------------------------------

class EvidenceRecordCreate(BaseModel):
    event_id: str
    evidence_type: str  # ANALYST_VERIFICATION, PHOTO_UPLOAD, OFFICIAL_DOCUMENT, SATELLITE_CONTEXT, GIS_EVIDENCE, HISTORICAL_BASELINE, FIELD_NOTE
    evidence_source: str
    title: str
    notes: Optional[str] = None
    evidence_data: Dict[str, Any] = {}


class EvidenceRecordOut(BaseModel):
    id: str
    event_id: str
    evidence_type: str
    evidence_source: str
    title: str
    notes: Optional[str] = None
    evidence_data: Dict[str, Any] = {}
    verified: bool = False
    verified_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ------------------------------------------------------------------------------
# AGNI-SAT Software Satellite & Mission Control Schemas
# ------------------------------------------------------------------------------

class SimulationScenarioOut(BaseModel):
    id: str
    name: str
    scenario_type: str
    description: str
    target_state: str
    target_lat: float
    target_lon: float
    target_facility: Optional[str] = None
    expected_class: str
    expected_risk_level: str
    parameters: Dict[str, Any] = {}
    status: str
    last_run_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SatelliteTaskingRequest(BaseModel):
    satellite_id: str = "AGNI-SAT-01"
    target_name: str
    target_lat: float
    target_lon: float
    sensor_id: str = "THERMAL_MWIR"
    observation_window_minutes: int = 15
    priority: str = "HIGH"


class SatelliteTelemetryOut(BaseModel):
    id: str
    satellite_id: str
    sensor_id: str
    scenario_id: Optional[str] = None
    timestamp: datetime
    latitude: float
    longitude: float
    frp: float
    brightness: float
    confidence: float
    footprint_geojson: Dict[str, Any] = {}
    status: str
    raw_packet: Dict[str, Any] = {}
    is_simulation: bool = True

    class Config:
        from_attributes = True


class LatencyBenchmarkOut(BaseModel):
    observation_to_telemetry_ms: float
    telemetry_to_ingestion_ms: float
    clustering_ms: float
    gis_enrichment_ms: float
    ml_inference_ms: float
    shap_explanation_ms: float
    risk_evaluation_ms: float
    total_processing_ms: float
    target_fps_or_hz: float


class MissionTaskOut(BaseModel):
    id: str
    task_code: str
    satellite_id: str
    target_name: str
    target_lat: float
    target_lon: float
    sensor_id: str
    priority: str
    status: str
    scheduled_pass_time: datetime
    observed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


