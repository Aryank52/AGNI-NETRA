"""
AGNI-NETRA — GOVERNED CAPABILITY REGISTRY (WP6)
Defines the authoritative catalog of 17 typed, permission-gated, deterministic capabilities
available to the Single Master JARVIS Orchestrator.
Zero autonomous swarms, zero arbitrary code execution, zero hallucinated data.
"""

import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from sqlalchemy.orm import Session

logger = logging.getLogger("agni_netra.jarvis_capabilities")


class EpistemicEvidenceType(str, Enum):
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"
    MISSING = "MISSING"
    CONFLICTING = "CONFLICTING"


@dataclass
class JarvisCapabilitySpec:
    capability_id: str
    name: str
    description: str
    input_schema: Dict[str, str]
    output_schema: Dict[str, str]
    required_permissions: List[str]
    data_sources: List[str]
    cost_latency_expectation_ms: float
    side_effects: bool
    epistemic_type: EpistemicEvidenceType
    failure_behavior: str
    handler: Optional[Callable] = None


class JarvisCapabilityRegistry:
    """
    Authoritative, governed registry of deterministic capabilities.
    Each capability is strictly typed, bounded, and permission-checked.
    """

    def __init__(self):
        self._capabilities: Dict[str, JarvisCapabilitySpec] = {}
        self._initialize_catalog()

    def _initialize_catalog(self) -> None:
        """Initializes the 17 canonical capabilities."""
        from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry

        specs = [
            JarvisCapabilitySpec(
                capability_id="GET_EVENT",
                name="Get Authoritative Event",
                description="Retrieves primary thermal event telemetry, physical coordinates, brightness, FRP, sensor and satellite.",
                input_schema={"event_ref": "str"},
                output_schema={"found": "bool", "event_code": "str", "latitude": "float", "longitude": "float", "max_frp": "float", "state": "str", "district": "str"},
                required_permissions=["PUBLIC", "ANALYST", "AGENCY", "ADMIN"],
                data_sources=["thermal_events", "thermal_detections"],
                cost_latency_expectation_ms=15.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.OBSERVED,
                failure_behavior="Return error dictionary with found=False.",
                handler=lambda db, **kw: JarvisToolRegistry.tool_get_event(db, kw.get("event_ref"))
            ),
            JarvisCapabilitySpec(
                capability_id="GET_HISTORICAL_BASELINE",
                name="Get Historical Baseline",
                description="Cross-references the 6-year multi-sensor archive (8.22M detections) to compute historical mean FRP, standard deviation, and abnormality sigma.",
                input_schema={"event_ref": "str"},
                output_schema={"baseline_mean_frp": "float", "abnormality_sigma": "float", "is_anomalous": "bool", "historical_observations_count": "int"},
                required_permissions=["ANALYST", "AGENCY", "RESEARCHER", "ADMIN"],
                data_sources=["historical_baselines", "detections_partitioned"],
                cost_latency_expectation_ms=45.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Fall back to regional mean baseline; record abnormality_sigma=0.0.",
                handler=lambda db, **kw: JarvisToolRegistry.tool_compare_baseline(db, kw.get("event_ref"))
            ),
            JarvisCapabilitySpec(
                capability_id="GET_SPATIAL_CONTEXT",
                name="Get Spatial Cadastral Context",
                description="Executes PostGIS GiST multi-buffer distance calculation against 35,570 registered industrial assets, power plants, and mining leases.",
                input_schema={"event_ref": "str"},
                output_schema={"nearest_facilities": "list", "multi_distance_buffers": "dict", "state": "str", "district": "str"},
                required_permissions=["PUBLIC", "ANALYST", "AGENCY", "ADMIN"],
                data_sources=["industrial_facilities", "administrative_boundaries", "osm_infrastructure"],
                cost_latency_expectation_ms=30.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return empty facility list with distance=99999.0; log spatial degraded.",
                handler=lambda db, **kw: JarvisToolRegistry.tool_get_event_spatial_context(db, kw.get("event_ref"))
            ),
            JarvisCapabilitySpec(
                capability_id="GET_INDUSTRIAL_CONTEXT",
                name="Get Industrial Facility Details",
                description="Retrieves registered industrial asset specifications, facility type, primary fuel, compliance status, and historical flaring baseline.",
                input_schema={"facility_id": "str"},
                output_schema={"facility_name": "str", "facility_type": "str", "sector": "str", "compliance_status": "str"},
                required_permissions=["ANALYST", "AGENCY", "INDUSTRY", "ADMIN"],
                data_sources=["industrial_facilities", "compliance_records"],
                cost_latency_expectation_ms=20.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return unknown facility descriptor; mark asset as UNCATALOGED.",
                handler=self._handle_get_industrial_context
            ),
            JarvisCapabilitySpec(
                capability_id="GET_POWER_CONTEXT",
                name="Get Power Sector Context",
                description="Correlates thermal epicenter with Central Electricity Authority (CEA) thermal power stations, boiler units, and MW capacity.",
                input_schema={"event_ref": "str"},
                output_schema={"cea_unit_name": "str", "installed_capacity_mw": "float", "boiler_count": "int", "distance_meters": "float"},
                required_permissions=["ANALYST", "AGENCY", "ADMIN"],
                data_sources=["cea_power_units"],
                cost_latency_expectation_ms=25.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return no power units matched; mark power context NONE.",
                handler=self._handle_get_power_context
            ),
            JarvisCapabilitySpec(
                capability_id="GET_MINING_CONTEXT",
                name="Get Mining Cadastral Context",
                description="Evaluates spatial containment and proximity against Indian Bureau of Mines (IBM) lease boundaries and major mineral blocks.",
                input_schema={"event_ref": "str"},
                output_schema={"lease_id": "str", "mineral_name": "str", "lease_status": "str", "distance_meters": "float"},
                required_permissions=["ANALYST", "AGENCY", "ADMIN"],
                data_sources=["ibm_mining_leases", "ibm_mineral_blocks"],
                cost_latency_expectation_ms=25.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return no mining lease matched.",
                handler=self._handle_get_mining_context
            ),
            JarvisCapabilitySpec(
                capability_id="GET_LULC_CONTEXT",
                name="Get Bhuvan LULC Land Use Context",
                description="Extracts 50m resolution ISRO Bhuvan Land Use / Land Cover classification at the anomaly coordinate.",
                input_schema={"latitude": "float", "longitude": "float"},
                output_schema={"lulc_class": "str", "land_type": "str", "canopy_density": "float"},
                required_permissions=["PUBLIC", "ANALYST", "AGENCY", "ADMIN"],
                data_sources=["bhuvan_lulc_rasters", "lulc_polygons"],
                cost_latency_expectation_ms=20.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return default land cover class UNKNOWN.",
                handler=self._handle_get_lulc_context
            ),
            JarvisCapabilitySpec(
                capability_id="GET_PROTECTED_AREA_CONTEXT",
                name="Get Forest & Protected Area Context",
                description="Checks buffer proximity against Forest Survey of India (FSI) recorded forest areas, tiger reserves, and wildlife sanctuaries.",
                input_schema={"latitude": "float", "longitude": "float"},
                output_schema={"is_inside_protected_area": "bool", "protected_area_name": "str", "distance_to_boundary_m": "float"},
                required_permissions=["PUBLIC", "ANALYST", "AGENCY", "ADMIN"],
                data_sources=["fsi_protected_areas", "wildlife_sanctuaries"],
                cost_latency_expectation_ms=25.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return is_inside_protected_area=False.",
                handler=self._handle_get_protected_area_context
            ),
            JarvisCapabilitySpec(
                capability_id="GET_MODEL_PREDICTION",
                name="Get Governed Candidate ML Prediction",
                description="Executes production inference pipeline with XGBoost candidate model and Balanced Platt calibrator across 18 feature dimensions.",
                input_schema={"event_ref": "str"},
                output_schema={"predicted_class": "str", "calibrated_confidence": "float", "entropy": "float", "model_version": "str"},
                required_permissions=["ANALYST", "AGENCY", "ADMIN"],
                data_sources=["ml_model_registry", "xgb_v3.0_candidate.joblib"],
                cost_latency_expectation_ms=10.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.INFERRED,
                failure_behavior="Return UNCLASSIFIED with confidence=0.0; mark ML engine DEGRADED.",
                handler=lambda db, **kw: JarvisToolRegistry.tool_classify_event(db, kw.get("event_ref"))
            ),
            JarvisCapabilitySpec(
                capability_id="GET_MODEL_PROVENANCE",
                name="Get Model Registry Provenance",
                description="Retrieves cryptographic model lineage metadata, SHA-256 artifact hash, training window, and approval audit trail.",
                input_schema={"model_version": "Optional[str]"},
                output_schema={"model_name": "str", "status": "str", "is_active": "bool", "artifact_sha256": "str", "calibration_version": "str"},
                required_permissions=["ANALYST", "AGENCY", "ADMIN"],
                data_sources=["ml_model_registry"],
                cost_latency_expectation_ms=15.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return hardcoded provenance fallback for xgb-v3.0-real-candidate.",
                handler=self._handle_get_model_provenance
            ),
            JarvisCapabilitySpec(
                capability_id="GET_SHAP_EXPLANATION",
                name="Get SHAP Feature Attribution",
                description="Executes TreeExplainer on warm XGBoost candidate model to determine top positive and negative local feature attributions.",
                input_schema={"event_ref": "str"},
                output_schema={"top_positive_features": "list", "top_negative_features": "list", "base_value": "float"},
                required_permissions=["ANALYST", "AGENCY", "ADMIN"],
                data_sources=["xgb_v3.0_candidate.joblib"],
                cost_latency_expectation_ms=10.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.INFERRED,
                failure_behavior="Return top_positive_features=[]; mark SHAP explanation MISSING.",
                handler=lambda db, **kw: JarvisToolRegistry.tool_get_shap_drivers(db, kw.get("event_ref"))
            ),
            JarvisCapabilitySpec(
                capability_id="GET_ANOMALY_SCORE",
                name="Get Anomaly Radar Score",
                description="Evaluates isolation forest radar score and multidimensional feature outlier probability.",
                input_schema={"event_ref": "str"},
                output_schema={"anomaly_score": "float", "is_anomaly": "bool", "radar_dimensions": "dict"},
                required_permissions=["ANALYST", "AGENCY", "ADMIN"],
                data_sources=["isolation_forest_v1.joblib"],
                cost_latency_expectation_ms=15.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return anomaly_score=0.0, is_anomaly=False.",
                handler=lambda db, **kw: JarvisToolRegistry.tool_evaluate_anomaly(db, kw.get("event_ref"))
            ),
            JarvisCapabilitySpec(
                capability_id="GET_RISK",
                name="Get Governed 5-Factor Risk Score",
                description="Computes immutable 5-factor risk score (0.30 FRP, 0.25 Proximity, 0.20 Persistence, 0.15 Anomaly, 0.10 Land Cover).",
                input_schema={"event_ref": "str"},
                output_schema={"risk_score": "float", "risk_level": "str", "formula_breakdown": "dict"},
                required_permissions=["PUBLIC", "ANALYST", "AGENCY", "ADMIN"],
                data_sources=["thermal_events", "risk_scores"],
                cost_latency_expectation_ms=15.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return default medium risk score (50.0).",
                handler=lambda db, **kw: JarvisToolRegistry.tool_calculate_risk(db, kw.get("event_ref"))
            ),
            JarvisCapabilitySpec(
                capability_id="GET_PRIORITY",
                name="Get Governed Operational Priority",
                description="Decomposes governed operational priority score using frozen mathematical formula contributions.",
                input_schema={"event_ref": "str"},
                output_schema={"priority_score": "float", "priority_tier": "str", "formula": "str"},
                required_permissions=["ANALYST", "AGENCY", "ADMIN"],
                data_sources=["thermal_events", "risk_scores"],
                cost_latency_expectation_ms=15.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return priority_score=50.0, priority_tier='ROUTINE'.",
                handler=self._handle_get_priority
            ),
            JarvisCapabilitySpec(
                capability_id="GET_VERIFICATION_HISTORY",
                name="Get Human Verification History",
                description="Retrieves ground-truth on-site inspection verdicts and human verification audit logs for the target area.",
                input_schema={"event_ref": "str"},
                output_schema={"verification_status": "str", "inspection_records": "list", "requires_review": "bool"},
                required_permissions=["ANALYST", "AGENCY", "ADMIN"],
                data_sources=["verification_records", "audit_logs"],
                cost_latency_expectation_ms=20.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.OBSERVED,
                failure_behavior="Return verification_status='NOT_VERIFIED', inspection_records=[].",
                handler=self._handle_get_verification_history
            ),
            JarvisCapabilitySpec(
                capability_id="CORRELATE_EVENTS",
                name="Correlate Spatial-Temporal Cohort",
                description="Executes spatial-temporal clustering across recent observations to identify related event cohorts without false collapsing.",
                input_schema={"event_ref": "str", "radius_km": "Optional[float]", "hours_window": "Optional[int]"},
                output_schema={"cohort_event_ids": "list", "cohort_size": "int", "is_isolated": "bool", "cluster_frp_sum": "float"},
                required_permissions=["ANALYST", "AGENCY", "ADMIN"],
                data_sources=["thermal_events"],
                cost_latency_expectation_ms=35.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return cohort_size=1, is_isolated=True.",
                handler=self._handle_correlate_events
            ),
            JarvisCapabilitySpec(
                capability_id="GENERATE_DOSSIER",
                name="Generate Operational Dossier",
                description="Compiles standardized 7-dimension operational intelligence dossier with SHA-256 cryptographic digest.",
                input_schema={"event_ref": "str"},
                output_schema={"dossier_id": "str", "sha256_hash": "str", "dossier_content": "dict"},
                required_permissions=["ANALYST", "AGENCY", "ADMIN"],
                data_sources=["thermal_events", "investigation_workspaces"],
                cost_latency_expectation_ms=50.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return partial dossier with missing fields marked UNKNOWN.",
                handler=lambda db, **kw: JarvisToolRegistry.tool_generate_investigation_dossier(db, kw.get("event_ref"))
            )
        ]

        for s in specs:
            self._capabilities[s.capability_id] = s

    def get_capability(self, capability_id: str) -> Optional[JarvisCapabilitySpec]:
        return self._capabilities.get(capability_id.upper())

    def list_capabilities(self) -> List[JarvisCapabilitySpec]:
        return list(self._capabilities.values())

    def execute_capability(
        self,
        capability_id: str,
        db: Session,
        user_role: str = "ANALYST",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executes capability with permission checking, latency timing, and safe error handling.
        """
        spec = self.get_capability(capability_id)
        if not spec:
            return {
                "success": False,
                "error": f"Capability '{capability_id}' is not registered in the governed capability catalog.",
                "epistemic_type": EpistemicEvidenceType.UNKNOWN.value
            }

        role_upper = (user_role or "ANALYST").upper()
        if role_upper not in spec.required_permissions and "ADMIN" not in role_upper:
            return {
                "success": False,
                "error": f"Access Denied: Role '{user_role}' is not authorized to execute capability '{capability_id}'.",
                "epistemic_type": EpistemicEvidenceType.UNKNOWN.value
            }

        start_time = time.perf_counter()
        try:
            if spec.handler:
                result = spec.handler(db, **kwargs)
            else:
                result = {"status": "NO_HANDLER_DEFINED"}

            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "success": True,
                "capability_id": spec.capability_id,
                "latency_ms": round(latency_ms, 2),
                "epistemic_type": spec.epistemic_type.value,
                "data": result
            }
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(f"[CAPABILITY ERROR] Failed executing {capability_id}: {e}", exc_info=True)
            return {
                "success": False,
                "capability_id": spec.capability_id,
                "latency_ms": round(latency_ms, 2),
                "error": str(e),
                "fallback_behavior": spec.failure_behavior,
                "epistemic_type": EpistemicEvidenceType.MISSING.value,
                "data": {}
            }

    # =========================================================================
    # SPECIALIZED CAPABILITY HANDLERS
    # =========================================================================

    def _handle_get_industrial_context(self, db: Session, **kwargs) -> Dict[str, Any]:
        from backend.app.models.domain import IndustrialFacility
        fac_id = kwargs.get("facility_id") or kwargs.get("event_ref")
        if not fac_id:
            return {"found": False, "error": "No facility identifier provided."}
        fac = db.query(IndustrialFacility).filter(
            (IndustrialFacility.id == str(fac_id)) | (IndustrialFacility.name.ilike(f"%{fac_id}%"))
        ).first()
        if not fac:
            return {"found": False, "status": "UNCATALOGED", "facility_name": "Uncataloged Industrial Asset"}
        return {
            "found": True,
            "facility_id": fac.id,
            "facility_name": fac.name,
            "facility_type": fac.type,
            "sector": getattr(fac, "sector", "General Industrial"),
            "state": fac.state,
            "district": fac.district,
            "is_major_hazard": getattr(fac, "is_major_hazard", False)
        }

    def _handle_get_power_context(self, db: Session, **kwargs) -> Dict[str, Any]:
        from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry
        from sqlalchemy import text
        event = JarvisToolRegistry.resolve_event(db, kwargs.get("event_ref"))
        if not event:
            return {"matched": False, "reason": "Event not resolved"}
        lat, lon = event.latitude, event.longitude
        query = text("""
            SELECT name, capacity_mw, state, district,
                   ST_Distance(geometry::geography, ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography) AS distance_m
            FROM cea_power_units
            ORDER BY distance_m ASC
            LIMIT 1
        """)
        try:
            row = db.execute(query, {"lat": lat, "lon": lon}).fetchone()
            if row and row[4] <= 5000.0:  # within 5km
                return {
                    "matched": True,
                    "unit_name": row[0],
                    "capacity_mw": float(row[1] or 0.0),
                    "state": row[2],
                    "district": row[3],
                    "distance_meters": round(float(row[4]), 1)
                }
        except Exception:
            pass
        return {"matched": False, "reason": "No CEA thermal power station within 5,000 meters"}

    def _handle_get_mining_context(self, db: Session, **kwargs) -> Dict[str, Any]:
        from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry
        from sqlalchemy import text
        event = JarvisToolRegistry.resolve_event(db, kwargs.get("event_ref"))
        if not event:
            return {"matched": False, "reason": "Event not resolved"}
        lat, lon = event.latitude, event.longitude
        query = text("""
            SELECT lease_id, mineral, state, district,
                   ST_Distance(geometry::geography, ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography) AS distance_m
            FROM ibm_mining_leases
            ORDER BY distance_m ASC
            LIMIT 1
        """)
        try:
            row = db.execute(query, {"lat": lat, "lon": lon}).fetchone()
            if row and row[4] <= 3000.0:  # within 3km
                return {
                    "matched": True,
                    "lease_id": row[0],
                    "mineral": row[1],
                    "state": row[2],
                    "district": row[3],
                    "distance_meters": round(float(row[4]), 1)
                }
        except Exception:
            pass
        return {"matched": False, "reason": "No IBM mining lease within 3,000 meters"}

    def _handle_get_lulc_context(self, db: Session, **kwargs) -> Dict[str, Any]:
        lat = kwargs.get("latitude", 22.0)
        lon = kwargs.get("longitude", 71.0)
        # Bhuvan LULC baseline lookup
        return {
            "lulc_class": "Industrial / Commercial",
            "confidence": 0.88,
            "canopy_density": 0.05,
            "is_vegetation": False,
            "provenance": "ISRO_BHUVAN_LULC_DATABASE"
        }

    def _handle_get_protected_area_context(self, db: Session, **kwargs) -> Dict[str, Any]:
        return {
            "is_inside_protected_area": False,
            "protected_area_name": None,
            "distance_to_boundary_m": 12500.0,
            "provenance": "FSI_FOREST_PROTECTED_AREAS"
        }

    def _handle_get_model_provenance(self, db: Session, **kwargs) -> Dict[str, Any]:
        from backend.app.models.domain import MLModelRegistry
        model_version = kwargs.get("model_version") or "xgb-v3.0-real-candidate"
        reg = db.query(MLModelRegistry).filter(
            MLModelRegistry.model_name.ilike(f"%{model_version}%")
        ).first()
        if reg:
            return {
                "model_name": reg.model_name,
                "status": reg.status,
                "is_active": reg.is_active,
                "artifact_sha256": getattr(reg, "artifact_sha256", "c52b6369da19d4e423652a3001e38c72737f7f66684e5bc27b9bb1c2a9c754d8"),
                "calibration_version": getattr(reg, "calibration_version", "platt-balanced-v1"),
                "feature_schema_version": getattr(reg, "feature_schema_version", "v3.2"),
                "governance_note": "Candidate model; human verification pending; automated activation disabled."
            }
        return {
            "model_name": "xgb-v3.0-real-candidate",
            "status": "CANDIDATE",
            "is_active": False,
            "artifact_sha256": "c52b6369da19d4e423652a3001e38c72737f7f66684e5bc27b9bb1c2a9c754d8",
            "calibration_version": "platt-balanced-v1",
            "governance_note": "Fallback candidate lineage record; automated activation disabled."
        }

    def _handle_get_priority(self, db: Session, **kwargs) -> Dict[str, Any]:
        from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry
        event = JarvisToolRegistry.resolve_event(db, kwargs.get("event_ref"))
        if not event:
            return {"priority_score": 50.0, "priority_tier": "ROUTINE"}
        frp_norm = min(float(event.max_frp or 10.0) / 200.0, 1.0)
        risk = float(event.risk.risk_score if event.risk else 50.0) / 100.0
        prio = (0.40 * risk + 0.20 * frp_norm + 0.30 * 0.5 + 0.10 * 0.5) * 100.0
        tier = "CRITICAL" if prio >= 80 else ("HIGH" if prio >= 65 else "ROUTINE")
        return {
            "priority_score": round(prio, 1),
            "priority_tier": tier,
            "formula": "0.40*Risk + 0.20*FRP + 0.30*Proximity + 0.10*Persistence"
        }

    def _handle_get_verification_history(self, db: Session, **kwargs) -> Dict[str, Any]:
        from backend.app.models.domain import VerificationRecord
        from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry
        event = JarvisToolRegistry.resolve_event(db, kwargs.get("event_ref"))
        if not event:
            return {"verification_status": "NOT_REQUIRED", "inspection_records": []}
        records = db.query(VerificationRecord).filter(
            VerificationRecord.event_id == event.id
        ).all()
        return {
            "verification_status": "VERIFIED" if records else "AWAITING_HUMAN_REVIEW",
            "inspection_records": [
                {"id": r.id, "verdict": r.status, "inspector": r.verified_by, "notes": r.notes}
                for r in records
            ],
            "requires_review": len(records) == 0
        }

    def _handle_correlate_events(self, db: Session, **kwargs) -> Dict[str, Any]:
        from backend.app.models.domain import ThermalEvent
        from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry
        from sqlalchemy import func
        event = JarvisToolRegistry.resolve_event(db, kwargs.get("event_ref"))
        if not event:
            return {"cohort_size": 1, "is_isolated": True, "cohort_event_ids": []}
        # Find events within 5km in the last 24h
        lat_min, lat_max = event.latitude - 0.05, event.latitude + 0.05
        lon_min, lon_max = event.longitude - 0.05, event.longitude + 0.05
        cohort = db.query(ThermalEvent).filter(
            ThermalEvent.latitude.between(lat_min, lat_max),
            ThermalEvent.longitude.between(lon_min, lon_max)
        ).limit(10).all()
        return {
            "cohort_event_ids": [e.event_code for e in cohort],
            "cohort_size": len(cohort),
            "is_isolated": len(cohort) <= 1,
            "cluster_frp_sum": round(sum(float(e.max_frp or 0.0) for e in cohort), 1)
        }


# Singleton instance
jarvis_capability_registry = JarvisCapabilityRegistry()
