"""
AGNI-NETRA JARVIS Phase 16: Quality Control Engine
Executes deterministic multi-dimensional quality assessment:
- RANGE_CHECK
- TEMPORAL_CHECK
- SPATIAL_CHECK
- SCHEMA_CHECK
- DUPLICATE_CHECK
- PROVENANCE_CHECK
- PROVIDER_CHECK
Emits PASS, WARN, or FAIL without silently discarding records marked WARN.
"""

from typing import Dict, Any, List, Tuple
from backend.app.services.data_plane.models import QualityStatus


class QualityControlResult:
    def __init__(
        self,
        status: QualityStatus,
        reasons: List[str],
        check_details: Dict[str, Any]
    ):
        self.status = status
        self.reasons = reasons
        self.check_details = check_details


class QualityControlEngine:
    """
    Evaluates records against 7 deterministic quality criteria.
    """

    @classmethod
    def evaluate(
        cls,
        record: Dict[str, Any],
        is_duplicate: bool = False,
        provenance_present: bool = True,
        provider_known: bool = True
    ) -> QualityControlResult:
        reasons: List[str] = []
        checks: Dict[str, str] = {}
        has_fail = False
        has_warn = False

        # 1. SCHEMA_CHECK
        if not record.get("provider") or not record.get("dataset") or not record.get("source_record_id"):
            checks["SCHEMA_CHECK"] = "FAIL"
            reasons.append("Missing core schema identification attributes")
            has_fail = True
        else:
            checks["SCHEMA_CHECK"] = "PASS"

        # 2. SPATIAL_CHECK
        lat = record.get("latitude")
        lon = record.get("longitude")
        if lat is None or lon is None:
            checks["SPATIAL_CHECK"] = "FAIL"
            reasons.append("Missing geographic coordinates")
            has_fail = True
        elif not (-90.0 <= float(lat) <= 90.0 and -180.0 <= float(lon) <= 180.0):
            checks["SPATIAL_CHECK"] = "FAIL"
            reasons.append(f"Coordinates ({lat}, {lon}) out of bounds")
            has_fail = True
        else:
            checks["SPATIAL_CHECK"] = "PASS"

        # 3. TEMPORAL_CHECK
        obs_time = record.get("observation_time")
        if not obs_time:
            checks["TEMPORAL_CHECK"] = "WARN"
            reasons.append("Missing explicit observation timestamp; retrieval time used as fallback")
            has_warn = True
        else:
            checks["TEMPORAL_CHECK"] = "PASS"

        # 4. RANGE_CHECK (physical values)
        confidence = record.get("confidence")
        if confidence is not None:
            try:
                c_val = float(confidence)
                if c_val < 30.0:
                    checks["RANGE_CHECK"] = "WARN"
                    reasons.append(f"Low detection confidence ({c_val}%)")
                    has_warn = True
                else:
                    checks["RANGE_CHECK"] = "PASS"
            except (ValueError, TypeError):
                checks["RANGE_CHECK"] = "FAIL"
                reasons.append(f"Invalid confidence value: {confidence}")
                has_fail = True
        else:
            checks["RANGE_CHECK"] = "PASS"

        # 5. DUPLICATE_CHECK
        if is_duplicate:
            checks["DUPLICATE_CHECK"] = "WARN"
            reasons.append("Record identified as duplicate; preserved for relational integrity")
            has_warn = True
        else:
            checks["DUPLICATE_CHECK"] = "PASS"

        # 6. PROVENANCE_CHECK
        if not provenance_present:
            checks["PROVENANCE_CHECK"] = "WARN"
            reasons.append("Provenance lineage incomplete or provisional")
            has_warn = True
        else:
            checks["PROVENANCE_CHECK"] = "PASS"

        # 7. PROVIDER_CHECK
        if not provider_known:
            checks["PROVIDER_CHECK"] = "WARN"
            reasons.append("Provider not registered in authoritative dataset catalog")
            has_warn = True
        else:
            checks["PROVIDER_CHECK"] = "PASS"

        # Final Status Synthesis
        if has_fail:
            status = QualityStatus.FAIL
        elif has_warn:
            status = QualityStatus.WARN
        else:
            status = QualityStatus.PASS

        return QualityControlResult(status=status, reasons=reasons, check_details=checks)


quality_control_engine = QualityControlEngine()
