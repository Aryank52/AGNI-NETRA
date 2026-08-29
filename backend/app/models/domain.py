import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text, JSON, Enum
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="PUBLIC", nullable=False)  # PUBLIC, RESEARCHER, INDUSTRY, ANALYST, AGENCY, ADMIN
    organization = Column(String(255), nullable=True)
    facility_id = Column(String(36), nullable=True)  # For INDUSTRY role facility association
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    verifications = relationship("VerificationRecord", back_populates="analyst")
    audit_logs = relationship("AuditLog", back_populates="user")


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_name = Column(String(100), unique=True, nullable=False)  # FIRMS, OSM, CEA, LULC_BHUVAN, SENTINEL_2, LANDSAT, MOSDAC
    adapter_class = Column(String(100), nullable=False)
    category = Column(String(100), default="THERMAL_HOTSPOTS")     # THERMAL_HOTSPOTS, FACILITY_REGISTRY, LULC, MULTISPECTRAL, SATELLITE_ARCHIVE
    endpoint = Column(String(500), nullable=True)
    auth_type = Column(String(50), default="NONE")                 # NONE, MAP_KEY, OAUTH2, API_KEY, BASIC_AUTH
    configured = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    health_status = Column(String(50), default="HEALTHY")          # HEALTHY, DEGRADED, NOT_CONFIGURED, UNAVAILABLE
    last_sync_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    latency_ms = Column(Float, default=0.0)
    record_count = Column(Integer, default=0)
    provenance_info = Column(JSON, default=dict)
    terms_url = Column(String(500), nullable=True)
    metadata_info = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    ingestion_jobs = relationship("DataIngestionJob", back_populates="source")


class DataIngestionJob(Base):
    __tablename__ = "data_ingestion_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_id = Column(String(36), ForeignKey("data_sources.id"), nullable=False)
    job_type = Column(String(50), default="SCHEDULED")  # SCHEDULED, MANUAL, DEMO_SEED
    status = Column(String(50), default="PENDING")      # PENDING, RUNNING, COMPLETED, FAILED
    records_ingested = Column(Integer, default=0)
    records_rejected = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    source = relationship("DataSource", back_populates="ingestion_jobs")


class IndustrialFacility(Base):
    __tablename__ = "industrial_facilities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), index=True, nullable=False)
    facility_type = Column(String(100), nullable=False)  # REFINERY, POWER_PLANT, STEEL_PLANT, CHEMICAL, CEMENT, MINING, TEXTILE, OTHER
    status = Column(String(50), default="KNOWN")        # KNOWN, VERIFIED, REJECTED
    source = Column(String(100), default="OSM")         # OSM, CEA, OFFICIAL_REGISTRY, MANUAL_SURVEY, PROMOTED_CANDIDATE
    source_id = Column(String(100), nullable=True)
    state = Column(String(100), index=True, nullable=False)
    district = Column(String(100), index=True, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    boundary_geojson = Column(JSON, nullable=True)      # Polygon footprint if available
    confidence_score = Column(Float, default=1.0)
    operating_hours = Column(String(50), default="24x7")
    contact_info = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    events = relationship("ThermalEvent", back_populates="facility")
    baselines = relationship("HistoricalBaseline", back_populates="facility")
    facility_baseline = relationship("FacilityBaseline", back_populates="facility", uselist=False)


class CandidateFacility(Base):
    __tablename__ = "candidate_facilities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name_label = Column(String(255), nullable=False)    # e.g., "Candidate-Thermal-Source-GJ-04"
    status = Column(String(50), default="CANDIDATE")    # CANDIDATE, UNDER_REVIEW, PROMOTED, REJECTED
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    state = Column(String(100), index=True, nullable=False)
    district = Column(String(100), nullable=True)
    industrial_context_score = Column(Float, default=0.0)  # 0.0 to 1.0
    persistence_days = Column(Integer, default=1)
    detection_count = Column(Integer, default=1)
    first_detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    evidence_summary = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    events = relationship("ThermalEvent", back_populates="candidate_facility")


class ThermalEvent(Base):
    __tablename__ = "thermal_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_code = Column(String(50), unique=True, index=True, nullable=False)  # e.g. EVT-2026-08-0012
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    bounding_box = Column(JSON, nullable=True)           # [min_lat, min_lon, max_lat, max_lon]
    convex_hull_geojson = Column(JSON, nullable=True)
    
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    detection_count = Column(Integer, default=1)
    
    avg_frp = Column(Float, default=0.0)
    max_frp = Column(Float, default=0.0)
    min_frp = Column(Float, default=0.0)
    frp_variance = Column(Float, default=0.0)
    avg_brightness = Column(Float, default=0.0)
    satellite_count = Column(Integer, default=1)
    
    facility_id = Column(String(36), ForeignKey("industrial_facilities.id"), nullable=True)
    candidate_facility_id = Column(String(36), ForeignKey("candidate_facilities.id"), nullable=True)
    facility_status = Column(String(50), default="UNKNOWN")  # KNOWN, CANDIDATE, UNKNOWN
    nearest_facility_distance_m = Column(Float, nullable=True)
    
    landcover_class = Column(String(100), default="Unknown")
    state = Column(String(100), index=True, nullable=False)
    district = Column(String(100), index=True, nullable=True)
    status = Column(String(50), default="ACTIVE")            # ACTIVE, DORMANT, RESOLVED
    is_demo = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    facility = relationship("IndustrialFacility", back_populates="events")
    candidate_facility = relationship("CandidateFacility", back_populates="events")
    detections = relationship("ThermalDetection", back_populates="event")
    features = relationship("EventFeature", back_populates="event", uselist=False)
    prediction = relationship("ModelPrediction", back_populates="event", uselist=False)
    risk = relationship("RiskScore", back_populates="event", uselist=False)
    alerts = relationship("Alert", back_populates="event")
    verifications = relationship("VerificationRecord", back_populates="event")
    satellite_observations = relationship("SatelliteObservation", back_populates="event")
    reports = relationship("Report", back_populates="event")


class ThermalDetection(Base):
    __tablename__ = "thermal_detections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source = Column(String(50), nullable=False)  # FIRMS_VIIRS, FIRMS_MODIS, S2_SWIR, LANDSAT_TIRS
    sensor = Column(String(50), nullable=False)  # VIIRS_NOAA20, VIIRS_NOAA21, VIIRS_SNPP, MODIS_AQUA, MODIS_TERRA
    satellite = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    acq_timestamp = Column(DateTime, index=True, nullable=False)
    brightness = Column(Float, nullable=True)
    bright_t31 = Column(Float, nullable=True)
    frp = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)      # 0 to 100
    day_night = Column(String(1), default="D")   # D or N
    event_id = Column(String(36), ForeignKey("thermal_events.id"), nullable=True)
    raw_metadata = Column(JSON, default=dict)
    is_demo = Column(Boolean, default=False)

    event = relationship("ThermalEvent", back_populates="detections")


class HistoricalBaseline(Base):
    __tablename__ = "historical_baselines"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    facility_id = Column(String(36), ForeignKey("industrial_facilities.id"), nullable=True)
    grid_cell_id = Column(String(100), index=True, nullable=True)
    mean_frp = Column(Float, default=0.0)
    median_frp = Column(Float, default=0.0)
    std_frp = Column(Float, default=0.0)
    max_historical_frp = Column(Float, default=0.0)
    detection_frequency_monthly = Column(Float, default=0.0)
    day_night_ratio = Column(Float, default=1.0)
    monthly_pattern = Column(JSON, default=dict)
    baseline_status = Column(String(50), default="ESTABLISHED")  # INSUFFICIENT_DATA, PRELIMINARY, ESTABLISHED
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    facility = relationship("IndustrialFacility", back_populates="baselines")


class FacilityBaseline(Base):
    __tablename__ = "facility_baselines"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    facility_id = Column(String(36), ForeignKey("industrial_facilities.id"), unique=True, nullable=False)
    mean_frp = Column(Float, default=0.0)
    median_frp = Column(Float, default=0.0)
    variance_frp = Column(Float, default=0.0)
    max_historical_frp = Column(Float, default=0.0)
    frp_distribution = Column(JSON, default=dict)  # Percentiles e.g. {"p25": 12.0, "p50": 24.5, "p75": 48.0, "p90": 85.0, "p99": 140.0}
    frequency_days = Column(Integer, default=0)
    day_night_ratio = Column(Float, default=1.0)
    status_band = Column(String(50), default="NORMAL")  # NORMAL, ELEVATED, ABNORMAL, CRITICAL (operational flags, not regulatory)
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    facility = relationship("IndustrialFacility", back_populates="facility_baseline")


class EventFeature(Base):
    __tablename__ = "event_features"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), ForeignKey("thermal_events.id"), unique=True, nullable=False)
    
    frp_max = Column(Float, default=0.0)
    frp_avg = Column(Float, default=0.0)
    frp_std = Column(Float, default=0.0)
    bright_max = Column(Float, default=0.0)
    bright_avg = Column(Float, default=0.0)
    
    dist_to_facility_m = Column(Float, default=999999.0)
    dist_to_forest_m = Column(Float, default=999999.0)
    dist_to_agriculture_m = Column(Float, default=999999.0)
    dist_to_settlement_m = Column(Float, default=999999.0)
    dist_to_water_m = Column(Float, default=999999.0)
    dist_to_mine_m = Column(Float, default=999999.0)
    
    landcover_code = Column(Integer, default=0)
    persistence_score = Column(Float, default=0.0)
    recurrence_rate = Column(Float, default=0.0)
    day_night_ratio = Column(Float, default=0.0)
    baseline_deviation_ratio = Column(Float, default=0.0)
    industrial_context_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    event = relationship("ThermalEvent", back_populates="features")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), unique=True, nullable=False)
    algorithm = Column(String(50), nullable=False)  # XGBOOST, RANDOM_FOREST, ISOLATION_FOREST
    metrics = Column(JSON, default=dict)            # accuracy, f1_macro, precision, recall, confusion_matrix
    dataset_version = Column(String(50), default="v1.0")
    is_active = Column(Boolean, default=False)
    artifact_path = Column(String(255), nullable=False)
    trained_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    predictions = relationship("ModelPrediction", back_populates="model_version")


class MLModelRegistry(Base):
    __tablename__ = "ml_model_registry"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), unique=True, nullable=False)
    dataset_version = Column(String(50), nullable=False)
    algorithm = Column(String(50), nullable=False)  # XGBoost, Random Forest, Isolation Forest
    metrics = Column(JSON, default=dict)            # accuracy, macro_f1, brier_score, spatial_holdout_f1, temporal_holdout_f1, confusion_matrix
    artifact_path = Column(String(255), nullable=False)
    status = Column(String(50), default="CANDIDATE")  # TRAINING, VALIDATION, CANDIDATE, APPROVED, ACTIVE, RETIRED
    is_active = Column(Boolean, default=False)
    trained_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


class DatasetRegistry(Base):
    __tablename__ = "dataset_registry"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(150), nullable=False)
    version = Column(String(50), unique=True, nullable=False)
    dataset_type = Column(String(50), nullable=False)  # REAL, WEAKLY_LABELED, HUMAN_VERIFIED, SYNTHETIC, DEMO
    source = Column(String(100), nullable=False)       # NASA_FIRMS_VIIRS, GROUND_TRUTH_SURVEY, CEA_REGISTRY, SYNTHETIC_GENERATOR
    record_count = Column(Integer, default=0)
    verified_count = Column(Integer, default=0)
    class_distribution = Column(JSON, default=dict)
    training_eligible = Column(Boolean, default=True)
    manifest_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ModelPrediction(Base):
    __tablename__ = "model_predictions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), ForeignKey("thermal_events.id"), unique=True, nullable=False)
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=True)
    
    predicted_class = Column(String(100), nullable=False)  # INDUSTRIAL_FIRE, GAS_FLARE, FOREST_FIRE, AGRICULTURAL_BURNING, MINING_ACTIVITY, OTHER_THERMAL, UNCERTAIN
    confidence = Column(Float, default=0.0)
    class_probabilities = Column(JSON, default=dict)
    shap_values = Column(JSON, default=dict)               # Feature attribution waterfall
    explanation_summary = Column(Text, nullable=True)
    predicted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    event = relationship("ThermalEvent", back_populates="prediction")
    model_version = relationship("ModelVersion", back_populates="predictions")


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), ForeignKey("thermal_events.id"), unique=True, nullable=False)
    
    risk_score = Column(Float, default=0.0)                # 0.0 to 100.0
    risk_level = Column(String(50), default="LOW")         # LOW, MODERATE, HIGH, CRITICAL
    
    intensity_subscore = Column(Float, default=0.0)
    abnormality_subscore = Column(Float, default=0.0)
    persistence_subscore = Column(Float, default=0.0)
    exposure_subscore = Column(Float, default=0.0)
    context_subscore = Column(Float, default=0.0)
    
    risk_reasons = Column(JSON, default=list)              # Array of explanatory strings
    evaluated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    event = relationship("ThermalEvent", back_populates="risk")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), ForeignKey("thermal_events.id"), nullable=False)
    alert_level = Column(String(50), default="MODERATE")   # LOW, MODERATE, HIGH, CRITICAL
    alert_type = Column(String(100), nullable=False)       # NEW_HIGH_RISK, ABNORMAL_SPIKE, PERSISTENT_UNKNOWN, CANDIDATE_EMERGENCE, VERIFICATION_NEEDED
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="NEW")             # NEW, ACKNOWLEDGED, UNDER_REVIEW, VERIFIED, RESOLVED
    acknowledged_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    event = relationship("ThermalEvent", back_populates="alerts")


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), ForeignKey("thermal_events.id"), nullable=False)
    analyst_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    original_prediction = Column(String(100), nullable=False)
    verified_label = Column(String(100), nullable=False)
    verification_action = Column(String(50), nullable=False)  # CONFIRM, CORRECT, MARK_UNCERTAIN, FALSE_POSITIVE
    notes = Column(Text, nullable=True)
    evidence_reviewed = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    event = relationship("ThermalEvent", back_populates="verifications")
    analyst = relationship("User", back_populates="verifications")


class SatelliteObservation(Base):
    __tablename__ = "satellite_observations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), ForeignKey("thermal_events.id"), nullable=False)
    satellite = Column(String(50), nullable=False)         # SENTINEL_2, LANDSAT_8, LANDSAT_9
    product_id = Column(String(255), nullable=False)
    acquisition_date = Column(DateTime, nullable=False)
    cloud_cover_percentage = Column(Float, default=0.0)
    bands_available = Column(JSON, default=list)
    preview_url = Column(String(500), nullable=True)
    metadata_info = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    event = relationship("ThermalEvent", back_populates="satellite_observations")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), ForeignKey("thermal_events.id"), nullable=False)
    report_title = Column(String(255), nullable=False)
    generated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    summary_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    event = relationship("ThermalEvent", back_populates="reports")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)           # LOGIN, LOGOUT, VERIFY_EVENT, OVERRIDE_PREDICTION, EXPORT_DATA, GENERATE_REPORT, PROMOTE_MODEL
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="audit_logs")


class ThermalHistory(Base):
    __tablename__ = "thermal_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source = Column(String(50), nullable=False)            # FIRMS_VIIRS_NOAA21, FIRMS_VIIRS_NOAA20, FIRMS_MODIS, LANDSAT_TIRS
    sensor = Column(String(50), nullable=False)            # VIIRS_NOAA21, VIIRS_NOAA20, MODIS_AQUA, MODIS_TERRA, LANDSAT_TIRS
    satellite = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    acq_date = Column(String(20), index=True, nullable=False)
    acq_time = Column(String(10), nullable=False)
    acq_timestamp = Column(DateTime, index=True, nullable=False)
    brightness = Column(Float, nullable=True)
    bright_t31 = Column(Float, nullable=True)
    frp = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    day_night = Column(String(1), default="D")
    processing_type = Column(String(50), default="NRT")    # NRT, STANDARD_SCIENCE
    state = Column(String(100), index=True, nullable=True)
    district = Column(String(100), index=True, nullable=True)
    source_record_id = Column(String(100), nullable=True)
    raw_metadata = Column(JSON, default=dict)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), ForeignKey("thermal_events.id"), nullable=False)
    evidence_type = Column(String(100), nullable=False)     # ANALYST_VERIFICATION, PHOTO_UPLOAD, OFFICIAL_DOCUMENT, SATELLITE_CONTEXT, GIS_EVIDENCE, HISTORICAL_BASELINE, FIELD_NOTE
    evidence_source = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    evidence_data = Column(JSON, default=dict)
    verified = Column(Boolean, default=False)
    verified_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SimulationScenario(Base):
    __tablename__ = "simulation_scenarios"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    scenario_type = Column(String(100), nullable=False)     # INDUSTRIAL_SURGE, GAS_FLARE, FOREST_FIRE, AGRICULTURAL_BURNING, MINING_ACTIVITY, UNKNOWN_PERSISTENT, MULTI_EVENT, MISSING_FACILITY, DELAYED_TELEMETRY, SENSOR_DROPOUT, CLOUD_OBSCURED
    description = Column(Text, nullable=False)
    target_state = Column(String(100), nullable=False)
    target_lat = Column(Float, nullable=False)
    target_lon = Column(Float, nullable=False)
    target_facility = Column(String(255), nullable=True)
    expected_class = Column(String(100), nullable=False)
    expected_risk_level = Column(String(50), nullable=False)
    parameters = Column(JSON, default=dict)
    status = Column(String(50), default="IDLE")             # IDLE, RUNNING, COMPLETED, FAILED
    last_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SatelliteTelemetryLog(Base):
    __tablename__ = "satellite_telemetry_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    satellite_id = Column(String(100), default="AGNI-SAT-01", nullable=False)
    sensor_id = Column(String(100), nullable=False)         # THERMAL_MWIR, OPTICAL_RGB, SWIR_2200NM, MULTISPECTRAL
    scenario_id = Column(String(36), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    frp = Column(Float, default=0.0)
    brightness = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    footprint_geojson = Column(JSON, default=dict)
    status = Column(String(50), default="RECEIVED")         # RECEIVED, PROCESSING, PROCESSED, FAILED
    raw_packet = Column(JSON, default=dict)
    is_simulation = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class MissionTask(Base):
    __tablename__ = "mission_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_code = Column(String(100), unique=True, index=True, nullable=False)
    satellite_id = Column(String(100), default="AGNI-SAT-01", nullable=False)
    target_name = Column(String(255), nullable=False)
    target_lat = Column(Float, nullable=False)
    target_lon = Column(Float, nullable=False)
    sensor_id = Column(String(100), nullable=False)
    priority = Column(String(50), default="NORMAL")          # LOW, NORMAL, HIGH, CRITICAL
    status = Column(String(50), default="SIMULATED_TASK_ACCEPTED")  # SIMULATED_TASK_ACCEPTED, IN_ORBIT_QUEUE, EXECUTING, COMPLETED, FAILED
    tasked_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    scheduled_pass_time = Column(DateTime, nullable=False)
    observed_at = Column(DateTime, nullable=True)
    metadata_info = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

