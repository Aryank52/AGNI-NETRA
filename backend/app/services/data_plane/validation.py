"""
AGNI-NETRA JARVIS Phase 16: Schema & Physical Validation Engine
Rigidly evaluates raw incoming records against schema constraints, coordinate limits,
and operational physics. Rejects or flags records for quarantine without silent mutations.
"""

from typing import Dict, Any, List, Tuple, Optional
from backend.app.services.data_plane.normalization import normalization_engine


class ValidationResult:
    def __init__(
        self,
        is_valid: bool,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        should_quarantine: bool = False,
        details: Optional[Dict[str, Any]] = None
    ):
        self.is_valid = is_valid
        self.error_code = error_code
        self.error_message = error_message
        self.should_quarantine = should_quarantine
        self.details = details or {}


class ValidationEngine:
    """
    Validates mandatory attributes, data types, physical ranges, and geodetic rules.
    """

    MANDATORY_FIELDS = ["provider", "dataset", "source_record_id"]

    @classmethod
    def validate_record(cls, record: Dict[str, Any]) -> ValidationResult:
        """
        Validates record schema, coordinates, timestamps, and physical ranges.
        """
        # 1. Mandatory Identity Fields
        for req in cls.MANDATORY_FIELDS:
            if not record.get(req):
                return ValidationResult(
                    is_valid=False,
                    error_code="MISSING_MANDATORY_FIELD",
                    error_message=f"Mandatory field '{req}' missing or empty",
                    should_quarantine=True
                )

        # 2. Coordinates Validation
        lat = record.get("latitude")
        lon = record.get("longitude")
        if lat is not None or lon is not None:
            c_valid, _, _, c_err = normalization_engine.normalize_coordinates(lat, lon)
            if not c_valid:
                return ValidationResult(
                    is_valid=False,
                    error_code="INVALID_COORDINATES",
                    error_message=c_err,
                    should_quarantine=True
                )

        # 3. Timestamp Validation
        ts_raw = record.get("observation_time") or record.get("acq_timestamp")
        date_str = record.get("acq_date")
        time_str = record.get("acq_time")
        if ts_raw is not None or date_str is not None:
            t_valid, _, _, t_err = normalization_engine.normalize_timestamp(ts_raw, date_str, time_str)
            if not t_valid:
                return ValidationResult(
                    is_valid=False,
                    error_code="INVALID_TIMESTAMP",
                    error_message=t_err,
                    should_quarantine=True
                )

        # 4. Physical Ranges for Thermal Telemetry
        if "frp" in record and record["frp"] is not None:
            try:
                frp = float(record["frp"])
                if frp < 0.0 or frp > 20000.0:
                    return ValidationResult(
                        is_valid=False,
                        error_code="PHYSICAL_OUT_OF_RANGE",
                        error_message=f"FRP value {frp} MW outside physical boundary [0.0, 20000.0]",
                        should_quarantine=True
                    )
            except (ValueError, TypeError):
                return ValidationResult(
                    is_valid=False,
                    error_code="INVALID_NUMERIC_FRP",
                    error_message=f"Non-numeric FRP value: {record['frp']}",
                    should_quarantine=True
                )

        if "brightness" in record and record["brightness"] is not None:
            try:
                bright = float(record["brightness"])
                if bright < 150.0 or bright > 650.0:
                    return ValidationResult(
                        is_valid=False,
                        error_code="PHYSICAL_OUT_OF_RANGE",
                        error_message=f"Brightness temperature {bright}K outside sensor envelope [150K, 650K]",
                        should_quarantine=True
                    )
            except (ValueError, TypeError):
                return ValidationResult(
                    is_valid=False,
                    error_code="INVALID_NUMERIC_BRIGHTNESS",
                    error_message=f"Non-numeric brightness value: {record['brightness']}",
                    should_quarantine=True
                )

        return ValidationResult(is_valid=True)


validation_engine = ValidationEngine()
