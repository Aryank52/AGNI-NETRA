import csv
import io
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx
from data_pipeline.adapters.base import DataSourceAdapter, NormalizedThermalObservation


class FIRMSAdapter(DataSourceAdapter):
    """
    NASA FIRMS Adapter for VIIRS (375m) and MODIS (1km) Active Fire & Thermal Anomaly feeds.
    Supports live NASA EOSDIS API, local CSV uploads, and JSON datasets without requiring API keys.
    """

    def __init__(self, api_key: str = "", base_url: str = "https://firms.modaps.eosdis.nasa.gov/api/country/csv"):
        self.api_key = api_key.strip()
        self.base_url = base_url

    def validate_connection(self) -> bool:
        """
        Validates FIRMS API availability if key is configured.
        """
        if not self.api_key:
            return False
        try:
            resp = httpx.get(
                f"https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/{self.api_key}/VIIRS_NOAA20_NRT",
                timeout=5.0
            )
            return resp.status_code == 200
        except Exception:
            return False

    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """
        Validates latitude/longitude bounds for geographic validity and India subcontinent focus.
        """
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return False
        # Validates broad India geographic boundary (6.0N to 38.0N, 68.0E to 98.0E)
        if not (5.0 <= lat <= 39.0 and 65.0 <= lon <= 100.0):
            return False
        return True

    def deduplicate(self, observations: List[NormalizedThermalObservation]) -> List[NormalizedThermalObservation]:
        """
        Deduplicates satellite thermal observations by sensor, rounded coordinates, and acquisition time.
        """
        seen = set()
        deduped = []
        for obs in observations:
            # Hash key: (sensor, lat rounded to 4 decimals ~ 11m, lon rounded to 4 decimals, timestamp)
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

    def fetch_data(
        self,
        country: str = "IND",
        days: int = 1,
        source_type: str = "VIIRS_NOAA20_NRT"
    ) -> List[NormalizedThermalObservation]:
        """
        Fetches live FIRMS NRT CSV records for India from NASA EOSDIS API.
        """
        if not self.api_key:
            return []

        url = f"{self.base_url}/{self.api_key}/{source_type}/{country}/{days}"
        try:
            resp = httpx.get(url, timeout=30.0)
            if resp.status_code != 200:
                return []
            raw_obs = self.parse_csv_content(resp.text, source_name=source_type, is_demo=False)
            return self.deduplicate(raw_obs)
        except Exception:
            return []

    def parse_csv_content(
        self,
        csv_text: str,
        source_name: str = "VIIRS",
        is_demo: bool = False
    ) -> List[NormalizedThermalObservation]:
        """
        Parses FIRMS CSV strings (from NASA API or local file upload) into normalized observations.
        """
        observations = []
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        
        for row in reader:
            try:
                lat = float(row.get("latitude", 0.0))
                lon = float(row.get("longitude", 0.0))

                # Coordinate validation
                if not self.validate_coordinates(lat, lon):
                    continue

                frp = float(row.get("frp", 0.0) or 0.0)
                bright_ti4 = float(row.get("bright_ti4") or row.get("brightness") or 300.0)
                bright_ti5 = float(row.get("bright_ti5") or row.get("bright_t31") or 290.0)
                
                # Timestamp formatting
                acq_date = row.get("acq_date", "2026-01-01")
                acq_time = str(row.get("acq_time", "0000")).strip().zfill(4)
                dt_str = f"{acq_date} {acq_time[:2]}:{acq_time[2:]}:00"
                acq_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                
                # Confidence translation
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

                obs = NormalizedThermalObservation(
                    source_record_id=f"{source_name}_{lat:.4f}_{lon:.4f}_{acq_date}_{acq_time}",
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
        Parses structured JSON thermal records (from local files or API payloads).
        """
        observations = []
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

                obs = NormalizedThermalObservation(
                    source_record_id=item.get("source_record_id") or f"{source_name}_{lat:.4f}_{lon:.4f}",
                    source=item.get("source", "FIRMS"),
                    sensor=item.get("sensor", source_name),
                    satellite=item.get("satellite", "NOAA-20"),
                    latitude=lat,
                    longitude=lon,
                    acq_timestamp=acq_dt,
                    brightness=float(item.get("brightness", 320.0)),
                    bright_t31=float(item.get("bright_t31", 295.0)),
                    frp=float(item.get("frp", 10.0)),
                    confidence=float(item.get("confidence", 85.0)),
                    day_night=str(item.get("day_night", "D")).upper(),
                    metadata=item.get("metadata", {}),
                    is_demo=is_demo
                )
                observations.append(obs)
            except Exception:
                continue

        return self.deduplicate(observations)
