"""
AGNI-NETRA Phase 6: Controlled Intelligence Provider Registry
Central singleton governing provider discovery, factual coverage aggregation,
operational health reporting, and RBAC-governed catalog access.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from backend.app.services.intelligence.providers.base import (
    BaseIntelligenceProvider,
    ThermalProvider,
    ProviderMetadata,
    ProviderHealth,
    GeographicCoverage,
    EvidenceAvailability,
)
from backend.app.services.intelligence.providers.adapters import (
    FIRMSProvider,
    CopernicusSLSTRProvider,
    MOSDACThermalProvider,
    NOAAGOESProvider,
    OSMFacilityProvider,
    CEAProvider,
    PARIVESHProvider,
    IBMMiningProvider,
    BhuvanProvider,
    FSIProvider,
    AdministrativeBoundaryProvider,
    WeatherProviderScaffold,
    HighResOpticalProviderScaffold,
)


class ProviderRegistry:
    """
    Controlled singleton maintaining all active and unconfigured provider adapters.
    Can be inspected by JARVIS and administrative APIs.
    """

    _instance: Optional["ProviderRegistry"] = None

    def __new__(cls) -> "ProviderRegistry":
        if cls._instance is None:
            cls._instance = super(ProviderRegistry, cls).__new__(cls)
            cls._instance._providers: Dict[str, BaseIntelligenceProvider] = {}
            cls._instance._initialize_default_providers()
        return cls._instance

    def _initialize_default_providers(self) -> None:
        """Populates the registry with all standard AGNI-NETRA adapters."""
        default_providers = [
            FIRMSProvider(),
            CopernicusSLSTRProvider(),
            MOSDACThermalProvider(),
            NOAAGOESProvider(),
            OSMFacilityProvider(),
            CEAProvider(),
            PARIVESHProvider(),
            IBMMiningProvider(),
            BhuvanProvider(),
            FSIProvider(),
            AdministrativeBoundaryProvider(),
            WeatherProviderScaffold(),
            HighResOpticalProviderScaffold(),
        ]
        for p in default_providers:
            meta = p.get_metadata()
            self._providers[meta.provider_name.upper()] = p

    def register_provider(self, provider: BaseIntelligenceProvider) -> None:
        """Registers or replaces a provider adapter."""
        meta = provider.get_metadata()
        self._providers[meta.provider_name.upper()] = provider

    def get_provider(self, name: str) -> Optional[BaseIntelligenceProvider]:
        """Retrieves a provider adapter by name (case-insensitive)."""
        return self._providers.get(name.upper())

    def list_providers(self, role: str = "ANALYST") -> List[Dict[str, Any]]:
        """
        Lists registered provider metadata.
        For PUBLIC users, restricts internal provenance and operational diagnostic limitations.
        """
        results = []
        is_public = (role.upper() == "PUBLIC")

        for p in self._providers.values():
            meta = p.get_metadata()
            item = meta.model_dump()
            if is_public:
                # Mask sensitive internal notes / URLs / diagnostic details for public tier
                item["source_provenance"] = "Authoritative Satellite / Official Public Catalog"
                if meta.availability == ProviderHealth.DEGRADED:
                    item["availability"] = ProviderHealth.AVAILABLE
            results.append(item)
        return results

    def get_coverage_summary(self) -> Dict[str, Any]:
        """
        Returns factual geographic coverage across all registered providers.
        Does NOT claim global coverage that does not exist.
        """
        global_providers = []
        country_providers = []
        unconfigured = []

        for p in self._providers.values():
            meta = p.get_metadata()
            cov = p.get_coverage()
            if meta.availability == ProviderHealth.NOT_CONFIGURED:
                unconfigured.append(meta.provider_name)
            elif cov.is_global:
                global_providers.append({
                    "provider": meta.provider_name,
                    "dataset": meta.dataset_name,
                    "coverage": "GLOBAL",
                    "description": cov.description
                })
            else:
                country_providers.append({
                    "provider": meta.provider_name,
                    "dataset": meta.dataset_name,
                    "coverage": "INDIA (National / State)",
                    "description": cov.description
                })

        return {
            "active_operational_profile": "INDIA",
            "global_capable_providers": global_providers,
            "india_operational_providers": country_providers,
            "unconfigured_providers": unconfigured,
            "factual_disclaimer": "Operational intelligence is active across India. Global coverage is currently available for FIRMS thermal sensing and OSM facilities; regional industrial and regulatory registries outside India are not configured."
        }

    def get_provider_health_summary(self, db: Optional[Session] = None) -> Dict[str, Any]:
        """Returns lightweight operational health of all registered providers."""
        statuses = {}
        for name, p in self._providers.items():
            health = p.get_health(db)
            statuses[name] = health.value
        return {
            "provider_count": len(self._providers),
            "statuses": statuses,
            "all_healthy": all(s in ("AVAILABLE", "NOT_CONFIGURED") for s in statuses.values())
        }

    def get_thermal_providers(self) -> List[ThermalProvider]:
        """Returns all registered thermal providers (both operational and unconfigured)."""
        return [p for p in self._providers.values() if isinstance(p, ThermalProvider)]

    def get_thermal_coverage_summary(self, region: Optional[str] = None) -> Dict[str, Any]:
        """Returns detailed coverage and status across all thermal satellite constellations."""
        thermal_list = []
        global_orbiters = []
        regional_geostationary = []
        unconfigured = []

        for p in self.get_thermal_providers():
            meta = p.get_metadata()
            cov = p.get_coverage()
            info = {
                "provider_name": meta.provider_name,
                "dataset_name": meta.dataset_name,
                "status": meta.availability.value,
                "coverage_type": cov.coverage_type.value,
                "is_global": cov.is_global,
                "description": cov.description,
                "capabilities": meta.capabilities,
                "limitations": meta.limitations
            }
            thermal_list.append(info)
            if meta.availability == ProviderHealth.NOT_CONFIGURED:
                unconfigured.append(info)
            elif cov.is_global:
                global_orbiters.append(info)
            else:
                regional_geostationary.append(info)

        return {
            "region": region or "GLOBAL",
            "total_thermal_providers": len(thermal_list),
            "global_polar_orbiters": global_orbiters,
            "regional_geostationary": regional_geostationary,
            "unconfigured_providers": unconfigured,
            "providers": thermal_list
        }

    def build_evidence_availability_matrix(
        self,
        requested_aspects: Optional[List[str]] = None,
        region: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Builds the 5-state evidence availability matrix:
        AVAILABLE, MISSING, PARTIAL, STALE, CONFLICTING.
        Feeds directly into evidence strength and uncertainty analysis.
        """
        # Standard matrix mapping for AGNI-NETRA operational case
        matrix = {
            "THERMAL_HOTSPOTS": EvidenceAvailability.AVAILABLE.value,
            "INDUSTRIAL_FACILITIES": EvidenceAvailability.AVAILABLE.value,
            "POWER_UTILITY_REGISTRY": EvidenceAvailability.AVAILABLE.value,
            "ENVIRONMENTAL_CLEARANCES": EvidenceAvailability.PARTIAL.value,  # Partial because not all plants have online EC
            "MINING_LEASE_CONTEXT": EvidenceAvailability.AVAILABLE.value,
            "LAND_COVER_LULC": EvidenceAvailability.AVAILABLE.value,
            "PROTECTED_AREAS": EvidenceAvailability.AVAILABLE.value,
            "HISTORICAL_BASELINES": EvidenceAvailability.AVAILABLE.value,
            "WEATHER_METEOROLOGY": EvidenceAvailability.MISSING.value,
            "HIGH_RES_OPTICAL": EvidenceAvailability.MISSING.value,
        }

        # If outside India, regional datasets become MISSING
        if region and region.upper() not in ("INDIA", "IN", "BHARAT"):
            matrix["POWER_UTILITY_REGISTRY"] = EvidenceAvailability.MISSING.value
            matrix["ENVIRONMENTAL_CLEARANCES"] = EvidenceAvailability.MISSING.value
            matrix["MINING_LEASE_CONTEXT"] = EvidenceAvailability.MISSING.value
            matrix["PROTECTED_AREAS"] = EvidenceAvailability.MISSING.value

        return matrix


# Singleton accessor
provider_registry = ProviderRegistry()
