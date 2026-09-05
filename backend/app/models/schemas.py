from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class ModelPredictionOut(BaseModel):
    predicted_class: str
    confidence: float
    class_probabilities: Dict[str, float]
    shap_values: Dict[str, Any]
    explanation_summary: Optional[str]
    predicted_at: datetime

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class FacilityBaselineOut(BaseModel):
    id: str
    facility_id: str
    mean_frp: float
    median_frp: float
    variance_frp: float
    max_historical_frp: float
    frp_distribution: Dict[str, Any] = {}
    frequency_days: int
    day_night_ratio: float
    status_band: str
    notes: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MiningThermalAssociationOut(BaseModel):
    id: Union[UUID, str]
    facility_id: str
    distance_band: str
    detection_count: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    active_days_count: int = 0
    mean_frp: Optional[float] = None
    median_frp: Optional[float] = None
    p90_frp: Optional[float] = None
    p99_frp: Optional[float] = None
    max_frp: Optional[float] = None
    mean_confidence: Optional[float] = None
    day_detection_count: int = 0
    night_detection_count: int = 0
    recurrence_rate: Optional[float] = None
    persistence_days: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class FacilityMiningEvidenceOut(BaseModel):
    facility_id: str
    facility_name: str
    facility_type: str
    osm_object_id: Optional[str] = None
    osm_object_type: Optional[str] = None
    operator: Optional[str] = None
    mineral_commodity: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    administrative_source: Optional[str] = None
    latitude: float
    longitude: float

    ibm_lease_context_present: bool = False
    ibm_district_lease_count: Optional[int] = None
    ibm_district_lease_area_ha: Optional[float] = None
    ibm_potential_tier: Optional[str] = None
    ibm_district_minerals: List[Dict[str, Any]] = []

    nmi_resource_context_present: bool = False
    nmi_commodity_reserves: Optional[float] = None
    nmi_commodity_resources: Optional[float] = None
    nmi_commodity_unit: Optional[str] = None

    firms_associated_500m: int = 0
    firms_associated_1km: int = 0
    firms_associated_2km: int = 0
    first_thermal_seen: Optional[datetime] = None
    last_thermal_seen: Optional[datetime] = None
    active_days_count: int = 0
    mean_frp: Optional[float] = None
    median_frp: Optional[float] = None
    p90_frp: Optional[float] = None
    p99_frp: Optional[float] = None
    max_frp: Optional[float] = None

    mining_context_present: bool = True
    mining_geometry_present: bool = True
    thermal_activity_present: bool = False
    thermal_persistence_category: str = "NO_THERMAL_ACTIVITY"
    confidence_score: float = 0.5
    scientific_attribution: str
    evidence_summary: Dict[str, Any] = {}
    associations: List[MiningThermalAssociationOut] = []

    model_config = ConfigDict(from_attributes=True)


class MiningContextSummaryOut(BaseModel):
    state: Optional[str] = None
    district: Optional[str] = None
    potential_tier: Optional[str] = None
    total_leases: Optional[int] = None
    total_area_ha: Optional[float] = None
    top_minerals: List[Dict[str, Any]] = []
    facility_count: int = 0


class IndustrialFacilityOut(BaseModel):
    id: str
    name: str
    facility_type: str
    status: str
    source: str
    state: str
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    confidence_score: Optional[float] = 1.0
    operating_hours: str = "24x7"
    contact_info: Dict[str, Any] = {}
    
    # Canonical Registry Fields
    industry_id: Optional[str] = None
    industry_name: Optional[str] = None
    nic_code: Optional[str] = None
    master_sector: Optional[str] = None
    sub_sector: Optional[str] = None
    industry_type: Optional[str] = None
    company_name: Optional[str] = None
    facility_name: Optional[str] = None
    plant_name: Optional[str] = None
    city: Optional[str] = None
    industrial_area: Optional[str] = None
    plant_capacity: Optional[str] = None
    production_type: Optional[str] = None
    energy_intensity: Optional[str] = None
    electricity_consumption: Optional[str] = None
    fuel_consumption: Optional[str] = None
    water_consumption: Optional[str] = None
    co2_emissions: Optional[str] = None
    equipment_type: Optional[str] = None
    major_machinery: Optional[str] = None
    operating_status: Optional[str] = None
    enterprise_size: Optional[str] = None
    ownership_type: Optional[str] = None
    data_source: Optional[str] = None
    source_record_id: Optional[str] = None
    source_url: Optional[str] = None
    source_date: Optional[str] = None
    source_file: Optional[str] = None
    unit_count: Optional[int] = None
    commissioning_year_min: Optional[int] = None
    commissioning_year_max: Optional[int] = None
    cea_project_name: Optional[str] = None
    cea_organisation: Optional[str] = None
    prime_mover: Optional[str] = None
    firms_detections_500m: Optional[int] = 0
    firms_detections_1km: Optional[int] = 0
    firms_detections_2km: Optional[int] = 0
    thermal_activity_status: Optional[str] = None

    # PARIVESH Environmental Clearance Attributes
    environmental_clearance_present: Optional[bool] = False
    ec_proposal_id: Optional[str] = None
    ec_clearance_type: Optional[str] = None
    ec_clearance_status: Optional[str] = None
    ec_category: Optional[str] = None
    ec_decision_date: Optional[str] = None
    forest_related_flag: Optional[bool] = False
    wildlife_related_flag: Optional[bool] = False
    crz_related_flag: Optional[bool] = False

    baselines: List[HistoricalBaselineOut] = []
    facility_baseline: Optional[FacilityBaselineOut] = None
    mining_evidence: Optional[FacilityMiningEvidenceOut] = None

    model_config = ConfigDict(from_attributes=True)


class IbmMiningLeaseContextOut(BaseModel):
    id: Union[UUID, str]
    record_id: str
    state: Optional[str] = None
    district: Optional[str] = None
    mineral: Optional[str] = None
    lease_count: Optional[int] = None
    lease_area_ha: Optional[float] = None
    sector: Optional[str] = None
    potential_category: Optional[str] = None
    reference_year: int = 2024
    reference_date: Optional[Any] = None
    source_document: str
    table_number: str
    page_number: Optional[int] = None
    provisional_flag: bool = True
    source: str = "IBM"
    aggregation_level: str = "DISTRICT_MINERAL"
    raw_metadata: Dict[str, Any] = {}

class IbmMineralResourceOut(BaseModel):
    id: Union[UUID, str]
    record_id: str
    sl_no: Optional[int] = None
    commodity: Optional[str] = None
    mineral: str
    unit: Optional[str] = None
    reserves: Optional[float] = None
    remaining_resources: Optional[float] = None
    total_resources: Optional[float] = None
    not_estimated: bool = False
    reference_year: int = 2020
    reference_date: Optional[Any] = None
    source: str = "IBM"
    source_document: str
    page_number: Optional[int] = None
    table_number: str = "Table 6"
    provisional_flag: bool = True
    model_config = ConfigDict(from_attributes=True)


class IbmAuctionedBlockOut(BaseModel):
    id: Union[UUID, str]
    source_doc_id: str
    sl_no: int
    block_name: str
    state: str
    district: Optional[str] = None
    mineral: str
    preferred_bidder: Optional[str] = None
    auction_financial_year: str = "2024-25"
    matched_facility_id: Optional[str] = None
    match_confidence: str = "UNMATCHED"
    match_score: Optional[float] = None
    match_method: Optional[str] = None
    firms_count_500m: int = 0
    firms_count_1km: int = 0
    firms_count_2km: int = 0
    source: str = "IBM"
    source_document: str
    page_number: Optional[int] = None
    table_number: str = "Table 15"
    is_provisional: bool = True
    raw_metadata: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)


class PariveshProjectOut(BaseModel):
    id: str
    proposal_id: str
    project_name: str
    project_type: Optional[str] = None
    proponent: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    category: Optional[str] = None
    sector: Optional[str] = None
    clearance_type: Optional[str] = None
    clearance_status: Optional[str] = None
    proposal_date: Optional[str] = None
    decision_date: Optional[str] = None
    forest_related_flag: bool = False
    wildlife_related_flag: bool = False
    crz_related_flag: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_url: Optional[str] = None
    source_file: Optional[str] = None
    source_date: Optional[str] = None
    match_status: str = "UNMATCHED"
    matched_facility_id: Optional[str] = None
    match_confidence: Optional[str] = None
    match_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# Phase 2A: National Administrative Geography Schemas
# ------------------------------------------------------------------------------

class AdminBoundaryOut(BaseModel):
    id: Union[str, UUID]
    admin_level: int
    admin_level_name: str
    admin_code: str
    name: str
    normalized_name: str
    parent_code: Optional[str] = None
    parent_name: Optional[str] = None
    state_code: Optional[str] = None
    state_name: Optional[str] = None
    district_code: Optional[str] = None
    district_name: Optional[str] = None
    subdistrict_code: Optional[str] = None
    source: str
    source_document: str
    source_version: Optional[str] = "2024"
    is_authoritative: bool = True

    model_config = ConfigDict(from_attributes=True)


class StateSummaryOut(BaseModel):
    state_code: Optional[str] = None
    state_name: str
    district_count: int = 0
    subdistrict_count: int = 0
    facility_count: int = 0
    thermal_observation_count: int = 0


class DistrictSummaryOut(BaseModel):
    district_code: Optional[str] = None
    district_name: str
    state_name: str
    subdistrict_count: int = 0
    facility_count: int = 0
    thermal_observation_count: int = 0


class FacilityAdministrativeContextOut(BaseModel):
    facility_id: str
    original_state: Optional[str] = None
    original_district: Optional[str] = None
    original_city: Optional[str] = None
    derived_state: Optional[str] = None
    derived_district: Optional[str] = None
    derived_subdistrict: Optional[str] = None
    state_id: Optional[Union[str, UUID]] = None
    district_id: Optional[Union[str, UUID]] = None
    subdistrict_id: Optional[Union[str, UUID]] = None
    has_state_conflict: bool = False
    has_district_conflict: bool = False
    spatial_match_method: str = "POSTGIS_SPATIAL_JOIN"
    administrative_source: str = "geoBoundaries / Local Government Directory"
    administrative_confidence: str = "HIGH"

    model_config = ConfigDict(from_attributes=True)


class ObservationAdministrativeContextOut(BaseModel):
    detection_id: str
    state_id: Optional[Union[str, UUID]] = None
    state_name: Optional[str] = None
    district_id: Optional[Union[str, UUID]] = None
    district_name: Optional[str] = None
    subdistrict_id: Optional[Union[str, UUID]] = None
    subdistrict_name: Optional[str] = None
    spatial_match_method: str = "POSTGIS_SPATIAL_JOIN"
    boundary_source: str = "geoBoundaries / Local Government Directory"
    administrative_confidence: str = "HIGH"

    model_config = ConfigDict(from_attributes=True)


class PariveshAdministrativeContextOut(BaseModel):
    proposal_id: str
    original_state: Optional[str] = None
    original_district: Optional[str] = None
    derived_state: Optional[str] = None
    derived_district: Optional[str] = None
    derived_subdistrict: Optional[str] = None
    state_id: Optional[Union[str, UUID]] = None
    district_id: Optional[Union[str, UUID]] = None
    subdistrict_id: Optional[Union[str, UUID]] = None
    has_state_conflict: bool = False
    has_district_conflict: bool = False
    administrative_method: str = "POSTGIS_SPATIAL_JOIN"
    administrative_confidence: str = "HIGH"

    model_config = ConfigDict(from_attributes=True)


class AdministrativeReverseLookupOut(BaseModel):
    latitude: float
    longitude: float
    state_name: Optional[str] = None
    district_name: Optional[str] = None
    subdistrict_name: Optional[str] = None
    state_code: Optional[str] = None
    district_code: Optional[str] = None
    subdistrict_code: Optional[str] = None
    boundary_source: str = "geoBoundaries / Local Government Directory"
    match_method: str = "POSTGIS_SPATIAL_JOIN"


# =========================================================================
# LULC (Land Use / Land Cover) Response Schemas
# =========================================================================

class LULCClassOut(BaseModel):
    id: str
    source_class_code: str
    source_class_name: str
    canonical_class: str
    is_industrial_compatible: bool
    risk_weight: float
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LULCSourceOut(BaseModel):
    id: str
    source_name: str
    organization: str
    dataset_name: str
    resolution_m: float
    reference_year: int
    product_version: str
    access_type: str
    license: str
    source_url: str
    metadata_info: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class LULCLookupOut(BaseModel):
    latitude: float
    longitude: float
    coverage_status: str  # REAL, NO_COVERAGE, DEMO_FALLBACK
    source_coverage: str  # COVERED, UNAVAILABLE, DEMO_MOCK
    primary_class: Optional[str] = None
    source_class_code: Optional[str] = None
    source_class_name: Optional[str] = None
    is_industrial_zone: bool = False
    is_mining_zone: bool = False
    is_forest_zone: bool = False
    is_agriculture_zone: bool = False
    is_water_zone: bool = False
    distance_to_forest_m: float
    distance_to_agriculture_m: float
    distance_to_water_m: float
    distance_to_industrial_m: float
    distance_to_mining_m: float
    source: str = "ISRO_BHUVAN_50K"
    resolution_m: Optional[float] = 24.0
    reference_year: Optional[int] = 2025
    confidence: float
    spatial_match_method: str


class ObservationLULCContextOut(BaseModel):
    id: str
    detection_id: str
    primary_lulc_class: str
    source_lulc_class: str
    is_industrial_zone: bool
    is_mining_zone: bool
    is_forest_zone: bool
    is_agriculture_zone: bool
    is_water_zone: bool
    distance_to_forest_m: Optional[float] = None
    distance_to_agriculture_m: Optional[float] = None
    distance_to_water_m: Optional[float] = None
    distance_to_industrial_m: Optional[float] = None
    distance_to_mining_m: Optional[float] = None
    spatial_match_method: str
    confidence_score: float
    reference_date: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FacilityLULCContextOut(BaseModel):
    id: str
    facility_id: str
    primary_lulc_class: str
    source_lulc_class: str
    industrial_compatibility: str
    distance_to_forest_m: Optional[float] = None
    distance_to_agriculture_m: Optional[float] = None
    distance_to_water_m: Optional[float] = None
    distance_to_mining_m: Optional[float] = None
    confidence_score: float
    reference_date: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LULCStatsOut(BaseModel):
    total_sources: int
    total_classes: int
    total_features: int
    sources: List[LULCSourceOut]
    canonical_class_distribution: Dict[str, int]


# =========================================================================
# Forest Intelligence (FSI / ISFR / Protected Areas) Schemas
# =========================================================================

class FSISourceOut(BaseModel):
    id: str
    source_name: str
    organization: str
    dataset_name: str
    reference_year: int
    product_version: str
    access_method: str
    source_url: str
    license: str
    metadata_info: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class FSIISFRStatsOut(BaseModel):
    id: str
    state: str
    district: str
    admin_boundary_id: Optional[UUID] = None
    geographical_area_sqkm: float
    very_dense_forest_sqkm: float
    moderately_dense_forest_sqkm: float
    open_forest_sqkm: float
    total_forest_sqkm: float
    percent_of_geo_area: float
    scrub_sqkm: float
    reference_year: int
    source_id: str
    source_document: str
    page_table_reference: Optional[str] = None
    provisional_flag: bool

    model_config = ConfigDict(from_attributes=True)


class ProtectedAreaOut(BaseModel):
    id: str
    pa_name: str
    pa_type: str
    state: str
    district: Optional[str] = None
    established_year: Optional[int] = None
    area_sqkm: Optional[float] = None
    legal_status: Optional[str] = None
    source_id: str
    source_record_id: Optional[str] = None
    reference_date: Optional[str] = None
    metadata_info: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class ObservationForestContextOut(BaseModel):
    id: str
    detection_id: str
    is_inside_forest: bool
    forest_density_class: str
    is_inside_recorded_forest: bool
    is_inside_protected_area: bool
    protected_area_id: Optional[str] = None
    protected_area_type: Optional[str] = None
    protected_area_name: Optional[str] = None
    distance_to_protected_area_m: Optional[float] = None
    distance_to_forest_m: Optional[float] = None
    forest_context_level: str
    forest_fire_evidence: str
    source_id: Optional[str] = None
    reference_year: Optional[int] = None
    confidence_score: float
    spatial_match_method: str

    model_config = ConfigDict(from_attributes=True)


class FacilityForestContextOut(BaseModel):
    id: str
    facility_id: str
    nearest_protected_area_id: Optional[str] = None
    nearest_protected_area_name: Optional[str] = None
    nearest_protected_area_type: Optional[str] = None
    distance_to_protected_area_m: Optional[float] = None
    distance_to_forest_m: Optional[float] = None
    is_inside_esz_10km: bool
    esz_evaluation_status: str
    forest_context_level: str
    source_id: Optional[str] = None
    reference_year: Optional[int] = None
    confidence_score: float

    model_config = ConfigDict(from_attributes=True)


class ForestLookupOut(BaseModel):
    latitude: float
    longitude: float
    forest_context_level: str  # HIGH, MEDIUM, LOW, NONE
    is_inside_forest: bool
    forest_density_class: str  # VDF, MDF, OF, SCRUB, NON_FOREST
    is_inside_protected_area: bool
    protected_area_id: Optional[str] = None
    protected_area_name: Optional[str] = None
    protected_area_type: Optional[str] = None
    distance_to_forest_m: float
    distance_to_protected_area_m: float
    is_within_10km_esz_buffer: bool
    nearest_isfr_district: Optional[str] = None
    district_forest_cover_pct: Optional[float] = None
    primary_source: str
    reference_year: int
    confidence: float
    spatial_match_method: str


class ForestStatsOut(BaseModel):
    total_sources: int
    total_district_records: int
    total_protected_areas: int
    sources: List[FSISourceOut]
    protected_area_distribution: Dict[str, int]
    top_forested_districts: List[FSIISFRStatsOut]





