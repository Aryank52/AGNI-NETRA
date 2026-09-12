"""
AGNI-NETRA JARVIS Phase 16: Normalization Engine
Canonicalizes coordinates, timestamps, physical units, and spatial geometries
while strictly preserving original source values and units.
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, Union


class NormalizationEngine:
    """
    Deterministic Normalization Engine for Global Data Ingestion.
    """

    # -------------------------------------------------------------------------
    # 1. Coordinates Normalization & Validation (Section 13)
    # -------------------------------------------------------------------------
    @staticmethod
    def normalize_coordinates(lat_raw: Any, lon_raw: Any) -> Tuple[bool, Optional[float], Optional[float], Optional[str]]:
        """
        Enforces WGS84 bounds:
        lat in [-90.0, 90.0]
        lon in [-180.0, 180.0]
        Rejects NaN, Infinity, and non-numeric values.
        """
        try:
            if lat_raw is None or lon_raw is None:
                return False, None, None, "Missing latitude or longitude"
            lat = float(lat_raw)
            lon = float(lon_raw)
        except (ValueError, TypeError):
            return False, None, None, f"Invalid non-numeric coordinates: lat={lat_raw}, lon={lon_raw}"

        if math.isnan(lat) or math.isinf(lat) or math.isnan(lon) or math.isinf(lon):
            return False, None, None, f"NaN or Infinite coordinates detected: ({lat}, {lon})"

        if not (-90.0 <= lat <= 90.0):
            return False, None, None, f"Latitude {lat} out of valid range [-90.0, 90.0]"

        if not (-180.0 <= lon <= 180.0):
            return False, None, None, f"Longitude {lon} out of valid range [-180.0, 180.0]"

        return True, round(lat, 6), round(lon, 6), None

    # -------------------------------------------------------------------------
    # 2. Timestamp Normalization & Validation (Section 14)
    # -------------------------------------------------------------------------
    @staticmethod
    def normalize_timestamp(
        ts_raw: Any,
        date_str: Optional[str] = None,
        time_str: Optional[str] = None,
        max_future_skew_seconds: int = 300
    ) -> Tuple[bool, Optional[datetime], Optional[str], Optional[str]]:
        """
        Parses and converts timestamps into UTC ISO-8601.
        Rejects future timestamps (beyond skew allowance) and impossible dates.
        Returns: (is_valid, dt_utc, iso_string, error_msg)
        """
        if ts_raw is None and date_str is None:
            return False, None, None, "No timestamp or date provided"

        dt: Optional[datetime] = None

        if isinstance(ts_raw, datetime):
            dt = ts_raw
        elif isinstance(ts_raw, (int, float)):
            # Epoch timestamp
            try:
                dt = datetime.fromtimestamp(ts_raw, tz=timezone.utc)
            except (ValueError, OSError, OverflowError) as e:
                return False, None, None, f"Invalid epoch timestamp: {e}"
        elif isinstance(ts_raw, str) and ts_raw.strip():
            cleaned = ts_raw.strip().replace("Z", "+00:00")
            for fmt in (
                "%Y-%m-%d %H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d"
            ):
                try:
                    dt = datetime.strptime(cleaned, fmt)
                    break
                except ValueError:
                    continue
            if dt is None:
                try:
                    dt = datetime.fromisoformat(cleaned)
                except ValueError:
                    pass

        # If date_str and time_str provided separately (e.g. NASA FIRMS acq_date + acq_time)
        if dt is None and date_str:
            t_clean = (time_str or "0000").strip().zfill(4)
            try:
                dt = datetime.strptime(f"{date_str.strip()} {t_clean}", "%Y-%m-%d %H%M")
            except ValueError:
                pass

        if dt is None:
            return False, None, None, f"Could not parse timestamp from {ts_raw or (date_str, time_str)}"

        # Ensure UTC timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        # Check year validity
        if dt.year < 1970 or dt.year > 2100:
            return False, None, None, f"Timestamp year {dt.year} outside realistic operational range [1970, 2100]"

        # Check future timestamp
        now_utc = datetime.now(timezone.utc)
        if dt > now_utc + timedelta(seconds=max_future_skew_seconds):
            return False, None, None, f"Future timestamp detected: {dt.isoformat()} is ahead of system time {now_utc.isoformat()}"

        return True, dt, dt.isoformat(), None

    # -------------------------------------------------------------------------
    # 3. Units Normalization (Section 15)
    # -------------------------------------------------------------------------
    @staticmethod
    def normalize_unit(
        field_type: str,
        value: Any,
        source_unit: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Converts physical variables into standard canonical units:
        - temperature: Kelvin (K)
        - distance: Meters (m)
        - frp: Megawatts (MW)
        - wind_speed: Meters per second (m/s)
        - precipitation: Millimeters (mm)
        - pressure: Hectopascals (hPa)
        Returns structured dictionary preserving original and normalized context.
        """
        if value is None:
            return {
                "original_value": None,
                "original_unit": source_unit,
                "normalized_value": None,
                "normalized_unit": None
            }

        val = float(value)
        unit = (source_unit or "").strip().lower()

        if field_type == "temperature":
            # Target: Kelvin (K)
            if unit in ("c", "celsius", "degc"):
                norm_val = val + 273.15
            elif unit in ("f", "fahrenheit", "degf"):
                norm_val = (val - 32.0) * 5.0 / 9.0 + 273.15
            else:  # Assume K
                norm_val = val
            return {
                "original_value": val,
                "original_unit": source_unit or "K",
                "normalized_value": round(norm_val, 2),
                "normalized_unit": "K"
            }

        elif field_type == "distance":
            # Target: Meters (m)
            if unit in ("km", "kilometer", "kilometers"):
                norm_val = val * 1000.0
            elif unit in ("mi", "mile", "miles"):
                norm_val = val * 1609.344
            elif unit in ("ft", "feet"):
                norm_val = val * 0.3048
            else:
                norm_val = val
            return {
                "original_value": val,
                "original_unit": source_unit or "m",
                "normalized_value": round(norm_val, 2),
                "normalized_unit": "m"
            }

        elif field_type == "frp":
            # Target: Megawatts (MW)
            norm_val = val
            return {
                "original_value": val,
                "original_unit": source_unit or "MW",
                "normalized_value": round(norm_val, 2),
                "normalized_unit": "MW"
            }

        elif field_type == "wind_speed":
            # Target: m/s
            if unit in ("km/h", "kmh", "kph"):
                norm_val = val / 3.6
            elif unit in ("knots", "knot", "kt"):
                norm_val = val * 0.514444
            elif unit in ("mph", "miles/h"):
                norm_val = val * 0.44704
            else:
                norm_val = val
            return {
                "original_value": val,
                "original_unit": source_unit or "m/s",
                "normalized_value": round(norm_val, 2),
                "normalized_unit": "m/s"
            }

        elif field_type == "precipitation":
            # Target: Millimeters (mm)
            if unit in ("in", "inch", "inches"):
                norm_val = val * 25.4
            else:
                norm_val = val
            return {
                "original_value": val,
                "original_unit": source_unit or "mm",
                "normalized_value": round(norm_val, 2),
                "normalized_unit": "mm"
            }

        elif field_type == "pressure":
            # Target: Hectopascals (hPa)
            if unit in ("pa", "pascal"):
                norm_val = val / 100.0
            elif unit in ("bar",):
                norm_val = val * 1000.0
            elif unit in ("atm",):
                norm_val = val * 1013.25
            else:
                norm_val = val
            return {
                "original_value": val,
                "original_unit": source_unit or "hPa",
                "normalized_value": round(norm_val, 2),
                "normalized_unit": "hPa"
            }

        return {
            "original_value": val,
            "original_unit": source_unit or "RAW",
            "normalized_value": val,
            "normalized_unit": source_unit or "RAW"
        }

    # -------------------------------------------------------------------------
    # 4. Geometry Normalization (Section 16)
    # -------------------------------------------------------------------------
    @staticmethod
    def normalize_geometry(
        geom_raw: Optional[Dict[str, Any]] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        source_crs: str = "EPSG:4326"
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Produces canonical GeoJSON geometry (Point, LineString, Polygon, MultiPolygon)
        normalized to EPSG:4326 (WGS84).
        """
        if geom_raw and isinstance(geom_raw, dict) and "type" in geom_raw:
            g_type = geom_raw.get("type")
            coords = geom_raw.get("coordinates")
            if not coords:
                return False, None, f"Geometry of type {g_type} missing coordinates"
            return True, {
                "type": g_type,
                "coordinates": coords,
                "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
                "source_crs": source_crs
            }, None

        if lat is not None and lon is not None:
            return True, {
                "type": "Point",
                "coordinates": [round(lon, 6), round(lat, 6)],
                "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
                "source_crs": source_crs
            }, None

        return False, None, "Neither geometry object nor point coordinates provided"


normalization_engine = NormalizationEngine()
