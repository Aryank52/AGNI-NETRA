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


class GlobalContextProfile:
    """
    Phase 8: Global Context Intelligence & Cross-Domain Provider Profile.
    Explicitly articulates availability (AVAILABLE, PARTIAL, NOT_CONFIGURED)
    for each contextual domain across Indian operational depth and global reach.
    """

    PROFILE_ID = "GLOBAL_CONTEXT"
    DISPLAY_NAME = "Global Context Intelligence & Cross-Domain Profile"
    DESCRIPTION = "Provider-neutral contextual intelligence profile exposing factual availability across 7 domains."

    # Minimum 7 required context domains with explicit availability status
    DOMAIN_AVAILABILITY = {
        "FACILITIES": {
            "status": "AVAILABLE",
            "provider": "OSM",
            "dataset": "OPENSTREETMAP_INDUSTRIAL_FACILITIES",
            "coverage": "GLOBAL_SCHEMA_INDIA_OPERATIONAL",
            "is_global": True,
            "description": "Global OSM industrial schema with operational depth across all Indian states and worldwide POI nodes.",
            "limitations": "Crowdsourced density varies in unmapped rural regions outside major industrial hubs."
        },
        "POWER": {
            "status": "PARTIAL",
            "provider": "CEA",
            "dataset": "CENTRAL_ELECTRICITY_AUTHORITY_STATION_DATABASE",
            "coverage": "INDIA_OPERATIONAL",
            "is_global": False,
            "description": "Official Central Electricity Authority generation stations across Northern, Western, Southern, Eastern, and NE regions.",
            "limitations": "Global power registry (WRI Global Power Plant Database) is NOT CONFIGURED. Off-grid units <25MW not cataloged."
        },
        "MINING": {
            "status": "PARTIAL",
            "provider": "IBM_MINING",
            "dataset": "INDIAN_BUREAU_OF_MINES_MINING_LEASES",
            "coverage": "INDIA_OPERATIONAL",
            "is_global": False,
            "description": "Indian Bureau of Mines statutory lease bulletins and mineral concession statistics.",
            "limitations": "Global mineral atlas (USGS MRDS / S&P Global) is NOT CONFIGURED. Local quarry minor minerals vary."
        },
        "LAND_COVER": {
            "status": "PARTIAL",
            "provider": "ISRO_BHUVAN",
            "dataset": "ISRO_BHUVAN_THEMATIC_LULC",
            "coverage": "INDIA_OPERATIONAL",
            "is_global": False,
            "description": "National Remote Sensing Centre 1:50,000 scale thematic LULC layers across India.",
            "limitations": "Global land cover (ESA WorldCover 10m / Copernicus) is NOT CONFIGURED. Rapid suburban realignments have latency."
        },
        "PROTECTED_AREAS": {
            "status": "PARTIAL",
            "provider": "FSI",
            "dataset": "FOREST_SURVEY_OF_INDIA_PROTECTED_AREAS",
            "coverage": "INDIA_OPERATIONAL",
            "is_global": False,
            "description": "National Parks, Wildlife Sanctuaries, Tiger Reserves, and Eco-Sensitive Zones (ESZ) across India.",
            "limitations": "Global protected areas (UNEP-WCMC / WDPA) is NOT CONFIGURED. State gazette notifications take time to sync."
        },
        "ADMINISTRATIVE": {
            "status": "PARTIAL",
            "provider": "ADMIN_BOUNDARIES",
            "dataset": "SURVEY_OF_INDIA_ADMIN_BOUNDARIES",
            "coverage": "INDIA_OPERATIONAL",
            "is_global": False,
            "description": "Official Survey of India administrative hierarchy covering Level 0 (Country) to Level 3 (Tehsils/Taluks).",
            "limitations": "Global administrative boundaries (geoBoundaries / Natural Earth) are NOT CONFIGURED. Post-2023 district splits require reconciliation."
        },
        "ENVIRONMENTAL": {
            "status": "PARTIAL",
            "provider": "PARIVESH",
            "dataset": "MOEFCC_PARIVESH_ENVIRONMENTAL_CLEARANCES",
            "coverage": "INDIA_OPERATIONAL",
            "is_global": False,
            "description": "Ministry of Environment, Forest and Climate Change statutory environmental clearance filings (Category A and B).",
            "limitations": "Global environmental compliance is NOT CONFIGURED. Legacy clearances may lack GIS coordinates."
        }
    }

    # Explicit unconfigured global stubs
    UNCONFIGURED_GLOBAL_PROVIDERS = [
        {"domain": "POWER", "provider": "GLOBAL_POWER_DATABASE", "status": "NOT_CONFIGURED", "limitations": "WRI Global Power Plant Database not configured."},
        {"domain": "MINING", "provider": "USGS_MRDS_GLOBAL_MINING", "status": "NOT_CONFIGURED", "limitations": "USGS global mineral resources dataset not configured."},
        {"domain": "LAND_COVER", "provider": "ESA_WORLDCOVER_GLOBAL", "status": "NOT_CONFIGURED", "limitations": "ESA WorldCover 10m global provider not configured."},
        {"domain": "PROTECTED_AREAS", "provider": "WDPA_GLOBAL_PROTECTED_AREAS", "status": "NOT_CONFIGURED", "limitations": "UNEP-WCMC World Database on Protected Areas not configured."},
        {"domain": "ADMINISTRATIVE", "provider": "GEOBOUNDARIES_GLOBAL", "status": "NOT_CONFIGURED", "limitations": "geoBoundaries global administrative database not configured."},
        {"domain": "ENVIRONMENTAL", "provider": "GLOBAL_ENVIRONMENTAL_REGISTRY", "status": "NOT_CONFIGURED", "limitations": "Global environmental compliance registries not configured."},
        {"domain": "WEATHER", "provider": "ECMWF_ERA5_ATMOSPHERIC", "status": "NOT_CONFIGURED", "limitations": "Global atmospheric dispersion reanalysis not configured."}
    ]

    @classmethod
    def get_context_coverage(cls, region: str = "GLOBAL") -> Dict[str, Any]:
        """Returns factual domain-by-domain coverage and availability."""
        is_india = region.upper() in ("INDIA", "IN", "BHARAT")
        domains_out = {}
        for domain, info in cls.DOMAIN_AVAILABILITY.items():
            if not is_india and not info["is_global"]:
                domains_out[domain] = {
                    **info,
                    "status": "NOT_CONFIGURED",
                    "coverage": "NOT_CONFIGURED_FOR_REGION",
                    "limitations": f"No regional adapter configured for {region} in {domain} domain."
                }
            else:
                domains_out[domain] = info

        return {
            "region": region,
            "profile_id": cls.PROFILE_ID,
            "display_name": cls.DISPLAY_NAME,
            "total_domains": len(domains_out),
            "domains": domains_out,
            "unconfigured_providers": cls.UNCONFIGURED_GLOBAL_PROVIDERS
        }

