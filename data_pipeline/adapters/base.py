from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class NormalizedThermalObservation(BaseModel):
    """
    Sensor-Agnostic Common Normalized Observation Schema
    Maps NASA FIRMS (VIIRS/MODIS), Sentinel-2, Landsat, or external GIS data.
    """
    source_record_id: Optional[str] = None
    source: str = "FIRMS"             # FIRMS, SENTINEL, LANDSAT, OSM, DEMO
    sensor: str = "VIIRS_NOAA20"      # VIIRS_NOAA20, VIIRS_SNPP, MODIS_AQUA, MODIS_TERRA, MSI_S2, TIRS_L8
    satellite: Optional[str] = "NOAA-20"
    latitude: float
    longitude: float
    acq_timestamp: datetime
    brightness: Optional[float] = None
    bright_t31: Optional[float] = None
    frp: float = Field(default=0.0, description="Fire Radiative Power in Megawatts (MW)")
    confidence: float = Field(default=80.0, description="Observation confidence percentage 0-100")
    day_night: str = Field(default="D", description="'D' for Day, 'N' for Night")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_demo: bool = False


class DataSourceAdapter(ABC):
    """
    Abstract Base Class for all external geospatial and remote sensing data sources.
    """

    @abstractmethod
    def fetch_data(self, **kwargs) -> List[NormalizedThermalObservation]:
        """Fetches raw records from API/file and returns normalized observations."""
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """Health check for data source availability."""
        pass
