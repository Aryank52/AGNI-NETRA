"""
AGNI-NETRA Phase 6: Intelligence Profiles
Logical configuration profiles defining active data environments and future global extension contracts.
Note: These are data/configuration profiles, NOT new runtime agents.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class IntelligenceProfile(BaseModel):
    profile_id: str
    display_name: str
    description: str
    is_active_default: bool
    active_providers: List[str]
    supported_capabilities: List[str]
    unconfigured_capabilities: List[str]
    extension_points: List[str] = Field(default_factory=list)


class IndiaIntelligenceProfile:
    """
    Authoritative active operational data profile for AGNI-NETRA.
    Covers the full multi-source fusion stack across Indian national and state datasets.
    """

    PROFILE_ID = "INDIA"
    DISPLAY_NAME = "India Operational Intelligence Profile"
    DESCRIPTION = "Fully populated operational intelligence environment covering all Indian states and Union Territories."

    ACTIVE_PROVIDERS = [
        "FIRMS",
        "OSM",
        "CEA",
        "PARIVESH",
        "IBM_MINING",
        "ISRO_BHUVAN",
        "FSI",
        "ADMIN_BOUNDARIES",
    ]

    SUPPORTED_CAPABILITIES = [
        "thermal_hotspot_detection",
        "fire_radiative_power",
        "facility_footprint_polygon",
        "utility_power_registry",
        "environmental_clearance_verification",
        "mining_lease_audit",
        "land_use_classification",
        "protected_area_buffer_analysis",
        "historical_baselines",
        "xgboost_anomaly_scoring",
    ]

    UNCONFIGURED_CAPABILITIES = [
        "weather_atmospheric_dispersion",
        "submeter_optical_imagery",
    ]

    @classmethod
    def get_profile(cls) -> IntelligenceProfile:
        return IntelligenceProfile(
            profile_id=cls.PROFILE_ID,
            display_name=cls.DISPLAY_NAME,
            description=cls.DESCRIPTION,
            is_active_default=True,
            active_providers=cls.ACTIVE_PROVIDERS,
            supported_capabilities=cls.SUPPORTED_CAPABILITIES,
            unconfigured_capabilities=cls.UNCONFIGURED_CAPABILITIES,
            extension_points=[]
        )


class GlobalIntelligenceProfile:
    """
    Architectural scaffolding profile for future global intelligence expansion.
    Enforces clean extension points without claiming global datasets that are not yet populated.
    """

    PROFILE_ID = "GLOBAL"
    DISPLAY_NAME = "Global Intelligence Architectural Scaffolding"
    DESCRIPTION = "Architectural framework for planetary coverage. Active only for global-native layers (FIRMS, OSM)."

    ACTIVE_PROVIDERS = [
        "FIRMS",  # Global thermal orbital detections
        "OSM",    # Global industrial nodes and polygons
    ]

    SUPPORTED_CAPABILITIES = [
        "global_thermal_monitoring",
        "global_industrial_tag_mapping",
    ]

    # Explicit extension points for future implementation without modifying core architecture
    EXTENSION_POINTS = [
        "global_land_cover (Copernicus / ESA WorldCover 10m)",
        "global_administrative_boundaries (Natural Earth / geoBoundaries Global)",
        "global_weather_intelligence (ECMWF ERA5 / GFS)",
        "global_protected_areas (UNEP-WCMC / WDPA / IUCN)",
        "global_power_infrastructure (Global Power Plant Database / WRI)",
        "global_mining_atlas (S&P Global Market Intelligence / USGS)",
        "global_high_resolution_optical (Sentinel-2 / PlanetScope Constellation)",
    ]

    UNCONFIGURED_CAPABILITIES = [
        "global_weather_dispersion",
        "global_mining_registry",
        "global_environmental_compliance",
        "global_submeter_optical",
    ]

    @classmethod
    def get_profile(cls) -> IntelligenceProfile:
        return IntelligenceProfile(
            profile_id=cls.PROFILE_ID,
            display_name=cls.DISPLAY_NAME,
            description=cls.DESCRIPTION,
            is_active_default=False,
            active_providers=cls.ACTIVE_PROVIDERS,
            supported_capabilities=cls.SUPPORTED_CAPABILITIES,
            unconfigured_capabilities=cls.UNCONFIGURED_CAPABILITIES,
            extension_points=cls.EXTENSION_POINTS
        )
