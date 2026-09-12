"""
AGNI-NETRA JARVIS Phase 16: Provider-Neutral Ingestion Interface
Defines the standard contract for all upstream data sources and sensor streams.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Iterator, Tuple
from sqlalchemy.orm import Session

from backend.app.services.data_plane.models import (
    IngestionRecordSchema, IngestionBatchSchema, CoverageScope
)
from backend.app.services.intelligence.providers.base import ProviderHealth


class IngestionProvider(ABC):
    """
    Abstract base class establishing the provider-neutral ingestion contract.
    Decouples raw source acquisition from canonical intelligence representations.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Standard uppercase provider identifier (e.g. 'NASA_FIRMS', 'COPERNICUS', 'OSM')."""
        pass

    @property
    @abstractmethod
    def dataset_name(self) -> str:
        """Specific dataset / product identifier (e.g. 'NASA_FIRMS_VIIRS_NRT')."""
        pass

    @property
    @abstractmethod
    def coverage_scope(self) -> CoverageScope:
        """Geographic scope: GLOBAL, REGIONAL, NATIONAL, PARTIAL, NOT_CONFIGURED."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Returns provider catalog metadata, license, spatial/temporal resolution, and policies."""
        pass

    @abstractmethod
    def fetch(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        cursor: Optional[Dict[str, Any]] = None,
        limit: int = 1000,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Fetches raw telemetry / record payloads from the upstream source.
        Returns a list of raw dictionaries with provider-native keys.
        """
        pass

    @abstractmethod
    def validate_raw(self, raw_record: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Performs raw schema and type checks on the native provider payload.
        Returns (is_valid: bool, error_code: Optional[str], error_message: Optional[str]).
        """
        pass

    @abstractmethod
    def normalize(self, raw_record: Dict[str, Any], batch_id: str) -> IngestionRecordSchema:
        """
        Normalizes a valid raw record into a canonical IngestionRecordSchema.
        Must preserve native source_record_id and retain raw identity.
        """
        pass

    def yield_records(
        self,
        batch_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        cursor: Optional[Dict[str, Any]] = None,
        limit: int = 1000,
        **kwargs: Any
    ) -> Iterator[Dict[str, Any]]:
        """
        Generator yielding raw fetched records one by one.
        """
        records = self.fetch(start_time=start_time, end_time=end_time, cursor=cursor, limit=limit, **kwargs)
        for r in records:
            yield r

    @abstractmethod
    def report_health(self, db: Optional[Session] = None) -> ProviderHealth:
        """
        Returns truthful operational health status:
        AVAILABLE, DEGRADED, UNAVAILABLE, NOT_CONFIGURED, PARTIAL.
        """
        pass


# Type alias for validate_raw return
Tuple_Validation = tuple[bool, Optional[str], Optional[str]]
