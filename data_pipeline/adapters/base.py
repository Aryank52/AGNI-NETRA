from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class SourceProvenance(BaseModel):
    """
    Provenance tracking metadata for every ingested geospatial and thermal record.
    """
    source_name: str                  # e.g., "NASA_FIRMS", "OSM", "ISRO_BHUVAN", "COPERNICUS_SENTINEL"
    source_record_id: Optional[str] = None
    source_version: Optional[str] = "v1.0"
    acquisition_time: datetime
    ingestion_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_reference: Optional[str] = None  # URL or bucket path to raw unparsed file
    provenance_hash: Optional[str] = None
    data_quality_score: float = Field(default=1.0, ge=0.0, le=1.0)
    additional_metadata: Dict[str, Any] = Field(default_factory=dict)


class NormalizedThermalObservation(BaseModel):
    """
    Sensor-Agnostic Common Normalized Observation Schema.
    Standardizes NASA FIRMS (VIIRS/MODIS), MOSDAC (INSAT-3D/3DR), Sentinel-2 SWIR, and Landsat TIRS.
    """
    source_record_id: Optional[str] = None
    source: str = "FIRMS"             # FIRMS, MOSDAC, SENTINEL, LANDSAT, DEMO, CSV_UPLOAD
    sensor: str = "VIIRS_NOAA20"      # VIIRS_NOAA21, VIIRS_NOAA20, VIIRS_SNPP, MODIS_AQUA, MODIS_TERRA, INSAT_3D, MSI_S2, TIRS_L8
    satellite: Optional[str] = "NOAA-20"
    latitude: float
    longitude: float
    acq_timestamp: datetime
    brightness: Optional[float] = None
    bright_t31: Optional[float] = None
    frp: float = Field(default=0.0, description="Fire Radiative Power in Megawatts (MW)")
    confidence: float = Field(default=80.0, description="Observation confidence percentage (0-100)")
    day_night: str = Field(default="D", description="'D' for Day, 'N' for Night")
    scan_angle: Optional[float] = None
    track_pixel_size_m: Optional[float] = 375.0
    provenance: Optional[SourceProvenance] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_demo: bool = False


class NormalizedFacilityRecord(BaseModel):
    """
    Normalized industrial facility schema across OpenStreetMap, State Pollution Boards, and Central Electricity Authority.
    """
    source: str = "OSM"               # OSM, CEA, SPCB, CPCB, USER_PROMOTED
    source_id: str
    name: str
    facility_type: str                # REFINERY, POWER_PLANT, STEEL_PLANT, CHEMICAL, CEMENT, MINING, LNG_GAS, OTHER
    operator: Optional[str] = None
    state: str
    district: Optional[str] = None
    latitude: float
    longitude: float
    boundary_geojson: Optional[Dict[str, Any]] = None
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    operating_status: str = "OPERATIONAL"  # OPERATIONAL, MAINTENANCE, DECOMMISSIONED
    provenance: Optional[SourceProvenance] = None
    raw_tags: Dict[str, Any] = Field(default_factory=dict)


class NormalizedImageryMetadata(BaseModel):
    """
    Standardized satellite scene metadata for Sentinel-2, Landsat-8/9, and PlanetScope.
    """
    source: str                       # SENTINEL_2, LANDSAT_8, LANDSAT_9
    product_id: str
    satellite: str
    acquisition_time: datetime
    cloud_cover_percentage: float = 0.0
    bounding_box: List[float] = Field(default_factory=list) # [min_lat, min_lon, max_lat, max_lon]
    optical_bands: List[str] = Field(default_factory=list)  # ["B02", "B03", "B04"]
    swir_bands: List[str] = Field(default_factory=list)     # ["B11", "B12"]
    thermal_bands: List[str] = Field(default_factory=list)  # ["B10"]
    preview_url: Optional[str] = None
    stac_item_url: Optional[str] = None
    provenance: Optional[SourceProvenance] = None


class NormalizedLULCRecord(BaseModel):
    """
    Normalized Land Use / Land Cover category and spatial buffer metrics.
    """
    category: str                     # Industrial, Forest, Agricultural, Urban, Barren, Water, Mining
    zone_code: int
    zone_description: str
    is_industrial_zone: bool
    distance_to_forest_m: float
    distance_to_agri_m: float
    distance_to_settlement_m: float
    distance_to_water_m: float
    distance_to_mine_m: float
    provenance: Optional[SourceProvenance] = None


# =========================================================================
# Abstract Adapter Interfaces
# =========================================================================

class DataSourceAdapter(ABC):
    """
    Root Abstract Base Class for all external geospatial and remote sensing data sources.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Returns canonical name of data source (e.g. 'NASA_FIRMS', 'OSM', 'BHUVAN')."""
        pass

    @abstractmethod
    def validate_connection(self) -> Dict[str, Any]:
        """Health check for data source connectivity and authentication status."""
        pass


class ThermalSourceAdapter(DataSourceAdapter):
    """
    Abstract adapter interface for thermal hotspot observation sources (FIRMS, MOSDAC).
    """

    @abstractmethod
    def fetch_thermal_observations(
        self,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        date_str: Optional[str] = None,
        sensor: Optional[str] = None,
        incremental_since: Optional[datetime] = None,
        **kwargs
    ) -> List[NormalizedThermalObservation]:
        """Fetches and normalizes satellite thermal observations."""
        pass


class FacilitySourceAdapter(DataSourceAdapter):
    """
    Abstract adapter interface for industrial facility registries (OSM, CEA, SPCB).
    """

    @abstractmethod
    def fetch_facilities(
        self,
        state: Optional[str] = None,
        facility_types: Optional[List[str]] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        **kwargs
    ) -> List[NormalizedFacilityRecord]:
        """Fetches and standardizes industrial facility records."""
        pass


class ImagerySourceAdapter(DataSourceAdapter):
    """
    Abstract adapter interface for event-driven optical, SWIR, and thermal imagery catalogs.
    """

    @abstractmethod
    def search_imagery_for_event(
        self,
        latitude: float,
        longitude: float,
        target_time: datetime,
        buffer_km: float = 3.0,
        time_window_days: int = 3,
        max_cloud_cover: float = 20.0,
        **kwargs
    ) -> List[NormalizedImageryMetadata]:
        """Queries STAC catalog for satellite scenes intersecting the event AOI."""
        pass


class LandCoverSourceAdapter(DataSourceAdapter):
    """
    Abstract adapter interface for LULC raster and vector classification services.
    """

    @abstractmethod
    def classify_location(
        self,
        latitude: float,
        longitude: float
    ) -> NormalizedLULCRecord:
        """Determines LULC category and computes distances to sensitive buffers."""
        pass
