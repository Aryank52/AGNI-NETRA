"""
AGNI-NETRA Phase 6: Canonical Intelligence Domain Objects
Defines provider-neutral canonical models representing domain concepts across
both Indian operational datasets and future global intelligence sources.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from backend.app.services.intelligence.provenance import SourceProvenance


class ThermalObservation(BaseModel):
    """
    Canonical single-sensor thermal observation (NASA FIRMS, Copernicus SLSTR, ISRO MOSDAC, NOAA GOES).
    Provider-neutral representation with strict validation and full provenance lineage.
    """
    observation_id: str = Field(default_factory=lambda: f"obs-{uuid.uuid4().hex[:8]}", description="Unique detection identifier")
    provider: str = Field("FIRMS", description="Provider identifier (FIRMS, COPERNICUS_SLSTR, ISRO_MOSDAC, NOAA_GOES)")
    dataset: Optional[str] = Field("VIIRS_NRT", description="Specific dataset or product name")
    source_record_id: Optional[str] = Field(None, description="Native source record identifier")
    latitude: float = Field(..., description="WGS84 latitude (-90.0 to 90.0)")
    longitude: float = Field(..., description="WGS84 longitude (-180.0 to 180.0)")
    observation_time: str = Field(..., description="Normalized ISO-8601 UTC observation timestamp")
    acq_timestamp: Optional[str] = Field(None, description="Backward-compatible acquisition timestamp alias")
    radiative_power: float = Field(0.0, description="Fire Radiative Power (FRP) in MW (>= 0.0)")
    frp: Optional[float] = Field(None, description="Backward-compatible FRP alias in MW")
    brightness_temperature: Optional[float] = Field(None, description="Brightness temperature in Kelvin (e.g. 200 - 500K)")
    brightness: Optional[float] = Field(None, description="Backward-compatible brightness temperature alias")
    confidence: float = Field(0.0, description="Detection confidence percentage (0 - 100)")
    sensor: str = Field("VIIRS", description="Sensor name (VIIRS, MODIS, SLSTR, INSAT_TIR, ABI)")
    satellite: Optional[str] = Field(None, description="Platform (NOAA-20, NOAA-21, Sentinel-3A, Terra, Aqua)")
    day_night: str = Field("D", description="Day ('D') or Night ('N')")
    geometry: Optional[Dict[str, Any]] = Field(None, description="WGS84 GeoJSON geometry Point")
    quality_flags: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Raw and processed quality flags")
    source_provenance: Optional[SourceProvenance] = Field(None, description="Detailed source provenance lineage")
    provenance: Optional[SourceProvenance] = Field(None, description="Backward-compatible provenance alias")

    def __init__(self, **data):
        if "observation_id" not in data or not data["observation_id"]:
            data["observation_id"] = f"obs-{uuid.uuid4().hex[:8]}"

        if "observation_time" in data and isinstance(data["observation_time"], datetime):
            data["observation_time"] = data["observation_time"].isoformat()
        if "acq_timestamp" in data and isinstance(data["acq_timestamp"], datetime):
            data["acq_timestamp"] = data["acq_timestamp"].isoformat()

        # Synchronize backward-compatible aliases
        if "acq_timestamp" in data and "observation_time" not in data:
            data["observation_time"] = str(data["acq_timestamp"])
        elif "observation_time" in data and "acq_timestamp" not in data:
            data["acq_timestamp"] = str(data["observation_time"])
        
        if "frp" in data and "radiative_power" not in data:
            data["radiative_power"] = float(data["frp"] or 0.0)
        elif "radiative_power" in data and "frp" not in data:
            data["frp"] = float(data["radiative_power"] or 0.0)

        if "brightness" in data and "brightness_temperature" not in data:
            data["brightness_temperature"] = data["brightness"]
        elif "brightness_temperature" in data and "brightness" not in data:
            data["brightness"] = data["brightness_temperature"]

        if "provenance" in data and "source_provenance" not in data:
            data["source_provenance"] = data["provenance"]
        elif "source_provenance" in data and "provenance" not in data:
            data["provenance"] = data["source_provenance"]

        if "geometry" not in data or not data["geometry"]:
            lat = data.get("latitude", 0.0)
            lon = data.get("longitude", 0.0)
            data["geometry"] = {"type": "Point", "coordinates": [lon, lat]}

        super().__init__(**data)


class ThermalEvent(BaseModel):
    """
    Canonical spatiotemporally clustered and fused thermal event.
    """
    event_id: str = Field(..., description="Event identifier or event code")
    event_code: Optional[str] = Field(None, description="Human-readable event code (e.g., EVT-2026-08-0012)")
    latitude: float = Field(..., description="Centroid latitude")
    longitude: float = Field(..., description="Centroid longitude")
    bounding_box: Optional[List[float]] = Field(None, description="[min_lat, min_lon, max_lat, max_lon]")
    first_seen: str = Field(..., description="ISO-8601 initial detection time")
    last_seen: str = Field(..., description="ISO-8601 latest detection time")
    detection_count: int = Field(1, description="Number of constituent thermal observations")
    avg_frp: float = Field(0.0, description="Average FRP in MW")
    max_frp: float = Field(0.0, description="Peak FRP in MW")
    country: str = Field("India", description="Country name")
    jurisdiction: Optional[str] = Field(None, description="State/Province/Admin level 1")
    district: Optional[str] = Field(None, description="District/County/Admin level 2")
    status: str = Field("ACTIVE", description="ACTIVE, DORMANT, RESOLVED")
    matched_facility_id: Optional[str] = Field(None, description="Linked facility ID if associated")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")

    # Phase 7 Multi-Provider Fusion Fields
    contributing_observations: List[str] = Field(default_factory=list, description="Constituent observation IDs")
    contributing_providers: List[str] = Field(default_factory=list, description="Unique contributing provider names")
    source_agreement: str = Field("SINGLE_SOURCE", description="SINGLE_SOURCE, MULTI_SOURCE_AGREEMENT, SOURCE_CONFLICT, INSUFFICIENT_OVERLAP")
    source_conflicts: List[Dict[str, Any]] = Field(default_factory=list, description="Cross-provider conflict disclosures")


class Facility(BaseModel):
    """
    Canonical industrial facility or candidate asset.
    """
    facility_id: str = Field(..., description="Unique facility identifier")
    name: str = Field(..., description="Facility name")
    facility_type: str = Field(..., description="Standardized type (POWER_PLANT, REFINERY, STEEL_PLANT, etc.)")
    status: str = Field("KNOWN", description="KNOWN, CANDIDATE, VERIFIED, REJECTED")
    country: str = Field("India", description="Country of location")
    state_province: str = Field(..., description="State or administrative region")
    district: Optional[str] = Field(None, description="District or local municipality")
    latitude: Optional[float] = Field(None, description="Representative latitude")
    longitude: Optional[float] = Field(None, description="Representative longitude")
    boundary_geojson: Optional[Dict[str, Any]] = Field(None, description="Footprint polygon if available")
    master_sector: Optional[str] = Field(None, description="High-level sector (Power, Metals, Chemical)")
    nic_code: Optional[str] = Field(None, description="Industrial classification code")
    operating_status: str = Field("OPERATIONAL", description="OPERATIONAL, DORMANT, UNDER_CONSTRUCTION")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")


class MiningSite(BaseModel):
    """
    Canonical mining lease, cluster, or quarry context.
    """
    mining_id: str = Field(..., description="Unique mining record identifier")
    state: str = Field(..., description="State or province")
    district: Optional[str] = Field(None, description="District or administrative zone")
    mineral: str = Field(..., description="Primary mineral commodity (Coal, Iron Ore, Bauxite)")
    lease_count: Optional[int] = Field(None, description="Number of active mining leases")
    lease_area_ha: Optional[float] = Field(None, description="Total lease area in hectares")
    potential_tier: Optional[str] = Field(None, description="High, Medium, Low mining potential")
    sector: Optional[str] = Field("PUBLIC", description="PUBLIC, PRIVATE")
    reference_year: int = Field(2024, description="Reference publication year")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")


class PowerFacility(BaseModel):
    """
    Canonical utility-scale power generation asset.
    """
    power_id: str = Field(..., description="Unique power plant record identifier")
    plant_name: str = Field(..., description="Official power station name")
    prime_mover: str = Field(..., description="Prime mover type (THERMAL, HYDRO, NUCLEAR, GAS)")
    installed_capacity_mw: Optional[float] = Field(None, description="Installed generation capacity (MW)")
    organisation: Optional[str] = Field(None, description="Operating utility / ownership body")
    state: str = Field(..., description="State or province")
    region: Optional[str] = Field(None, description="Grid region (NR, WR, SR, ER, NER)")
    commissioning_year: Optional[int] = Field(None, description="Year of commissioning")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")


class AdministrativeArea(BaseModel):
    """
    Canonical geopolitical administrative boundary.
    """
    admin_id: str = Field(..., description="Unique administrative boundary identifier")
    admin_level: int = Field(..., description="0=Country, 1=State/Province, 2=District, 3=Subdistrict")
    name: str = Field(..., description="Administrative unit name")
    parent_id: Optional[str] = Field(None, description="Parent administrative unit ID")
    country_code: str = Field("IN", description="ISO 3166-1 alpha-2 or alpha-3 country code")
    boundary_geojson: Optional[Dict[str, Any]] = Field(None, description="Boundary polygon/multipolygon")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")


class LandCover(BaseModel):
    """
    Canonical Land Use / Land Cover (LULC) context.
    """
    lulc_id: str = Field(..., description="Unique LULC feature or grid identifier")
    latitude: float = Field(..., description="Centroid latitude")
    longitude: float = Field(..., description="Centroid longitude")
    canonical_class: str = Field(..., description="Standard class (Industrial, Forest, Agricultural, Water, Barren)")
    original_class_name: Optional[str] = Field(None, description="Source dataset class label")
    industrial_compatible: bool = Field(False, description="Whether LULC permits industrial activity")
    resolution_m: Optional[float] = Field(30.0, description="Spatial resolution in meters")
    reference_year: Optional[int] = Field(None, description="LULC observation year")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")


class ProtectedArea(BaseModel):
    """
    Canonical ecological conservation or protected zone.
    """
    pa_id: str = Field(..., description="Unique protected area identifier")
    name: str = Field(..., description="Protected area designation name")
    category: str = Field(..., description="NATIONAL_PARK, WILDLIFE_SANCTUARY, BIOSPHERE_RESERVE, ESZ")
    state: str = Field(..., description="State or province")
    buffer_distance_km: float = Field(10.0, description="Regulatory buffer threshold (default 10km)")
    boundary_geojson: Optional[Dict[str, Any]] = Field(None, description="Boundary geometry if available")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")


class HistoricalBaseline(BaseModel):
    """
    Canonical longitudinal thermal baseline distribution.
    """
    baseline_id: str = Field(..., description="Baseline record identifier")
    target_id: str = Field(..., description="Facility ID or Grid Cell ID")
    target_type: str = Field("FACILITY", description="FACILITY or GRID_CELL")
    mean_frp: float = Field(0.0, description="Baseline mean FRP")
    median_frp: float = Field(0.0, description="Baseline median FRP")
    std_frp: float = Field(0.0, description="Standard deviation")
    p90_frp: float = Field(0.0, description="90th percentile FRP")
    p99_frp: float = Field(0.0, description="99th percentile FRP")
    observation_count: int = Field(0, description="Number of historical samples")
    baseline_status: str = Field("STABLE", description="STABLE, HIGH_VOLATILITY, INSUFFICIENT_HISTORY")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")


class RiskAssessment(BaseModel):
    """
    Canonical authoritative 5-factor risk score assessment (0-100).
    Preserves exact formula: Persistence(25%) + Radiative(25%) + Proximity(20%) + LandUse(15%) + History(15%).
    """
    assessment_id: str = Field(..., description="Risk assessment identifier")
    event_id: str = Field(..., description="Associated thermal event ID")
    risk_score: float = Field(..., description="Composite risk score (0.0 - 100.0)")
    severity_level: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    factors: Dict[str, float] = Field(default_factory=dict, description="Component factor scores")
    model_version: str = Field("xgb-v3.0-real-candidate", description="ML / Risk model version")
    confidence: float = Field(1.0, description="Assessment confidence")
    calculation_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Calculation timestamp"
    )
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")


class Alert(BaseModel):
    """
    Canonical industrial thermal alert object.
    """
    alert_id: str = Field(..., description="Unique alert identifier")
    event_id: str = Field(..., description="Associated event ID")
    severity: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    trigger_rule: str = Field(..., description="Threshold or heuristic triggering the alert")
    status: str = Field("ACTIVE", description="ACTIVE, ACKNOWLEDGED, RESOLVED, SUPPRESSED")
    created_at: str = Field(..., description="Alert generation timestamp")
    notification_sent: bool = Field(False, description="Whether notification was dispatched")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")


class Evidence(BaseModel):
    """
    Canonical atomic epistemic evidence item supporting an investigation.
    """
    evidence_id: str = Field(..., description="Evidence item identifier")
    epistemic_category: str = Field(..., description="THERMAL, SPATIAL, REGULATORY, BASELINE, ML_PREDICTION")
    claim: str = Field(..., description="Human-readable claim or finding")
    strength: str = Field("SUPPORTING", description="STRONG_SUPPORT, SUPPORTING, WEAK, CONFLICTING")
    observation_time: Optional[str] = Field(None, description="When physical event occurred")
    retrieval_time: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="When evidence was gathered"
    )
    provenance: Optional[SourceProvenance] = Field(None, description="Originating source provenance")


class Investigation(BaseModel):
    """
    Canonical investigation case representation with provider and coverage tracking.
    """
    investigation_id: str = Field(..., description="Case identifier (e.g., INV-20260910-A1B2C3)")
    target_event_id: Optional[str] = Field(None, description="Target thermal event ID")
    status: str = Field("ACTIVE", description="ACTIVE, COMPLETED, CLOSED, REQUIRES_HUMAN_REVIEW")
    coverage_profile: str = Field("INDIA", description="INDIA or GLOBAL")
    sources_used: List[str] = Field(default_factory=list, description="List of providers utilized")
    missing_sources: List[str] = Field(default_factory=list, description="Unconfigured or absent sources")
    partial_sources: List[str] = Field(default_factory=list, description="Partial coverage sources")
    evidence_items: List[Evidence] = Field(default_factory=list, description="Attached evidence items")
    verification_status: str = Field("NOT_REQUIRED", description="NOT_REQUIRED, REQUIRES_HUMAN_REVIEW, VERIFIED")


class Verification(BaseModel):
    """
    Canonical Human-In-The-Loop (HITL) verification record.
    """
    verification_id: str = Field(..., description="Unique verification identifier")
    event_id: str = Field(..., description="Associated event ID")
    analyst_id: Optional[str] = Field(None, description="Reviewing analyst identifier")
    status: str = Field("PENDING", description="PENDING, VERIFIED, REJECTED, ESCALATED")
    review_tier: str = Field("TIER_1", description="TIER_1, TIER_2_SUPERVISORY, TIER_3_COMMAND")
    notes: Optional[str] = Field(None, description="Analyst grounding and justification notes")
    verified_at: Optional[str] = Field(None, description="Timestamp of review completion")
    provenance: Optional[SourceProvenance] = Field(None, description="Audit provenance")
