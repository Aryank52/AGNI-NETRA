"""
AGNI-NETRA Phase 6: Intelligence Source Provenance System
Captures factual origin, temporal lineage, spatial resolution, and limitations
for every canonical intelligence artifact.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class SourceProvenance(BaseModel):
    """
    Factual provenance audit metadata attached to canonical intelligence objects.
    Enforces strict lineage without fabricating metadata.
    """
    provider: str = Field(..., description="Intelligence provider identifier (e.g., FIRMS, OSM, CEA)")
    dataset: str = Field(..., description="Specific underlying dataset name (e.g., NASA_FIRMS_VIIRS_NRT)")
    source_record_id: Optional[str] = Field(None, description="Primary unique record identifier in upstream system")
    observation_time: Optional[str] = Field(None, description="ISO-8601 UTC timestamp of original physical observation")
    retrieval_time: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 UTC timestamp of retrieval/ingestion into AGNI-NETRA"
    )
    source_type: str = Field(
        "REAL_PROVIDER",
        description="Source classification: REAL_PROVIDER, LOCAL_DATASET, TEST_FIXTURE, SIMULATION, UNAVAILABLE, UNVERIFIED"
    )
    evidence_nature: str = Field(
        "OBSERVED",
        description="Evidence nature: OBSERVED, DERIVED, INFERRED, MISSING, CONFLICTING, TEST_FIXTURE, SIMULATION, UNAVAILABLE"
    )
    quality: str = Field("HIGH", description="Quality rating: HIGH, MEDIUM, LOW, PROVISIONAL, DEGRADED")
    latitude: Optional[float] = Field(None, description="Spatial latitude coordinate")
    longitude: Optional[float] = Field(None, description="Spatial longitude coordinate")
    geographic_coverage: str = Field(..., description="Factual geographic reach (GLOBAL, COUNTRY:IN, STATE:GJ, etc.)")
    spatial_resolution: Optional[str] = Field(None, description="Spatial resolution if known (e.g., 375m, 10m, Polygon)")
    temporal_resolution: Optional[str] = Field(None, description="Temporal cadence if known (e.g., 12-hour, annual)")
    source_version: Optional[str] = Field(None, description="Dataset/catalog version if known")
    limitations: Optional[str] = Field(None, description="Factual operational or sensor limitations")
    confidence_tier: Optional[str] = Field("HIGH", description="Confidence tier: HIGH, MEDIUM, LOW, PROVISIONAL")
    extra_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional non-fabricated metadata")

    model_config = {
        "frozen": False,
        "from_attributes": True
    }

    def __init__(self, **data):
        if "provider_name" in data and "provider" not in data:
            data["provider"] = data.pop("provider_name")
        if "dataset_name" in data and "dataset" not in data:
            data["dataset"] = data.pop("dataset_name")
        if "geographic_coverage_type" in data and "geographic_coverage" not in data:
            data["geographic_coverage"] = data.pop("geographic_coverage_type")
        if "authoritative_limitations" in data and "limitations" not in data:
            data["limitations"] = data.pop("authoritative_limitations")
        if "collection_timestamp" in data and "observation_time" not in data:
            cts = data.pop("collection_timestamp")
            data["observation_time"] = cts.isoformat() if hasattr(cts, "isoformat") else str(cts)
        if "processing_level" in data:
            pl = data.pop("processing_level")
            extra = data.get("extra_metadata", {})
            extra["processing_level"] = pl
        if "data_authenticity" in data and "source_type" not in data:
            data["source_type"] = data.pop("data_authenticity")
        super().__init__(**data)

    @property
    def data_authenticity(self) -> str:
        return self.source_type


def create_firms_provenance(
    record_id: Optional[str] = None,
    observation_time: Optional[datetime] = None,
    sensor: str = "VIIRS_NOAA21",
    confidence: Optional[float] = None
) -> SourceProvenance:
    """Helper to construct factual NASA FIRMS thermal provenance."""
    obs_str = observation_time.isoformat() if observation_time else None
    return SourceProvenance(
        provider="FIRMS",
        dataset=f"NASA_FIRMS_{sensor}",
        source_record_id=str(record_id) if record_id else None,
        observation_time=obs_str,
        geographic_coverage="GLOBAL",
        spatial_resolution="375m" if "VIIRS" in sensor else "1000m",
        temporal_resolution="12-hour orbit revisit",
        source_version="NRT v2.0",
        limitations="Cloud cover and heavy smoke may occlude low-intensity thermal anomalies; nominal pixel footprint 375m.",
        confidence_tier="HIGH" if (confidence and confidence >= 80) else "MEDIUM",
        extra_metadata={"sensor": sensor, "confidence": confidence}
    )


def create_osm_provenance(
    osm_id: Optional[Any] = None,
    osm_type: Optional[str] = None,
    entity_classification: Optional[str] = None,
    record_id: Optional[str] = None,
    confidence: Optional[Any] = None,
    **kwargs: Any
) -> SourceProvenance:
    """Helper to construct factual OpenStreetMap industrial facility provenance."""
    src_id = str(record_id) if record_id else (f"{osm_type}/{osm_id}" if osm_type and osm_id else (str(osm_id) if osm_id else None))
    tier = "HIGH" if (confidence in ("HIGH", 80) or (isinstance(confidence, (int, float)) and confidence >= 80)) else "MEDIUM"
    return SourceProvenance(
        provider="OSM",
        dataset="OPENSTREETMAP_INDUSTRIAL_REGISTRY",
        source_record_id=src_id,
        geographic_coverage="GLOBAL / REGIONAL",
        spatial_resolution="Vector (Polygon/Point)",
        temporal_resolution="Crowdsourced / Quarterly Snapshot",
        source_version="OSM Planet Snapshot",
        limitations="Crowdsourced boundary definitions; non-exhaustive industrial operator tagging in rural regions.",
        confidence_tier=tier,
        extra_metadata={"osm_type": osm_type, "classification": entity_classification}
    )


def create_cea_provenance(
    cea_record_id: Optional[str] = None,
    plant_name: Optional[str] = None,
    prime_mover: Optional[str] = None,
    **kwargs: Any
) -> SourceProvenance:
    """Helper to construct factual Central Electricity Authority provenance."""
    rec_id = cea_record_id or kwargs.get("record_id")
    return SourceProvenance(
        provider="CEA",
        dataset="CENTRAL_ELECTRICITY_AUTHORITY_POWER_REGISTRY",
        source_record_id=str(rec_id) if rec_id else None,
        geographic_coverage="COUNTRY:IN",
        spatial_resolution="Plant / District Level Coordinates",
        temporal_resolution="Annual CEA Power Survey",
        source_version="CEA 2024-2025",
        limitations="Covers thermal, hydro, and nuclear utilities under CEA purview; captive micro-plants may be excluded.",
        confidence_tier="HIGH",
        extra_metadata={"plant_name": plant_name, "prime_mover": prime_mover}
    )


def create_parivesh_provenance(
    proposal_id: Optional[str] = None,
    category: Optional[str] = None,
    decision_date: Optional[str] = None,
    **kwargs: Any
) -> SourceProvenance:
    """Helper to construct factual MoEFCC PARIVESH regulatory clearance provenance."""
    rec_id = proposal_id or kwargs.get("record_id")
    return SourceProvenance(
        provider="PARIVESH",
        dataset="MOEFCC_PARIVESH_ENVIRONMENTAL_CLEARANCES",
        source_record_id=str(rec_id) if rec_id else None,
        observation_time=decision_date,
        geographic_coverage="COUNTRY:IN (PARTIAL)",
        spatial_resolution="Project Footprint Coordinates",
        temporal_resolution="Event-driven regulatory filings",
        source_version="MoEFCC Portal 2024",
        limitations="Contains statutory clearance proposals; legacy pre-2006 clearances or unfiled micro-expansions may not appear.",
        confidence_tier="HIGH",
        extra_metadata={"category": category}
    )


def create_ibm_provenance(
    record_id: Optional[str] = None,
    mineral: Optional[str] = None,
    table_number: Optional[str] = None,
    **kwargs: Any
) -> SourceProvenance:
    """Helper to construct factual Indian Bureau of Mines mining lease provenance."""
    return SourceProvenance(
        provider="IBM",
        dataset="INDIAN_BUREAU_OF_MINES_LEASE_BULLETIN",
        source_record_id=str(record_id) if record_id else None,
        geographic_coverage="COUNTRY:IN",
        spatial_resolution="District / Sub-district aggregates",
        temporal_resolution="Annual Bulletin",
        source_version="IBM Bulletin 2024",
        limitations="District-level statistical lease areas; unorganized artisanal quarrying not captured.",
        confidence_tier="HIGH",
        extra_metadata={"mineral": mineral, "table_number": table_number}
    )


def create_bhuvan_provenance(
    feature_id: Optional[str] = None,
    lulc_class: Optional[str] = None,
    **kwargs: Any
) -> SourceProvenance:
    """Helper to construct factual ISRO Bhuvan LULC provenance."""
    rec_id = feature_id or kwargs.get("record_id")
    return SourceProvenance(
        provider="ISRO_BHUVAN",
        dataset="BHUVAN_LULC_THEMATIC_MAPS",
        source_record_id=str(rec_id) if rec_id else None,
        geographic_coverage="COUNTRY:IN",
        spatial_resolution="1:50,000 / 30m Grid",
        temporal_resolution="Multi-year Land Use Cycle",
        source_version="ISRO LULC Cycle 4",
        limitations="LULC classification boundary edges subject to mixed-pixel classification error at 30m resolution.",
        confidence_tier="HIGH",
        extra_metadata={"lulc_class": lulc_class}
    )


def create_fsi_provenance(
    record_id: Optional[str] = None,
    pa_name: Optional[str] = None,
    **kwargs: Any
) -> SourceProvenance:
    """Helper to construct factual Forest Survey of India protected area provenance."""
    return SourceProvenance(
        provider="FSI",
        dataset="FSI_ISFR_PROTECTED_AREAS",
        source_record_id=str(record_id) if record_id else None,
        geographic_coverage="COUNTRY:IN",
        spatial_resolution="Vector Boundaries / Eco-Sensitive Zones (ESZ)",
        temporal_resolution="Biennial India State of Forest Report",
        source_version="ISFR 2023-2024",
        limitations="Boundary accuracy aligns with official gazette notifications; contested boundary demarcations require ground validation.",
        confidence_tier="HIGH",
        extra_metadata={"protected_area": pa_name}
    )


def create_copernicus_slstr_provenance(
    record_id: Optional[str] = None,
    observation_time: Optional[datetime] = None,
    satellite: str = "Sentinel-3A",
    confidence: Optional[float] = None
) -> SourceProvenance:
    """Helper to construct factual Copernicus Sentinel-3 SLSTR thermal provenance."""
    obs_str = observation_time.isoformat() if observation_time else None
    return SourceProvenance(
        provider="COPERNICUS_SLSTR",
        dataset=f"COPERNICUS_SENTINEL3_SLSTR_FRP_{satellite}",
        source_record_id=str(record_id) if record_id else None,
        observation_time=obs_str,
        geographic_coverage="GLOBAL",
        spatial_resolution="1000m SLSTR Nadir Footprint",
        temporal_resolution="Daily Global Revisit (Dual-satellite Sentinel-3A/3B)",
        source_version="SLSTR NRT L2 FRP v2.1",
        limitations="Solar glint filtering and thick cloud obscuration may affect low-radiative power detection.",
        confidence_tier="HIGH" if (confidence and confidence >= 70) else "MEDIUM",
        extra_metadata={"satellite": satellite, "confidence": confidence}
    )


create_slstr_provenance = create_copernicus_slstr_provenance



def create_mosdac_provenance(
    record_id: Optional[str] = None,
    observation_time: Optional[datetime] = None,
    satellite: str = "INSAT-3D",
    confidence: Optional[float] = None
) -> SourceProvenance:
    """Helper to construct factual ISRO MOSDAC geostationary thermal provenance."""
    obs_str = observation_time.isoformat() if observation_time else None
    return SourceProvenance(
        provider="ISRO_MOSDAC",
        dataset=f"MOSDAC_{satellite}_TIR_HOTSPOT",
        source_record_id=str(record_id) if record_id else None,
        observation_time=obs_str,
        geographic_coverage="REGION:INDIAN_OCEAN",
        spatial_resolution="4000m Geostationary TIR",
        temporal_resolution="15-minute Rapid Scan Cadence",
        source_version="MOSDAC FIR v1.0",
        limitations="Coarse 4km pixel resolution compared to polar orbiters; optimized for large-scale flaring and thermal anomalies.",
        confidence_tier="MEDIUM",
        extra_metadata={"satellite": satellite, "confidence": confidence}
    )


def create_goes_provenance(
    record_id: Optional[str] = None,
    observation_time: Optional[datetime] = None,
    satellite: str = "GOES-16"
) -> SourceProvenance:
    """Helper to construct factual NOAA GOES ABI FDCA thermal provenance."""
    obs_str = observation_time.isoformat() if observation_time else None
    return SourceProvenance(
        provider="NOAA_GOES",
        dataset=f"NOAA_GOES_ABI_FDCA_{satellite}",
        source_record_id=str(record_id) if record_id else None,
        observation_time=obs_str,
        geographic_coverage="REGION:AMERICAS",
        spatial_resolution="2000m ABI Nadir",
        temporal_resolution="5-minute CONUS / 10-minute Full Disk",
        source_version="NOAA ABI L2 FDCA",
        limitations="Geostationary coverage restricted strictly to Western Hemisphere (Americas). Not configured for Indian subcontinent.",
        confidence_tier="HIGH",
        extra_metadata={"satellite": satellite}
    )


def create_environmental_fixture_provenance(
    provider: str = "REGIONAL_SURFACE_METEOROLOGY",
    dataset: str = "IMD_GROUND_MESONET_ARCHIVE",
    record_id: Optional[str] = None,
    observation_time: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    limitations: Optional[str] = None,
    source_type: str = "TEST_FIXTURE",
    evidence_nature: str = "TEST_FIXTURE",
    quality: str = "HIGH"
) -> SourceProvenance:
    """Helper to construct explicit TEST_FIXTURE provenance for environmental demonstration data."""
    return SourceProvenance(
        provider=provider,
        dataset=dataset,
        source_record_id=str(record_id) if record_id else None,
        observation_time=observation_time or datetime.now(timezone.utc).isoformat(),
        source_type=source_type,
        evidence_nature=evidence_nature,
        quality=quality,
        latitude=lat,
        longitude=lon,
        geographic_coverage="REGION:GUJARAT_COASTAL",
        spatial_resolution="POINT_STATION",
        temporal_resolution="HOURLY",
        source_version="DEMO_FIXTURE_v1.0",
        limitations=limitations or "Deterministic demonstration fixture for local test suite and simulation.",
        confidence_tier="HIGH"
    )


def create_derived_environmental_provenance(
    derivation_name: str = "PLUME_DISPERSION_VECTOR",
    input_providers: Optional[List[str]] = None,
    record_id: Optional[str] = None,
    observation_time: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    derivation_method: str = "Gaussian vector translation from 10m wind vector and boundary layer height"
) -> SourceProvenance:
    """Helper to construct explicit DERIVED provenance for non-directly-observed environmental properties."""
    inputs = input_providers or ["REGIONAL_SURFACE_METEOROLOGY"]
    return SourceProvenance(
        provider="AGNI_NETRA_DERIVATION_ENGINE",
        dataset=f"DERIVED_{derivation_name}",
        source_record_id=str(record_id) if record_id else None,
        observation_time=observation_time or datetime.now(timezone.utc).isoformat(),
        source_type="DERIVED",
        evidence_nature="DERIVED",
        quality="HIGH",
        latitude=lat,
        longitude=lon,
        geographic_coverage="LOCAL_ANALYSIS_RADIUS",
        spatial_resolution="Vector corridor",
        temporal_resolution="EVENT_SYNCHRONIZED",
        source_version="AN_DERIVATION_v1.0",
        limitations=f"DERIVED ENVIRONMENTAL RELATIONSHIP: {derivation_method}. Not an observed plume or physical measurement.",
        confidence_tier="HIGH",
        extra_metadata={"derivation_inputs": inputs, "derivation_method": derivation_method}
    )


def create_derived_provenance(
    provider: str = "AGNI_NETRA",
    dataset: str = "DERIVED_INTELLIGENCE",
    derivation_method: str = "Deterministic Domain Synthesis",
    record_id: Optional[str] = None,
    observation_time: Optional[str] = None,
    **kwargs: Any
) -> SourceProvenance:
    """Helper to construct explicit DERIVED provenance for synthesized intelligence artifacts."""
    return SourceProvenance(
        provider=provider,
        dataset=dataset,
        source_record_id=str(record_id) if record_id else None,
        observation_time=observation_time or datetime.now(timezone.utc).isoformat(),
        source_type="DERIVED",
        evidence_nature="DERIVED",
        quality="HIGH",
        geographic_coverage="LOCAL_ANALYSIS_RADIUS",
        spatial_resolution=kwargs.get("spatial_resolution", "Point / Region"),
        temporal_resolution="EVENT_SYNCHRONIZED",
        source_version="AN_DERIVATION_v1.0",
        limitations=f"DERIVED EVIDENCE: {derivation_method}.",
        confidence_tier="HIGH",
        extra_metadata={"derivation_method": derivation_method, **kwargs}
    )


def create_unconfigured_provenance(
    provider: str,
    dataset: str,
    modality: str,
    limitations: Optional[str] = None
) -> SourceProvenance:
    """Helper to construct explicit UNAVAILABLE / NOT_CONFIGURED provenance."""
    return SourceProvenance(
        provider=provider,
        dataset=dataset,
        source_record_id=None,
        observation_time=None,
        source_type="UNAVAILABLE",
        evidence_nature="MISSING",
        quality="DEGRADED",
        geographic_coverage="GLOBAL",
        spatial_resolution="N/A",
        temporal_resolution="N/A",
        source_version="UNCONFIGURED",
        limitations=limitations or f"[NOT CONFIGURED] {provider} data access pipeline is not configured in local environment. Zero synthetic records fabricated.",
        confidence_tier="PROVISIONAL",
        extra_metadata={"modality": modality, "status": "NOT_CONFIGURED"}
    )
