import csv
import io
from datetime import datetime, timezone
from typing import List, Dict, Any
import httpx
from data_pipeline.adapters.base import DataSourceAdapter, NormalizedThermalObservation


class FIRMSAdapter(DataSourceAdapter):
    """
    NASA FIRMS Adapter for VIIRS and MODIS active fire & thermal anomaly products.
    """

    def __init__(self, api_key: str = "", base_url: str = "https://firms.modaps.eosdis.nasa.gov/api/country/csv"):
        self.api_key = api_key
        self.base_url = base_url

    def validate_connection(self) -> bool:
        if not self.api_key:
            return False
        try:
            # Check FIRMS API transaction status
            resp = httpx.get(f"https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv/{self.api_key}/VIIRS_NOAA20_NRT", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    def fetch_data(self, country: str = "IND", days: int = 1, source_type: str = "VIIRS_NOAA20_NRT") -> List[NormalizedThermalObservation]:
        """
        Fetches FIRMS NRT CSV records for India and normalizes to NormalizedThermalObservation.
        """
        if not self.api_key:
            return []

        url = f"{self.base_url}/{self.api_key}/{source_type}/{country}/{days}"
        try:
            resp = httpx.get(url, timeout=25.0)
            if resp.status_code != 200:
                return []
            
            return self.parse_csv_content(resp.text, source_name=source_type)
        except Exception:
            return []

    def parse_csv_content(self, csv_text: str, source_name: str = "VIIRS") -> List[NormalizedThermalObservation]:
        """
        Parses FIRMS CSV strings into normalized objects.
        """
        observations = []
        reader = csv.DictReader(io.StringIO(csv_text))
        
        for row in reader:
            try:
                lat = float(row.get("latitude", 0.0))
                lon = float(row.get("longitude", 0.0))
                frp = float(row.get("frp", 0.0))
                bright_ti4 = float(row.get("bright_ti4") or row.get("brightness") or 300.0)
                bright_ti5 = float(row.get("bright_ti5") or row.get("bright_t31") or 290.0)
                
                # Timestamp formatting
                acq_date = row.get("acq_date", "2026-01-01")
                acq_time = row.get("acq_time", "0000").zfill(4)
                dt_str = f"{acq_date} {acq_time[:2]}:{acq_time[2:]}:00"
                acq_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                
                # Confidence translation
                conf_raw = row.get("confidence", "n")
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

                dn = row.get("daynight", "D").upper()
                satellite = row.get("satellite", "NOAA-20")

                obs = NormalizedThermalObservation(
                    source_record_id=f"{source_name}_{lat:.4f}_{lon:.4f}_{acq_time}",
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
                    is_demo=False
                )
                observations.append(obs)
            except Exception:
                continue

        return observations
