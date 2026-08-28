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
