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
    baseline_status: str = Field("STABLE", description="STABLE, HIGH_VOLATILITY, INSUFFICIENT_HISTORY, ESTABLISHED, NO_BASELINE")
    expected_frequency: float = Field(0.0, description="Expected monthly or annual detection frequency")
    recent_frequency: float = Field(0.0, description="Recent 30-day detection frequency")
    day_night_ratio: float = Field(1.0, description="Historical day-night ratio")
    multi_scale_metrics: Dict[str, Any] = Field(default_factory=dict, description="Multi-scale temporal window metrics")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")

    def __init__(self, **data):
        if "sample_count" in data and "observation_count" not in data:
            data["observation_count"] = data["sample_count"]
        if "sample_size" in data and "observation_count" not in data:
            data["observation_count"] = data["sample_size"]
        if "mean_frp_mw" in data and "mean_frp" not in data:
            data["mean_frp"] = data["mean_frp_mw"]
        if "std_frp_mw" in data and "std_frp" not in data:
            data["std_frp"] = data["std_frp_mw"]
        if "event_id" in data and "target_id" not in data:
            data["target_id"] = str(data["event_id"])
        super().__init__(**data)


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


# ============================================================================
# Phase 8: Canonical Global Context Models
# ============================================================================

class ContextProvenance(SourceProvenance):
    """
    Context-specific extension of canonical SourceProvenance.
    """
    context_domain: Optional[str] = Field(None, description="FACILITIES, POWER, MINING, LAND_COVER, PROTECTED_AREAS, ADMINISTRATIVE, ENVIRONMENTAL")


class ContextObservation(BaseModel):
    """
    Canonical provider-neutral contextual intelligence record.
    Supports multi-domain spatial and environmental context associating with thermal events.
    """
    context_id: str = Field(default_factory=lambda: f"CTX-{uuid.uuid4().hex[:8].upper()}", description="Unique contextual record identifier")
    context_domain: str = Field(..., description="FACILITIES, POWER, MINING, LAND_COVER, PROTECTED_AREAS, ADMINISTRATIVE, ENVIRONMENTAL")
    provider: str = Field(..., description="Provider name (e.g. OSM, CEA, IBM_MINING, ISRO_BHUVAN, FSI, ADMIN_BOUNDARIES, PARIVESH)")
    dataset: str = Field(..., description="Specific dataset or catalog identifier")
    source_record_id: Optional[str] = Field(None, description="Native source database key")
    country: str = Field("India", description="Country of contextual feature")
    jurisdiction: Optional[str] = Field(None, description="State, province, or primary administrative unit")
    latitude: Optional[float] = Field(None, description="WGS84 latitude")
    longitude: Optional[float] = Field(None, description="WGS84 longitude")
    geometry: Optional[Dict[str, Any]] = Field(None, description="GeoJSON geometry if available")
    observation_time: Optional[str] = Field(None, description="Observation or acquisition timestamp")
    effective_time: Optional[str] = Field(None, description="Publication or gazette effective date")
    source_resolution: Optional[str] = Field(None, description="Spatial resolution or scale")
    confidence: Optional[float] = Field(None, description="Provider-reported confidence (0-100)")
    distance_meters: Optional[float] = Field(None, description="Geodesic distance to target event epicenter (m)")
    spatial_relationship: Optional[str] = Field(None, description="DIRECT_OVERLAP, VERY_NEAR, NEAR, DISTANT, NO_RELEVANT_CONTEXT")
    spatial_relevance: Optional[str] = Field("MEDIUM", description="HIGH, MEDIUM, LOW, NEGLIGIBLE")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Domain-specific key-value attributes")
    provenance: Optional[SourceProvenance] = Field(None, description="Canonical source provenance metadata")
    limitations: Optional[str] = Field(None, description="Data caveats or coverage constraints")
    coverage_status: str = Field("AVAILABLE", description="AVAILABLE, PARTIAL, NOT_CONFIGURED")


class FacilityContext(ContextObservation):
    """Canonical industrial facility context."""
    context_domain: str = Field("FACILITIES", description="FACILITIES")
    facility_name: Optional[str] = Field(None, description="Facility or complex name")
    facility_type: Optional[str] = Field(None, description="Industrial classification (e.g. REFINERY, STEEL_PLANT)")
    sector: Optional[str] = Field(None, description="Industrial sector")
    operating_status: Optional[str] = Field("OPERATIONAL", description="OPERATIONAL, DORMANT, UNDER_CONSTRUCTION")


class PowerContext(ContextObservation):
    """Canonical power generation infrastructure context."""
    context_domain: str = Field("POWER", description="POWER")
    plant_name: Optional[str] = Field(None, description="Power station designation")
    prime_mover: Optional[str] = Field(None, description="Generation type: THERMAL, HYDRO, NUCLEAR, GAS, SOLAR, WIND")
    installed_capacity_mw: Optional[float] = Field(None, description="Capacity in MW")
    organisation: Optional[str] = Field(None, description="Utility or operating entity")


class MiningContext(ContextObservation):
    """Canonical mineral concession and extraction context."""
    context_domain: str = Field("MINING", description="MINING")
    block_name: Optional[str] = Field(None, description="Mining lease or block designation")
    lease_name: Optional[str] = Field(None, description="Lease name alias")
    mineral: Optional[str] = Field(None, description="Primary mineral commodity")
    lease_status: Optional[str] = Field(None, description="ACTIVE, AUCTIONED, EXPIRED")
    lease_area_hectares: Optional[float] = Field(None, description="Lease area in hectares")

    def __init__(self, **data):
        if "lease_name" in data and "block_name" not in data:
            data["block_name"] = data["lease_name"]
        elif "block_name" in data and "lease_name" not in data:
            data["lease_name"] = data["block_name"]
        super().__init__(**data)


class LandCoverContext(ContextObservation):
    """Canonical thematic Land Use / Land Cover (LULC) context."""
    context_domain: str = Field("LAND_COVER", description="LAND_COVER")
    canonical_class: Optional[str] = Field(None, description="Standard class: Industrial, Forest, Agricultural, Water, Barren")
    primary_class: Optional[str] = Field(None, description="Primary LULC class alias")
    secondary_class: Optional[str] = Field(None, description="Secondary LULC class")
    resolution_m: Optional[float] = Field(None, description="Resolution in meters")
    is_industrial_compatible: Optional[bool] = Field(None, description="Whether land cover permits thermal/industrial operations")

    def __init__(self, **data):
        if "primary_class" in data and "canonical_class" not in data:
            data["canonical_class"] = data["primary_class"]
        elif "canonical_class" in data and "primary_class" not in data:
            data["primary_class"] = data["canonical_class"]
        super().__init__(**data)


class ProtectedAreaContext(ContextObservation):
    """Canonical ecological reserve and protected area context."""
    context_domain: str = Field("PROTECTED_AREAS", description="PROTECTED_AREAS")
    pa_name: Optional[str] = Field(None, description="Sanctuary or reserve designation")
    pa_category: Optional[str] = Field(None, description="NATIONAL_PARK, WILDLIFE_SANCTUARY, BIOSPHERE_RESERVE, ESZ")
    buffer_distance_km: Optional[float] = Field(10.0, description="Statutory buffer perimeter in km")


class AdministrativeContext(ContextObservation):
    """Canonical geopolitical administrative hierarchy context."""
    context_domain: str = Field("ADMINISTRATIVE", description="ADMINISTRATIVE")
    admin_level: Optional[int] = Field(None, description="0=Country, 1=State, 2=District, 3=Subdistrict")
    admin_name: Optional[str] = Field(None, description="Administrative boundary designation")
    state: Optional[str] = Field(None, description="State/Province name")
    district: Optional[str] = Field(None, description="District name")


class EnvironmentalContext(ContextObservation):
    """Canonical statutory environmental clearance and compliance context."""
    context_domain: str = Field("ENVIRONMENTAL", description="ENVIRONMENTAL")
    proposal_id: Optional[str] = Field(None, description="Statutory filing or proposal identifier")
    proposal_no: Optional[str] = Field(None, description="Proposal number alias")
    project_name: Optional[str] = Field(None, description="Project title in clearance registry")
    ec_category: Optional[str] = Field(None, description="EIA Category (A, B1, B2)")
    category: Optional[str] = Field(None, description="Category alias")
    decision_date: Optional[str] = Field(None, description="Date of clearance determination")
    compliance_status: Optional[str] = Field(None, description="APPROVED, REJECTED, PENDING")
    status: Optional[str] = Field(None, description="Status alias")

    def __init__(self, **data):
        if "category" in data and "ec_category" not in data:
            data["ec_category"] = data["category"]
        elif "ec_category" in data and "category" not in data:
            data["category"] = data["ec_category"]
        if "status" in data and "compliance_status" not in data:
            data["compliance_status"] = data["status"]
        elif "compliance_status" in data and "status" not in data:
            data["status"] = data["compliance_status"]
        if "proposal_no" in data and "proposal_id" not in data:
            data["proposal_id"] = data["proposal_no"]
        elif "proposal_id" in data and "proposal_no" not in data:
            data["proposal_no"] = data["proposal_id"]
        super().__init__(**data)


class ContextRelationship(BaseModel):
    """
    Deterministic spatial and semantic relationship between a thermal event and a contextual entity.
    """
    relationship_id: str = Field(default_factory=lambda: f"REL-{uuid.uuid4().hex[:8].upper()}")
    event_id: str = Field(..., description="Target thermal event ID")
    context_id: str = Field(..., description="Associated contextual record ID")
    domain: str = Field(..., description="Context domain (FACILITIES, POWER, MINING, etc.)")
    category: str = Field(..., description="DIRECT_OVERLAP, VERY_NEAR, NEAR, DISTANT, NO_RELEVANT_CONTEXT")
    distance_m: float = Field(..., description="Distance in meters")
    spatial_relevance: str = Field("MEDIUM", description="HIGH, MEDIUM, LOW, NEGLIGIBLE")
    is_supporting: bool = Field(False, description="Whether this relationship supports the operational hypothesis")
    is_conflicting: bool = Field(False, description="Whether this relationship conflicts with other evidence")
    details: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic and contextual detail payload")


class ContextCoverage(BaseModel):
    """
    Deterministic coverage disclosure for an intelligence context domain.
    """
    domain: str = Field(..., description="FACILITIES, POWER, MINING, LAND_COVER, PROTECTED_AREAS, ADMINISTRATIVE, ENVIRONMENTAL")
    provider: str = Field(..., description="Provider name")
    dataset: str = Field(..., description="Dataset name")
    geographic_coverage: str = Field("GLOBAL", description="GLOBAL, REGIONAL, COUNTRY")
    status: str = Field("AVAILABLE", description="AVAILABLE, PARTIAL, NOT_CONFIGURED")
    availability: str = Field("AVAILABLE", description="AVAILABLE, DEGRADED, UNAVAILABLE, NOT_CONFIGURED")
    resolution: Optional[str] = Field(None, description="Nominal resolution or scale")
    limitations: Optional[str] = Field(None, description="Known operational limitations")
    last_health_state: str = Field("AVAILABLE", description="Health check outcome")
    is_global: bool = Field(False, description="Whether coverage is global")
    coverage_status: Optional[str] = Field(None, description="Alias for status")
    geographic_scope: Optional[str] = Field(None, description="Alias for geographic_coverage")

    def __init__(self, **data):
        if "coverage_status" in data and "status" not in data:
            data["status"] = data["coverage_status"]
        if "status" in data and "coverage_status" not in data:
            data["coverage_status"] = data["status"]
        if "geographic_scope" in data and "geographic_coverage" not in data:
            data["geographic_coverage"] = data["geographic_scope"]
        if "geographic_coverage" in data and "geographic_scope" not in data:
            data["geographic_scope"] = data["geographic_coverage"]
        super().__init__(**data)
        if self.coverage_status is None:
            object.__setattr__(self, "coverage_status", self.status)
        if self.geographic_scope is None:
            object.__setattr__(self, "geographic_scope", self.geographic_coverage)


# =====================================================================
# PHASE 9: CANONICAL TEMPORAL PATTERN & HISTORICAL BASELINE MODELS
# =====================================================================

class TemporalObservation(BaseModel):
    """
    Canonical normalized temporal observation record from a satellite or archive provider.
    """
    observation_id: str = Field(default_factory=lambda: f"TOBS-{uuid.uuid4().hex[:8].upper()}")
    event_id: Optional[str] = Field(None, description="Associated event ID")
    provider: str = Field(..., description="NASA_FIRMS, COPERNICUS_SLSTR, ISRO_MOSDAC, etc.")
    dataset: str = Field(..., description="Archive or sensor dataset name")
    source_record_id: Optional[str] = Field(None, description="Source provider detection ID")
    country: str = Field("India", description="Country")
    jurisdiction: Optional[str] = Field(None, description="Jurisdiction or state")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    observation_time: str = Field(..., description="Observation acquisition timestamp ISO8601")
    effective_time: Optional[str] = Field(None, description="Effective processing timestamp ISO8601")
    frp_mw: float = Field(0.0, description="Fire Radiative Power in MW")
    brightness_k: Optional[float] = Field(None, description="Brightness temperature in Kelvin")
    day_night: str = Field("D", description="D (Day) or N (Night)")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")

    def __init__(self, **data):
        if "timestamp" in data and "observation_time" not in data:
            data["observation_time"] = data["timestamp"]
        if "source" in data and "provider" not in data:
            data["provider"] = data["source"]
        if "satellite" in data and "dataset" not in data:
            data["dataset"] = data["satellite"]
        super().__init__(**data)


class PersistenceAssessment(BaseModel):
    """
    Deterministic quantitative and qualitative persistence assessment.
    5 Tiers: EPHEMERAL, SHORT_DURATION, PERSISTENT, REPEATED, LONG_TERM_RECURRENT.
    """
    event_id: str = Field(..., description="Target thermal event ID")
    persistence_category: str = Field(..., description="EPHEMERAL, SHORT_DURATION, PERSISTENT, REPEATED, LONG_TERM_RECURRENT")
    tier: Optional[str] = Field(None, description="Alias for persistence_category")
    persistence_score: float = Field(..., description="Normalized persistence score 0.0 - 10.0")
    active_time_span_hours: float = Field(0.0, description="Total active duration in hours")
    active_days_count: int = Field(0, description="Distinct active calendar days")
    observation_count: int = Field(0, description="Total observation passes")
    observation_gaps_avg_hours: float = Field(0.0, description="Average gap between observations in hours")
    temporal_density: float = Field(0.0, description="Observations per active day")
    supporting_providers: List[str] = Field(default_factory=list, description="Providers confirming persistence")
    confidence: float = Field(1.0, description="Confidence in persistence calculation")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")

    def __init__(self, **data):
        if "tier" in data and "persistence_category" not in data:
            data["persistence_category"] = data["tier"]
        elif "persistence_category" in data and ("tier" not in data or data["tier"] is None):
            data["tier"] = data["persistence_category"]
        super().__init__(**data)


class RecurrenceAssessment(BaseModel):
    """
    Deterministic recurrence intelligence across multi-scale temporal windows.
    """
    event_id: str = Field(..., description="Target thermal event ID")
    is_recurring: bool = Field(False, description="Whether thermal activity recurs at location")
    recurrence_category: str = Field("NON_RECURRENT", description="NON_RECURRENT, RECURRENT, HIGHLY_RECURRENT, SEASONAL_RECURRENT")
    recurrence_count: int = Field(0, description="Distinct recurrent episodes / clusters")
    recurrence_interval_days: float = Field(0.0, description="Average recurrence interval in days")
    recurrence_regularity: float = Field(0.0, description="Regularity score 0.0 to 1.0")
    recent_recurrence_count: int = Field(0, description="Recurrence episodes in last 30 days")
    historical_recurrence_count: int = Field(0, description="Recurrence episodes across historical archive")
    seasonal_recurrence: bool = Field(False, description="Whether recurrence follows seasonal cadence")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")


class TemporalPattern(BaseModel):
    """
    Multi-scale temporal behavior pattern including seasonality and day/night split.
    """
    event_id: str = Field(..., description="Target thermal event ID")
    seasonality: str = Field("INSUFFICIENT_DATA", description="SEASONAL, NON_SEASONAL, INSUFFICIENT_DATA")
    seasonal_peak_months: List[str] = Field(default_factory=list, description="Peak activity months")
    day_night_behavior: str = Field("MIXED", description="PREDOMINANTLY_DAYTIME, PREDOMINANTLY_NIGHTTIME, MIXED, INSUFFICIENT_OBSERVATIONS")
    day_count: int = Field(0, description="Daytime pass count")
    night_count: int = Field(0, description="Nighttime pass count")
    day_night_ratio: float = Field(1.0, description="Night to Day ratio")
    duration_pattern: str = Field("INTERMITTENT", description="CONTINUOUS, INTERMITTENT, TRANSIENT, CYCLIC")
    clustering_over_time: str = Field("BURST", description="STEADY, BURST, SPORADIC")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")


class TemporalAnomaly(BaseModel):
    """
    Comparison against historical baseline distribution. Kept independent from model-based Isolation Forest.
    """
    event_id: str = Field(..., description="Target thermal event ID")
    deviation_status: str = Field("NORMAL", description="NORMAL, ELEVATED, HIGHLY_ELEVATED, NOVEL, INSUFFICIENT_BASELINE")
    z_score: float = Field(0.0, description="Statistical z-score against historical baseline mean")
    deviation_ratio: float = Field(1.0, description="Ratio of observed FRP to baseline mean FRP")
    model_anomaly_status: str = Field("NORMAL", description="Isolation Forest anomaly status")
    is_temporal_anomaly: bool = Field(False, description="True if temporally elevated/abnormal")
    explanation: str = Field("", description="Explainable diagnostic rationale")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")


class TemporalEvidence(BaseModel):
    """
    Comprehensive temporal evidence assessment with calibrated strength and uncertainty.
    """
    event_id: str = Field(..., description="Target thermal event ID")
    evidence_strength: str = Field("MODERATE", description="STRONG, MODERATE, LIMITED, INSUFFICIENT")
    temporal_uncertainty: str = Field("KNOWN", description="KNOWN, UNCERTAIN, MISSING, CONFLICTING")
    observation_count: int = Field(0, description="Total observations analyzed")
    baseline_sample_size: int = Field(0, description="Samples in historical baseline")
    active_time_span: str = Field("", description="Human-readable duration description")
    limiting_factors: List[str] = Field(default_factory=list, description="Factors creating temporal uncertainty")
    what_could_reduce_uncertainty: List[str] = Field(default_factory=list, description="Actionable observations that would reduce uncertainty")
    missing_historical_sources: List[str] = Field(default_factory=list, description="Unconfigured or missing historical archives")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")


class TemporalCoverage(BaseModel):
    """
    Deterministic disclosure of temporal provider archive availability.
    """
    provider: str = Field(..., description="Provider name")
    dataset: str = Field(..., description="Dataset or archive name")
    period_covered: str = Field(..., description="Historical range covered")
    geographic_coverage: str = Field("GLOBAL", description="GLOBAL, REGIONAL, COUNTRY")
    temporal_resolution: str = Field("12_HOURS", description="Nominal revisit rate")
    observation_count: int = Field(0, description="Observations available in scope")
    limitations: Optional[str] = Field(None, description="Known temporal limitations")
    status: str = Field("AVAILABLE", description="AVAILABLE, PARTIAL, INSUFFICIENT, NOT_CONFIGURED")


# ==============================================================================
# Phase 10 Canonical Environmental Intelligence & Cross-Modal Verification Models
# ==============================================================================

class EnvironmentalObservation(BaseModel):
    """
    Base canonical environmental observation supporting meteorological, atmospheric,
    and ecological measurements with strict provenance lineage.
    """
    observation_id: str = Field(default_factory=lambda: f"ENV-{uuid.uuid4().hex[:8].upper()}")
    provider: str = Field(..., description="Provider identifier (e.g. ECMWF, GFS, IMD, NASA)")
    dataset: str = Field(..., description="Dataset or model product name")
    source_record_id: Optional[str] = Field(None, description="Native source record identifier")
    country: str = Field("India", description="Country name")
    jurisdiction: Optional[str] = Field(None, description="State/Province/Admin level 1")
    latitude: float = Field(..., description="WGS84 latitude")
    longitude: float = Field(..., description="WGS84 longitude")
    geometry: Optional[Dict[str, Any]] = Field(None, description="GeoJSON Point representation")
    observation_time: str = Field(..., description="Observation timestamp ISO8601")
    effective_time: Optional[str] = Field(None, description="Effective processing timestamp ISO8601")
    spatial_resolution: Optional[str] = Field(None, description="Spatial resolution (e.g. 0.25 deg, 1 km, 10m)")
    temporal_resolution: Optional[str] = Field(None, description="Temporal cadence (e.g. 1 hour, 3 hours, daily)")
    measurement: Optional[Union[float, str, Dict[str, Any]]] = Field(None, description="Primary measurement value")
    unit: Optional[str] = Field(None, description="Measurement unit")
    quality: str = Field("HIGH", description="Data quality classification")
    confidence: float = Field(1.0, description="Confidence score 0.0 - 1.0")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance lineage")
    limitations: Optional[str] = Field(None, description="Known observation limitations")

    def __init__(self, **data):
        if "geometry" not in data or not data["geometry"]:
            lat = data.get("latitude", 0.0)
            lon = data.get("longitude", 0.0)
            data["geometry"] = {"type": "Point", "coordinates": [lon, lat]}
        super().__init__(**data)


class WeatherObservation(BaseModel):
    """
    Canonical meteorological observation (surface temperature, humidity, wind vectors, precipitation).
    """
    observation_id: str = Field(default_factory=lambda: f"WX-{uuid.uuid4().hex[:8].upper()}")
    provider: str = Field("ECMWF_ERA5", description="Meteorological provider")
    dataset: str = Field("SURFACE_REANALYSIS", description="Dataset product name")
    source_record_id: Optional[str] = None
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    observation_time: str = Field(..., description="Observation timestamp ISO8601")
    retrieval_time: Optional[str] = Field(None, description="Retrieval timestamp ISO8601")
    source_type: str = Field("TEST_FIXTURE", description="REAL_PROVIDER, LOCAL_DATASET, TEST_FIXTURE, SIMULATION, UNAVAILABLE, UNVERIFIED")
    evidence_nature: str = Field("OBSERVED", description="OBSERVED, DERIVED, INFERRED, MISSING, CONFLICTING, TEST_FIXTURE, SIMULATION, UNAVAILABLE")
    spatial_resolution: Optional[str] = Field(None, description="Spatial resolution")
    temporal_resolution: Optional[str] = Field(None, description="Temporal cadence")
    temperature_c: Optional[float] = Field(None, description="2-meter ambient temperature in Celsius")
    relative_humidity_pct: Optional[float] = Field(None, description="Relative humidity percentage (0 - 100)")
    surface_pressure_hpa: Optional[float] = Field(None, description="Surface pressure in hPa")
    wind_speed_ms: Optional[float] = Field(None, description="10-meter wind speed in m/s")
    wind_direction_deg: Optional[float] = Field(None, description="10-meter wind direction in meteorological degrees (0-360)")
    wind_gust_ms: Optional[float] = Field(None, description="Peak wind gust in m/s")
    precipitation_rate_mmh: Optional[float] = Field(None, description="Precipitation rate in mm/hour")
    cloud_cover_pct: Optional[float] = Field(None, description="Total cloud cover percentage (0 - 100)")
    dew_point_c: Optional[float] = Field(None, description="Dew point temperature in Celsius")
    quality: str = Field("HIGH", description="Quality rating")
    provenance: Optional[SourceProvenance] = Field(None, description="Provenance lineage")
    limitations: Optional[str] = Field(None, description="Measurement limitations")


class AtmosphericObservation(BaseModel):
    """
    Canonical atmospheric composition observation (Aerosol Optical Depth, CO, SO2, NO2).
    """
    observation_id: str = Field(default_factory=lambda: f"ATM-{uuid.uuid4().hex[:8].upper()}")
    provider: str = Field("COPERNICUS_CAMS", description="Atmospheric provider")
    dataset: str = Field("ATMOSPHERIC_COMPOSITION", description="Dataset product name")
    source_record_id: Optional[str] = None
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    observation_time: str = Field(..., description="Observation timestamp ISO8601")
    retrieval_time: Optional[str] = Field(None, description="Retrieval timestamp ISO8601")
    source_type: str = Field("TEST_FIXTURE", description="REAL_PROVIDER, LOCAL_DATASET, TEST_FIXTURE, SIMULATION, UNAVAILABLE, UNVERIFIED")
    evidence_nature: str = Field("OBSERVED", description="OBSERVED, DERIVED, INFERRED, MISSING, CONFLICTING, TEST_FIXTURE, SIMULATION, UNAVAILABLE")
    spatial_resolution: Optional[str] = Field(None, description="Spatial resolution")
    temporal_resolution: Optional[str] = Field(None, description="Temporal cadence")
    aod: Optional[float] = Field(None, description="Aerosol Optical Depth at 550nm")
    co_ppm: Optional[float] = Field(None, description="Carbon Monoxide volume mixing ratio in ppm")
    no2_umol_m2: Optional[float] = Field(None, description="Nitrogen Dioxide tropospheric column in umol/m2")
    so2_umol_m2: Optional[float] = Field(None, description="Sulfur Dioxide total column in umol/m2")
    aqi: Optional[int] = Field(None, description="Air Quality Index")
    surface_visibility_km: Optional[float] = Field(None, description="Horizontal visibility in kilometers")
    quality: str = Field("HIGH", description="Quality rating")
    provenance: Optional[SourceProvenance] = Field(None, description="Provenance lineage")
    limitations: Optional[str] = Field(None, description="Measurement limitations")


class CloudCondition(BaseModel):
    """
    Cloud condition & optical observability assessment.
    Crucially separates ACTIVITY ABSENCE from OBSERVATION ABSENCE.
    """
    observation_id: str = Field(default_factory=lambda: f"CLD-{uuid.uuid4().hex[:8].upper()}")
    provider: str = Field("METEOROLOGICAL_SATELLITE", description="Observing provider")
    dataset: str = Field("CLOUD_MASK", description="Dataset product")
    source_record_id: Optional[str] = None
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    observation_time: str = Field(..., description="Observation timestamp ISO8601")
    retrieval_time: Optional[str] = Field(None, description="Retrieval timestamp ISO8601")
    source_type: str = Field("TEST_FIXTURE", description="REAL_PROVIDER, LOCAL_DATASET, TEST_FIXTURE, SIMULATION, UNAVAILABLE, UNVERIFIED")
    evidence_nature: str = Field("OBSERVED", description="OBSERVED, DERIVED, INFERRED, MISSING, CONFLICTING, TEST_FIXTURE, SIMULATION, UNAVAILABLE")
    spatial_resolution: Optional[str] = Field(None, description="Spatial resolution")
    temporal_resolution: Optional[str] = Field(None, description="Temporal cadence")
    cloud_cover_pct: float = Field(0.0, description="Total cloud fraction (0-100)")
    cloud_type: Optional[str] = Field(None, description="Cirrus, Cumulus, Stratus, Deep Convective, Clear")
    cloud_base_altitude_m: Optional[float] = Field(None, description="Base height above ground in meters")
    optical_opacity: float = Field(0.0, description="Optical thickness/opacity (0.0 clear to 1.0 fully opaque)")
    visibility_attenuation_factor: float = Field(1.0, description="Atmospheric transmissivity factor (0.0 - 1.0)")
    limits_optical_observation: bool = Field(False, description="True if clouds obscure optical surface sensing")
    limits_thermal_observation: bool = Field(False, description="True if thick clouds attenuate thermal infrared signals")
    is_activity_absence: bool = Field(False, description="False indicates clouds cause observation absence, NOT thermal inactivity")
    quality: str = Field("HIGH", description="Quality rating")
    provenance: Optional[SourceProvenance] = Field(None, description="Provenance lineage")
    limitations: Optional[str] = Field(None, description="Limitations notes")


class WindObservation(BaseModel):
    """
    Canonical surface wind conditions and smoke/heat plume dispersion direction.
    """
    observation_id: str = Field(default_factory=lambda: f"WND-{uuid.uuid4().hex[:8].upper()}")
    provider: str = Field("METEOROLOGICAL_STATION", description="Wind observation provider")
    dataset: str = Field("SURFACE_WIND", description="Dataset name")
    source_record_id: Optional[str] = None
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    observation_time: str = Field(..., description="Observation timestamp ISO8601")
    retrieval_time: Optional[str] = Field(None, description="Retrieval timestamp ISO8601")
    source_type: str = Field("TEST_FIXTURE", description="REAL_PROVIDER, LOCAL_DATASET, TEST_FIXTURE, SIMULATION, UNAVAILABLE, UNVERIFIED")
    evidence_nature: str = Field("OBSERVED", description="OBSERVED, DERIVED, INFERRED, MISSING, CONFLICTING, TEST_FIXTURE, SIMULATION, UNAVAILABLE")
    spatial_resolution: Optional[str] = Field(None, description="Spatial resolution")
    temporal_resolution: Optional[str] = Field(None, description="Temporal cadence")
    wind_speed_ms: float = Field(0.0, description="Wind speed in meters per second")
    wind_direction_deg: float = Field(0.0, description="Wind direction in degrees from North (0-360)")
    gust_speed_ms: Optional[float] = Field(None, description="Wind gust speed in m/s")
    transport_condition: str = Field("LIGHT_DISPERSION", description="CALM, LIGHT_DISPERSION, MODERATE_TRANSPORT, STRONG_ADVECTION, SEVERE_DISPERSION")
    smoke_dispersion_direction: Optional[str] = Field(None, description="Downwind bearing compass direction (e.g. ENE)")
    quality: str = Field("HIGH", description="Quality rating")
    provenance: Optional[SourceProvenance] = Field(None, description="Provenance lineage")
    limitations: Optional[str] = Field(None, description="Limitations")


class PrecipitationObservation(BaseModel):
    """
    Canonical precipitation metrics and thermal persistence support analysis.
    """
    observation_id: str = Field(default_factory=lambda: f"PCP-{uuid.uuid4().hex[:8].upper()}")
    provider: str = Field("METEOROLOGICAL_RADAR_GAUGE", description="Precipitation provider")
    dataset: str = Field("PRECIPITATION_RATE", description="Dataset name")
    source_record_id: Optional[str] = None
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    observation_time: str = Field(..., description="Observation timestamp ISO8601")
    retrieval_time: Optional[str] = Field(None, description="Retrieval timestamp ISO8601")
    source_type: str = Field("TEST_FIXTURE", description="REAL_PROVIDER, LOCAL_DATASET, TEST_FIXTURE, SIMULATION, UNAVAILABLE, UNVERIFIED")
    evidence_nature: str = Field("OBSERVED", description="OBSERVED, DERIVED, INFERRED, MISSING, CONFLICTING, TEST_FIXTURE, SIMULATION, UNAVAILABLE")
    spatial_resolution: Optional[str] = Field(None, description="Spatial resolution")
    temporal_resolution: Optional[str] = Field(None, description="Temporal cadence")
    precipitation_rate_mmh: float = Field(0.0, description="Current rain rate in mm/hour")
    accumulation_24h_mm: Optional[float] = Field(0.0, description="24-hour total accumulation in mm")
    precipitation_type: str = Field("NONE", description="NONE, DRIZZLE, LIGHT_RAIN, MODERATE_RAIN, HEAVY_RAIN, THUNDERSTORM")
    persistence_support_status: str = Field("SUPPORTIVE", description="SUPPORTIVE, NEUTRAL, INHIBITING, POTENTIALLY_INCONSISTENT")
    quality: str = Field("HIGH", description="Quality rating")
    provenance: Optional[SourceProvenance] = Field(None, description="Provenance lineage")
    limitations: Optional[str] = Field(None, description="Limitations")


class TemperatureObservation(BaseModel):
    """
    Ambient surface temperature observation.
    """
    observation_id: str = Field(default_factory=lambda: f"TMP-{uuid.uuid4().hex[:8].upper()}")
    provider: str = Field("SURFACE_MESONET", description="Temperature provider")
    dataset: str = Field("2M_TEMPERATURE", description="Dataset name")
    source_record_id: Optional[str] = None
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    observation_time: str = Field(..., description="Observation timestamp ISO8601")
    retrieval_time: Optional[str] = Field(None, description="Retrieval timestamp ISO8601")
    source_type: str = Field("TEST_FIXTURE", description="REAL_PROVIDER, LOCAL_DATASET, TEST_FIXTURE, SIMULATION, UNAVAILABLE, UNVERIFIED")
    evidence_nature: str = Field("OBSERVED", description="OBSERVED, DERIVED, INFERRED, MISSING, CONFLICTING, TEST_FIXTURE, SIMULATION, UNAVAILABLE")
    spatial_resolution: Optional[str] = Field(None, description="Spatial resolution")
    temporal_resolution: Optional[str] = Field(None, description="Temporal cadence")
    temperature_c: float = Field(25.0, description="Ambient temperature in Celsius")
    heat_index_c: Optional[float] = Field(None, description="Calculated heat index in Celsius")
    quality: str = Field("HIGH", description="Quality rating")
    provenance: Optional[SourceProvenance] = Field(None, description="Provenance lineage")
    limitations: Optional[str] = Field(None, description="Limitations")


class OpticalObservation(BaseModel):
    """
    Satellite high-resolution optical imagery pass (Sentinel-2, PlanetScope, Landsat).
    """
    observation_id: str = Field(default_factory=lambda: f"OPT-{uuid.uuid4().hex[:8].upper()}")
    provider: str = Field("COPERNICUS_SENTINEL2", description="Optical provider")
    dataset: str = Field("SENTINEL2_MSI_L2A", description="Dataset or product")
    source_record_id: Optional[str] = None
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    observation_time: str = Field(..., description="Acquisition timestamp ISO8601")
    retrieval_time: Optional[str] = Field(None, description="Retrieval timestamp ISO8601")
    source_type: str = Field("UNAVAILABLE", description="REAL_PROVIDER, LOCAL_DATASET, TEST_FIXTURE, SIMULATION, UNAVAILABLE, UNVERIFIED")
    evidence_nature: str = Field("MISSING", description="OBSERVED, DERIVED, INFERRED, MISSING, CONFLICTING, TEST_FIXTURE, SIMULATION, UNAVAILABLE")
    spatial_resolution: Optional[str] = Field(None, description="Spatial resolution")
    temporal_resolution: Optional[str] = Field(None, description="Temporal cadence")
    sensor: str = Field("SENTINEL_2_MSI", description="Sensor name")
    satellite: Optional[str] = Field("Sentinel-2B", description="Platform")
    cloud_cover_pct: float = Field(0.0, description="Tile cloud cover percentage")
    spatial_resolution_m: float = Field(10.0, description="Ground sampling distance in meters")
    swir_anomaly_detected: bool = Field(False, description="Shortwave infrared thermal reflection detected")
    surface_reflectance_change: Optional[float] = Field(None, description="Normalized burn ratio or delta index")
    observation_status: str = Field("NOT_CONFIGURED", description="AVAILABLE, CLOUD_OBSCURED, NOT_CONFIGURED, UNAVAILABLE")
    quality: str = Field("PROVISIONAL", description="Quality rating")
    provenance: Optional[SourceProvenance] = Field(None, description="Provenance lineage")
    limitations: Optional[str] = Field(None, description="Known sensor limitations")


class SARObservation(BaseModel):
    """
    Satellite Synthetic Aperture Radar pass (Sentinel-1 C-SAR).
    Provides all-weather, day/night penetrating radar backscatter measurements.
    """
    observation_id: str = Field(default_factory=lambda: f"SAR-{uuid.uuid4().hex[:8].upper()}")
    provider: str = Field("COPERNICUS_SENTINEL1", description="SAR provider")
    dataset: str = Field("SENTINEL1_GRD_CSAR", description="Dataset or product")
    source_record_id: Optional[str] = None
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    observation_time: str = Field(..., description="Acquisition timestamp ISO8601")
    retrieval_time: Optional[str] = Field(None, description="Retrieval timestamp ISO8601")
    source_type: str = Field("UNAVAILABLE", description="REAL_PROVIDER, LOCAL_DATASET, TEST_FIXTURE, SIMULATION, UNAVAILABLE, UNVERIFIED")
    evidence_nature: str = Field("MISSING", description="OBSERVED, DERIVED, INFERRED, MISSING, CONFLICTING, TEST_FIXTURE, SIMULATION, UNAVAILABLE")
    spatial_resolution: Optional[str] = Field(None, description="Spatial resolution")
    temporal_resolution: Optional[str] = Field(None, description="Temporal cadence")
    sensor: str = Field("SENTINEL_1_CSAR", description="Sensor name")
    satellite: Optional[str] = Field("Sentinel-1A", description="Platform")
    polarization: str = Field("VV_VH", description="Polarization channels (e.g. VV, VH, HH, HV)")
    spatial_resolution_m: float = Field(10.0, description="Spatial resolution in meters")
    backscatter_anomaly_detected: bool = Field(False, description="Significant radar backscatter difference detected")
    all_weather_penetration: bool = Field(True, description="True: C-band radar penetrates clouds, fog, and smoke")
    observation_status: str = Field("NOT_CONFIGURED", description="AVAILABLE, NOT_CONFIGURED, UNAVAILABLE")
    quality: str = Field("PROVISIONAL", description="Quality rating")
    provenance: Optional[SourceProvenance] = Field(None, description="Provenance lineage")
    limitations: Optional[str] = Field(None, description="Known SAR limitations")


class EnvironmentalRelationship(BaseModel):
    """
    Deterministic supporting relationship between environmental conditions and a thermal event.
    Explicitly labeled as SUPPORTING CONDITIONS or DERIVED RELATIONSHIPS, never absolute causality claims.
    """
    event_id: str = Field(..., description="Target thermal event ID")
    relationship_type: str = Field(..., description="DERIVED_ENVIRONMENTAL_RELATIONSHIP, ATMOSPHERIC_TRANSPORT_CONDITION, METEOROLOGICAL_PERSISTENCE_SUPPORT, PRECIPITATION_BURNING_INHIBITION, CLOUD_OBSERVATION_ATTENUATION")
    description: str = Field(..., description="Factual explanatory text")
    confidence: float = Field(1.0, description="Confidence score 0.0 - 1.0")
    is_supporting_condition: bool = Field(True, description="True indicates non-causal supporting environmental condition")
    source_type: str = Field("DERIVED", description="REAL_PROVIDER, LOCAL_DATASET, TEST_FIXTURE, DERIVED, INFERRED")
    evidence_nature: str = Field("DERIVED", description="DERIVED, INFERRED, OBSERVED, TEST_FIXTURE")
    derivation_details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Derivation inputs and calculation details")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")


class CrossModalEvidence(BaseModel):
    """
    Multi-modal corroboration evaluation comparing independently sourced observations
    (THERMAL, OPTICAL, SAR, WEATHER, ATMOSPHERIC, LAND COVER).
    """
    event_id: str = Field(..., description="Target thermal event ID")
    corroboration_status: str = Field("INSUFFICIENT_MODALITY", description="CORROBORATED, PARTIALLY_CORROBORATED, INCONCLUSIVE, CONFLICTING, INSUFFICIENT_MODALITY")
    modalities_evaluated: List[str] = Field(default_factory=list, description="List of modalities cross-referenced")
    source_type: str = Field("DERIVED", description="REAL_PROVIDER, LOCAL_DATASET, TEST_FIXTURE, DERIVED, INFERRED")
    evidence_nature: str = Field("INFERRED", description="INFERRED, DERIVED, OBSERVED, TEST_FIXTURE")
    thermal_time: Optional[str] = Field(None, description="Observation timestamp of primary thermal event")
    environment_time: Optional[str] = Field(None, description="Timestamp of auxiliary environmental or cross-modal observation")
    time_delta_hours: Optional[float] = Field(None, description="Temporal delta between primary thermal and auxiliary pass in hours")
    thermal_location: Optional[List[float]] = Field(None, description="[latitude, longitude] of thermal hotspot")
    environment_location: Optional[List[float]] = Field(None, description="[latitude, longitude] of auxiliary observation")
    spatial_distance_m: Optional[float] = Field(None, description="Spatial separation distance in meters")
    alignment_quality: str = Field("PROXIMATE", description="CONCURRENT, PROXIMATE, EPISODIC, HISTORICAL_CONTEXT, INSUFFICIENT_ALIGNMENT")
    evidence_strength: str = Field("LIMITED", description="STRONG, MODERATE, LIMITED, INSUFFICIENT")
    cross_modal_uncertainty: str = Field("UNCERTAIN", description="KNOWN, UNCERTAIN, MISSING, CONFLICTING")
    optical_corroboration: Dict[str, Any] = Field(default_factory=dict, description="Optical modality evaluation details")
    sar_corroboration: Dict[str, Any] = Field(default_factory=dict, description="SAR modality evaluation details")
    weather_corroboration: Dict[str, Any] = Field(default_factory=dict, description="Weather supporting condition details")
    land_cover_corroboration: Dict[str, Any] = Field(default_factory=dict, description="Land cover thematic match details")
    conflicts: List[str] = Field(default_factory=list, description="Genuine contradictions identified")
    missing_modalities: List[str] = Field(default_factory=list, description="Modalities unavailable or unconfigured")
    limiting_factors: List[str] = Field(default_factory=list, description="Factors creating cross-modal uncertainty")
    what_could_reduce_uncertainty: List[str] = Field(default_factory=list, description="Observations that would reduce cross-modal uncertainty")
    highest_value_observation: str = Field("", description="Single highest-value next observation to resolve ambiguity")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")


class EnvironmentalEvidence(BaseModel):
    """
    Comprehensive environmental conditions and supporting context for a thermal event.
    """
    event_id: str = Field(..., description="Target thermal event ID")
    evidence_strength: str = Field("MODERATE", description="STRONG, MODERATE, LIMITED, INSUFFICIENT")
    environmental_uncertainty: str = Field("KNOWN", description="KNOWN, UNCERTAIN, MISSING, CONFLICTING")
    source_type: str = Field("TEST_FIXTURE", description="REAL_PROVIDER, LOCAL_DATASET, TEST_FIXTURE, DERIVED, INFERRED")
    evidence_nature: str = Field("DERIVED", description="DERIVED, INFERRED, OBSERVED, TEST_FIXTURE")
    weather_observation: Optional[WeatherObservation] = Field(None, description="Normalized weather observation")
    wind_observation: Optional[WindObservation] = Field(None, description="Wind vector observation")
    precipitation_observation: Optional[PrecipitationObservation] = Field(None, description="Precipitation observation")
    cloud_condition: Optional[CloudCondition] = Field(None, description="Cloud observability condition")
    atmospheric_observation: Optional[AtmosphericObservation] = Field(None, description="Atmospheric composition")
    relationships: List[EnvironmentalRelationship] = Field(default_factory=list, description="Supporting environmental relationships")
    missing_sources: List[str] = Field(default_factory=list, description="Unconfigured or unavailable environmental providers")
    conflicts: List[str] = Field(default_factory=list, description="Contradictions detected")
    limiting_factors: List[str] = Field(default_factory=list, description="Factors creating environmental uncertainty")
    what_could_reduce_uncertainty: List[str] = Field(default_factory=list, description="Actionable observations to reduce uncertainty")
    provenance: Optional[SourceProvenance] = Field(None, description="Source provenance metadata")




