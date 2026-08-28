import csv
import io
import time
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
import httpx

from data_pipeline.adapters.base import (
    ThermalSourceAdapter, NormalizedThermalObservation, SourceProvenance
)
from backend.app.core.config import settings


# Supported NASA FIRMS Sensors
DEFAULT_FIRMS_SENSORS = [
    "VIIRS_NOAA21_NRT",
    "VIIRS_NOAA20_NRT",
    "VIIRS_SNPP_NRT",
    "MODIS_NRT"
]

# Canonical India Subcontinent Bounding Box [min_lat, min_lon, max_lat, max_lon]
INDIA_BBOX = (6.0, 68.0, 37.5, 97.5)


class FIRMSAdapter(ThermalSourceAdapter):
    """
    NASA FIRMS (EOSDIS) Production Ingestion Adapter.
    Supports VIIRS (NOAA-21, NOAA-20, Suomi-NPP @ 375m) and MODIS (Terra/Aqua @ 1km).
    Features:
    - Bounding-box and national country queries
    - Multi-sensor configurable ingestion
    - Retry logic with exponential backoff & rate-limiting protection
    - Duplicate detection via spatial-temporal coordinate hash
    - Standardized SourceProvenance & DataQuality indicators
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://firms.modaps.eosdis.nasa.gov/api"
    ):
        self.api_key = (api_key if api_key is not None else settings.FIRMS_MAP_KEY).strip()
        self.base_url = base_url.rstrip("/")
        self._max_retries = 3
        self._backoff_factor = 1.5

    @property
    def source_name(self) -> str:
        return "NASA_FIRMS"

    def validate_connection(self) -> Dict[str, Any]:
        """
        Validates FIRMS API availability and authentication status.
        """
        if not self.api_key:
            return {
                "source": self.source_name,
                "status": "NOT_CONFIGURED",
                "configured": False,
                "message": "FIRMS_MAP_KEY environment variable is not set. Operating in verified demo mode.",
                "latency_ms": 0
            }

        start_time = time.time()
        try:
            url = f"{self.base_url}/data_availability/csv/{self.api_key}/VIIRS_NOAA20_NRT"
            resp = httpx.get(url, timeout=6.0)
            latency = int((time.time() - start_time) * 1000)

            if resp.status_code == 200:
                return {
                    "source": self.source_name,
                    "status": "HEALTHY",
                    "configured": True,
                    "message": "NASA EOSDIS FIRMS API is online and authenticated.",
                    "latency_ms": latency
                }
            elif resp.status_code in (401, 403):
                return {
                    "source": self.source_name,
                    "status": "UNAUTHORIZED",
                    "configured": True,
                    "message": "Invalid FIRMS_MAP_KEY credentials.",
                    "latency_ms": latency
                }
            else:
                return {
                    "source": self.source_name,
                    "status": "DEGRADED",
                    "configured": True,
                    "message": f"NASA API returned HTTP {resp.status_code}",
                    "latency_ms": latency
                }
        except Exception as e:
            return {
                "source": self.source_name,
                "status": "UNAVAILABLE",
                "configured": True,
                "message": f"Connection error: {str(e)}",
                "latency_ms": int((time.time() - start_time) * 1000)
            }

    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """
        Validates latitude/longitude bounds for broad India geographic scope.
        """
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return False
        # Broad India subcontinent + coastal EEZ envelope (5.0N to 39.0N, 65.0E to 100.0E)
        return (5.0 <= lat <= 39.0 and 65.0 <= lon <= 100.0)

    def deduplicate(self, observations: List[NormalizedThermalObservation]) -> List[NormalizedThermalObservation]:
        """
        Deduplicates satellite observations by sensor, rounded coordinates (~11m), and acquisition minute.
        """
        seen = set()
        deduped = []
        for obs in observations:
            key = (
                obs.sensor,
                round(obs.latitude, 4),
                round(obs.longitude, 4),
                obs.acq_timestamp.strftime("%Y-%m-%d %H:%M")
            )
            if key not in seen:
                seen.add(key)
                deduped.append(obs)
        return deduped

    def fetch_thermal_observations(
        self,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        date_str: Optional[str] = None,
        sensor: Optional[str] = None,
        incremental_since: Optional[datetime] = None,
        country: str = "IND",
        days: int = 1,
        **kwargs
    ) -> List[NormalizedThermalObservation]:
        """
        Fetches satellite thermal observations with retry backoff and rate limiting.
        """
        if not self.api_key:
            return []

        active_sensor = sensor or "VIIRS_NOAA20_NRT"
        
        # Build URL for area bbox or country
        if bbox:
            # NASA FIRMS Area API format: /api/area/csv/[MAP_KEY]/[SOURCE]/[W_LON],[S_LAT],[E_LON],[N_LAT]/[DAY_RANGE]
            min_lat, min_lon, max_lat, max_lon = bbox
            url = f"{self.base_url}/area/csv/{self.api_key}/{active_sensor}/{min_lon},{min_lat},{max_lon},{max_lat}/{days}"
        else:
            # NASA FIRMS Country API format: /api/country/csv/[MAP_KEY]/[SOURCE]/[COUNTRY]/[DAY_RANGE]
            url = f"{self.base_url}/country/csv/{self.api_key}/{active_sensor}/{country}/{days}"

        if date_str:
            url += f"/{date_str}"

        # Execute HTTP GET with Exponential Backoff
        for attempt in range(1, self._max_retries + 1):
            try:
                resp = httpx.get(url, timeout=30.0)
                if resp.status_code == 200:
                    raw_obs = self.parse_csv_content(resp.text, source_name=active_sensor, is_demo=False)
                    # Filter incremental if requested
                    if incremental_since:
                        raw_obs = [o for o in raw_obs if o.acq_timestamp > incremental_since]
                    return self.deduplicate(raw_obs)
                elif resp.status_code == 429:
                    # Rate limit encountered: backoff and retry
                    time.sleep(self._backoff_factor ** attempt)
                    continue
                else:
                    break
            except Exception:
                if attempt < self._max_retries:
                    time.sleep(self._backoff_factor ** attempt)
                else:
                    break

        return []

    def fetch_data(
        self,
        country: str = "IND",
        days: int = 1,
        source_type: str = "VIIRS_NOAA20_NRT"
    ) -> List[NormalizedThermalObservation]:
        """
        Backward-compatible interface for standard country queries.
        """
        return self.fetch_thermal_observations(
            country=country,
            days=days,
            sensor=source_type
        )

    def parse_csv_content(
        self,
        csv_text: str,
        source_name: str = "VIIRS",
        is_demo: bool = False
    ) -> List[NormalizedThermalObservation]:
        """
        Parses NASA FIRMS CSV telemetry strings into normalized observations with full provenance.
        """
        observations = []
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        ingestion_time = datetime.now(timezone.utc)
        
        for row in reader:
            try:
                lat = float(row.get("latitude", 0.0))
                lon = float(row.get("longitude", 0.0))

                if not self.validate_coordinates(lat, lon):
                    continue

                frp = float(row.get("frp", 0.0) or 0.0)
                bright_ti4 = float(row.get("bright_ti4") or row.get("brightness") or 300.0)
                bright_ti5 = float(row.get("bright_ti5") or row.get("bright_t31") or 290.0)
                
                acq_date = row.get("acq_date", "2026-01-01")
                acq_time = str(row.get("acq_time", "0000")).strip().zfill(4)
                dt_str = f"{acq_date} {acq_time[:2]}:{acq_time[2:]}:00"
                acq_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                
                # Confidence score translation
                conf_raw = str(row.get("confidence", "n")).lower().strip()
                if conf_raw == "l":
                    conf_val = 30.0
                elif conf_raw == "n":
                    conf_val = 65.0
                elif conf_raw == "h":
                    conf_val = 95.0
                else:
                    try:
                        conf_val = float(conf_raw)
                    except ValueError:
                        conf_val = 50.0

                dn = str(row.get("daynight", "D")).upper().strip()
                satellite = row.get("satellite", "NOAA-20")
                record_id = f"FIRMS_{source_name}_{lat:.4f}_{lon:.4f}_{acq_date}_{acq_time}"

                # Calculate objective Data Quality Score (0.0 to 1.0)
                quality_score = min(1.0, max(0.2, (conf_val / 100.0) * (1.0 if bright_ti4 > 300 else 0.85)))

                provenance = SourceProvenance(
                    source_name=f"NASA_FIRMS_{source_name}",
                    source_record_id=record_id,
                    source_version="NRT-v2.0",
                    acquisition_time=acq_dt,
                    ingestion_time=ingestion_time,
                    raw_reference="NASA_EOSDIS_API",
                    data_quality_score=quality_score,
                    additional_metadata={
                        "scan": row.get("scan"),
                        "track": row.get("track"),
                        "version": row.get("version")
                    }
                )

                obs = NormalizedThermalObservation(
                    source_record_id=record_id,
                    source="FIRMS",
                    sensor=source_name,
                    satellite=satellite,
                    latitude=lat,
                    longitude=lon,
                    acq_timestamp=acq_dt,
                    brightness=bright_ti4,
                    bright_t31=bright_ti5,
                    frp=frp,
                    confidence=conf_val,
                    day_night=dn,
                    provenance=provenance,
                    metadata=dict(row),
                    is_demo=is_demo
                )
                observations.append(obs)
            except Exception:
                continue

        return self.deduplicate(observations)

    def parse_json_content(
        self,
        json_data: List[Dict[str, Any]],
        source_name: str = "VIIRS_JSON",
        is_demo: bool = False
    ) -> List[NormalizedThermalObservation]:
        """
        Parses structured JSON thermal records into normalized observations.
        """
        observations = []
        ingestion_time = datetime.now(timezone.utc)

        for item in json_data:
            try:
                lat = float(item.get("latitude", 0.0))
                lon = float(item.get("longitude", 0.0))
                if not self.validate_coordinates(lat, lon):
                    continue

                acq_dt_raw = item.get("acq_timestamp")
                if isinstance(acq_dt_raw, str):
                    acq_dt = datetime.fromisoformat(acq_dt_raw.replace("Z", "+00:00"))
                elif isinstance(acq_dt_raw, datetime):
                    acq_dt = acq_dt_raw
                else:
                    acq_dt = datetime.now(timezone.utc)

                record_id = item.get("source_record_id") or f"{source_name}_{lat:.4f}_{lon:.4f}_{acq_dt.strftime('%Y%m%d%H%M')}"
                conf_val = float(item.get("confidence", 85.0))
                quality_score = min(1.0, max(0.3, conf_val / 100.0))

                provenance = SourceProvenance(
                    source_name=f"NASA_FIRMS_{source_name}",
                    source_record_id=record_id,
                    source_version="NRT-v2.0",
                    acquisition_time=acq_dt,
                    ingestion_time=ingestion_time,
                    raw_reference="JSON_PAYLOAD",
                    data_quality_score=quality_score
                )

                obs = NormalizedThermalObservation(
                    source_record_id=record_id,
                    source=item.get("source", "FIRMS"),
                    sensor=item.get("sensor", source_name),
                    satellite=item.get("satellite", "NOAA-20"),
                    latitude=lat,
                    longitude=lon,
                    acq_timestamp=acq_dt,
                    brightness=float(item.get("brightness", 320.0)),
                    bright_t31=float(item.get("bright_t31", 295.0)),
                    frp=float(item.get("frp", 10.0)),
                    confidence=conf_val,
                    day_night=str(item.get("day_night", "D")).upper(),
                    provenance=provenance,
                    metadata=item.get("metadata", {}),
                    is_demo=is_demo
                )
                observations.append(obs)
            except Exception:
                continue

        return self.deduplicate(observations)


firms_adapter = FIRMSAdapter()
