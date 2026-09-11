"""
AGNI-NETRA Phase 6: Provider Abstraction Base Classes & Contracts
Defines standard provider interfaces, geographic coverage models, health statuses,
and capability contracts.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.services.intelligence.provenance import SourceProvenance


class CoverageType(str, Enum):
    GLOBAL = "GLOBAL"
    COUNTRY = "COUNTRY"
    REGION = "REGION"
    STATE = "STATE"
    DISTRICT = "DISTRICT"


class ProviderHealth(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"


class EvidenceAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    PARTIAL = "PARTIAL"
    STALE = "STALE"
    CONFLICTING = "CONFLICTING"


class GeographicCoverage(BaseModel):
    coverage_type: CoverageType
    countries: List[str] = Field(default_factory=list)
    states_provinces: List[str] = Field(default_factory=list)
    description: str
    is_global: bool = False


class ProviderMetadata(BaseModel):
    provider_name: str
    dataset_name: str
    capabilities: List[str] = Field(default_factory=list)
    geographic_coverage: GeographicCoverage
    temporal_coverage: Optional[str] = None
    update_frequency: Optional[str] = None
    availability: ProviderHealth = ProviderHealth.AVAILABLE
    source_provenance: Optional[str] = None
    limitations: Optional[str] = None
    is_authoritative: bool = True
    restricted_roles: List[str] = Field(default_factory=list)  # Roles excluded from viewing full internal metadata


class BaseIntelligenceProvider(ABC):
    """
    Core abstract base class for all AGNI-NETRA intelligence providers.
    """

    @abstractmethod
    def get_metadata(self) -> ProviderMetadata:
        """Returns factual machine-readable provider metadata."""
        pass

    @abstractmethod
    def get_coverage(self) -> GeographicCoverage:
        """Returns factual geographic coverage scope."""
        pass

    @abstractmethod
    def get_health(self, db: Optional[Session] = None) -> ProviderHealth:
        """Performs lightweight operational status check."""
        pass

    def is_available(self, db: Optional[Session] = None) -> bool:
        """Convenience helper returning True if provider is operational."""
        return self.get_health(db) in (ProviderHealth.AVAILABLE, ProviderHealth.DEGRADED)


# Specialized Contract Interfaces

class ThermalProvider(BaseIntelligenceProvider):
    @abstractmethod
    def query_detections(self, db: Session, bbox: Optional[List[float]] = None, limit: int = 100) -> List[Any]:
        pass

    @abstractmethod
    def get_detection_provenance(self, record_id: str) -> Optional[SourceProvenance]:
        pass


class FacilityProvider(BaseIntelligenceProvider):
    @abstractmethod
    def query_facilities(self, db: Session, state: Optional[str] = None, limit: int = 50) -> List[Any]:
        pass

    @abstractmethod
    def get_facility_by_id(self, db: Session, facility_id: str) -> Optional[Any]:
        pass


class MiningProvider(BaseIntelligenceProvider):
    @abstractmethod
    def query_mining_context(self, db: Session, state: str, district: Optional[str] = None) -> List[Any]:
        pass


class PowerProvider(BaseIntelligenceProvider):
    @abstractmethod
    def query_power_stations(self, db: Session, state: Optional[str] = None, prime_mover: Optional[str] = None) -> List[Any]:
        pass


class AdministrativeProvider(BaseIntelligenceProvider):
    @abstractmethod
    def resolve_admin_hierarchy(self, db: Session, lat: float, lon: float) -> Dict[str, Any]:
        pass


class LandCoverProvider(BaseIntelligenceProvider):
    @abstractmethod
    def get_landcover_at(self, db: Session, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        pass


class ProtectedAreaProvider(BaseIntelligenceProvider):
    @abstractmethod
    def check_protected_area_proximity(self, db: Session, lat: float, lon: float, buffer_km: float = 10.0) -> List[Dict[str, Any]]:
        pass


class HistoricalBaselineProvider(BaseIntelligenceProvider):
    @abstractmethod
    def get_baseline_for_facility(self, db: Session, facility_id: str) -> Optional[Dict[str, Any]]:
        pass
