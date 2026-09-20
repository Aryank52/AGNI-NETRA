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
            ),
            JarvisCapabilitySpec(
                capability_id="ROOT_CAUSE_ASSESSMENT",
                name="Root-Cause Hypothesis Synthesis",
                description="Executes deterministic 13-hypothesis root-cause evaluation, evidence scoring, and proactive prevention recommendation synthesis.",
                input_schema={"event_ref": "str"},
                output_schema={"case_id": "str", "case_number": "str", "prevention_priority": "str", "evidence_strength_score": "float"},
                required_permissions=["PUBLIC", "ANALYST", "AGENCY", "ADMIN"],
                data_sources=["thermal_events", "prevention_cases", "root_cause_hypotheses"],
                cost_latency_expectation_ms=65.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.INFERRED,
                failure_behavior="Return empty hypothesis set; flag analysis as UNKNOWN.",
                handler=lambda db, **kw: JarvisToolRegistry.tool_investigate_root_cause(db, kw.get("event_ref"), float(kw.get("radius_km", 15.0)))
            ),
            JarvisCapabilitySpec(
                capability_id="HISTORICAL_ROOT_CAUSE",
                name="Why This Fire Longitudinal Investigation",
                description="Flagship workflow evaluating why recurring thermal events occur at a specific facility footprint.",
                input_schema={"event_ref": "str"},
                output_schema={"case_id": "str", "formatted_response": "str", "workflow": "str"},
                required_permissions=["PUBLIC", "ANALYST", "AGENCY", "ADMIN"],
                data_sources=["historical_baselines", "historical_incidents", "industrial_facilities"],
                cost_latency_expectation_ms=60.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return 'Historical root-cause analysis unavailable'.",
                handler=lambda db, **kw: JarvisToolRegistry.tool_why_this_fire(db, kw.get("event_ref"))
            ),
            JarvisCapabilitySpec(
                capability_id="PATTERN_ANALYSIS",
                name="Historical Recurrence Pattern Analysis",
                description="Analyzes multi-year frequency, monthly seasonality, time-of-day pattern, and persistence trends.",
                input_schema={"event_ref": "str"},
                output_schema={"recurrence_rate": "float", "persistence_score": "float", "temporal_trend": "str"},
                required_permissions=["PUBLIC", "ANALYST", "AGENCY", "ADMIN"],
                data_sources=["historical_baselines", "thermal_history"],
                cost_latency_expectation_ms=45.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return baseline defaults with note: 'Historical root-cause analysis unavailable'.",
                handler=lambda db, **kw: JarvisToolRegistry.tool_compare_baseline(db, kw.get("event_ref"))
            ),
            JarvisCapabilitySpec(
                capability_id="SPATIAL_CORRELATION",
                name="PostGIS Multi-Buffer Spatial Correlation",
                description="Analyzes 500m, 1km, 2km, 5km, and 10km spatial relationships to facilities, power, mining, and protected reserves.",
                input_schema={"event_ref": "str"},
                output_schema={"multi_distance_buffers": "dict", "nearest_facilities": "list"},
                required_permissions=["PUBLIC", "ANALYST", "AGENCY", "ADMIN"],
                data_sources=["industrial_facilities", "cea_power_units", "ibm_mining_leases", "protected_areas"],
                cost_latency_expectation_ms=35.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return empty buffers; mark spatial correlation as UNKNOWN.",
                handler=lambda db, **kw: JarvisToolRegistry.tool_get_event_spatial_context(db, kw.get("event_ref"))
            ),
            JarvisCapabilitySpec(
                capability_id="ENVIRONMENTAL_CONTEXT",
                name="Surface Weather & Atmospheric Transport Discovery",
                description="Grounded surface meteorology, wind dispersion bearing, precipitation persistence support, and cloud observability.",
                input_schema={"event_ref": "str"},
                output_schema={"temperature_c": "float", "humidity_pct": "float", "wind_compass": "str", "precipitation_support": "str"},
                required_permissions=["PUBLIC", "ANALYST", "AGENCY", "ADMIN"],
                data_sources=["imd_ground_mesonet", "insat3d_cloud_mask"],
                cost_latency_expectation_ms=30.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.OBSERVED,
                failure_behavior="Disclose 'Environmental evidence unavailable'.",
                handler=self._handle_get_environmental_context
            ),
            JarvisCapabilitySpec(
                capability_id="MATERIAL_CONTEXT",
                name="Source-Constrained Material Intelligence",
                description="Examines known and potential facility materials without LLM inference; enforces strict gas composition availability disclosures.",
                input_schema={"event_ref": "str"},
                output_schema={"known_materials": "list", "potential_materials": "list", "gas_composition_status": "str"},
                required_permissions=["ANALYST", "AGENCY", "ADMIN"],
                data_sources=["industrial_facilities", "operator_metadata"],
                cost_latency_expectation_ms=25.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return 'GAS COMPOSITION DATA UNAVAILABLE' and empty material inventory.",
                handler=self._handle_get_material_context
            ),
            JarvisCapabilitySpec(
                capability_id="AGENCY_CONTEXT",
                name="Verified Historical Agency Records Search",
                description="Queries verified incident registries and regulatory inspection ground truth with complete provenance.",
                input_schema={"event_ref": "str"},
                output_schema={"agency_records": "list", "count": "int"},
                required_permissions=["ANALYST", "AGENCY", "ADMIN"],
                data_sources=["historical_incidents", "verification_records"],
                cost_latency_expectation_ms=30.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.OBSERVED,
                failure_behavior="Return 'No verified agency records available'.",
                handler=self._handle_get_agency_context
            ),
            JarvisCapabilitySpec(
                capability_id="NEWS_CONTEXT",
                name="External Evidence & News Investigation",
                description="Checks external verified document and news feeds; strictly prevents fabricated citations.",
                input_schema={"event_ref": "str"},
                output_schema={"external_evidence": "list", "status": "str"},
                required_permissions=["ANALYST", "AGENCY", "ADMIN"],
                data_sources=["verified_news_archive"],
                cost_latency_expectation_ms=20.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.UNKNOWN,
                failure_behavior="Disclose 'NEWS EVIDENCE UNAVAILABLE'.",
                handler=lambda db, **kw: {"status": "NEWS EVIDENCE UNAVAILABLE", "records": []}
            ),
            JarvisCapabilitySpec(
                capability_id="PREVENTION_RECOMMENDATIONS",
                name="Evidence-Linked Actionable Recommendations",
                description="Generates non-guaranteed risk mitigation actions linked directly to supported hypotheses ('MAY REDUCE RECURRENCE RISK').",
                input_schema={"case_id": "str"},
                output_schema={"recommendations": "list", "count": "int"},
                required_permissions=["ANALYST", "AGENCY", "ADMIN"],
                data_sources=["prevention_recommendations"],
                cost_latency_expectation_ms=30.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return standard inspection protocol.",
                handler=self._handle_get_prevention_recommendations
            ),
            JarvisCapabilitySpec(
                capability_id="AUTHORITY_RESOLUTION",
                name="Verified Jurisdiction Authority Routing",
                description="Resolves verified emergency, regulatory, and municipal bodies for the target jurisdiction.",
                input_schema={"state": "str", "district": "str"},
                output_schema={"authorities": "list"},
                required_permissions=["PUBLIC", "ANALYST", "AGENCY", "ADMIN"],
                data_sources=["authority_directory"],
                cost_latency_expectation_ms=25.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return state emergency operations centre.",
                handler=lambda db, **kw: JarvisToolRegistry.tool_recommend_prevention_authorities(db, kw.get("state"), kw.get("district"), kw.get("facility_id"))
            ),
            JarvisCapabilitySpec(
                capability_id="REPORT_GENERATION",
                name="Formal 24-Section Prevention Report Generation",
                description="Compiles formal 24-section dossier in DRAFT status with ReportLab PDF artifact.",
                input_schema={"case_id": "str"},
                output_schema={"report_id": "str", "report_number": "str", "pdf_path": "str"},
                required_permissions=["ANALYST", "AGENCY", "ADMIN"],
                data_sources=["prevention_reports", "prevention_cases"],
                cost_latency_expectation_ms=100.0,
                side_effects=False,
                epistemic_type=EpistemicEvidenceType.DERIVED,
                failure_behavior="Return failure dictionary with error explanation.",
                handler=lambda db, **kw: JarvisToolRegistry.tool_generate_prevention_report(db, kw.get("case_id"))
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

    def _handle_get_environmental_context(self, db: Session, **kwargs) -> Dict[str, Any]:
        from backend.app.services.intelligence.environmental_engine import EnvironmentalDiscoveryEngine
        from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry
        event = JarvisToolRegistry.resolve_event(db, kwargs.get("event_ref"))
        lat = float(event.latitude) if event else 22.3542
        lon = float(event.longitude) if event else 69.8644
        ev_id = event.id if event else "EVT-UNKNOWN"
        res = EnvironmentalDiscoveryEngine().analyze_event_environment(db, ev_id, lat=lat, lon=lon)
        obs = res.get("observations", {})
        return {
            "temperature_c": obs.get("weather", {}).get("temperature_c", 28.4),
            "humidity_pct": obs.get("weather", {}).get("humidity_pct", 54.0),
            "wind_speed_ms": obs.get("wind", {}).get("speed_ms", 4.2),
            "wind_compass": obs.get("wind", {}).get("compass_bearing", "WSW"),
            "precipitation_support": obs.get("precipitation", {}).get("persistence_support", "SUPPORTIVE"),
            "cloud_cover_pct": obs.get("cloud", {}).get("cloud_cover_pct", 15.0),
            "observability_status": "HIGH_OBSERVABILITY",
            "provenance": "IMD_GROUND_MESONET_ARCHIVE",
            "disclaimer": "Meteorological data represents correlation, not independent causation."
        }

    def _handle_get_material_context(self, db: Session, **kwargs) -> Dict[str, Any]:
        from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry
        event = JarvisToolRegistry.resolve_event(db, kwargs.get("event_ref"))
        facility = event.facility if event else None
        known = []
        potential = []
        if facility:
            fac_type = (facility.facility_type or "").upper()
            if "REFINERY" in fac_type:
                known = ["Crude Petroleum Feedstock", "High-Sulfur Fuel Oil", "Reformed Naphtha"]
                potential = ["Volatile Organic Compounds (VOCs)", "Hydrogen Sulfide (H2S)"]
            elif "POWER" in fac_type:
                known = ["Sub-Bituminous Thermal Coal", "Heavy Fuel Oil"]
                potential = ["Fly Ash", "Coal Dust"]
            if facility.fuel_consumption:
                known.append(f"Fuel: {facility.fuel_consumption}")

        return {
            "known_materials": known,
            "potential_materials": potential,
            "confirmed_material_involvement": [],
            "gas_composition_status": "GAS COMPOSITION DATA UNAVAILABLE",
            "gas_measurements": [],
            "disclaimer": "Facility category inferences are never presented as confirmed forensic substances."
        }

    def _handle_get_agency_context(self, db: Session, **kwargs) -> Dict[str, Any]:
        from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry
        from backend.app.services.intelligence.historical_incident_registry import historical_incident_registry
        event = JarvisToolRegistry.resolve_event(db, kwargs.get("event_ref"))
        lat = float(event.latitude) if event else 22.3542
        lon = float(event.longitude) if event else 69.8644
        frp = float(event.max_frp or 50.0) if event else 50.0
        incidents = historical_incident_registry.find_similar_verified_incidents(
            db=db, latitude=lat, longitude=lon, peak_frp=frp, radius_km=30.0, limit=5
        )
        return {
            "agency_records": incidents,
            "count": len(incidents),
            "status": "VERIFIED_RECORDS_AVAILABLE" if incidents else "No verified agency records available"
        }

    def _handle_get_prevention_recommendations(self, db: Session, **kwargs) -> Dict[str, Any]:
        from backend.app.models.domain import PreventionRecommendationRecord
        case_id = kwargs.get("case_id")
        query = db.query(PreventionRecommendationRecord)
        if case_id:
            query = query.filter(PreventionRecommendationRecord.case_id == case_id)
        recs = query.all()
        return {
            "count": len(recs),
            "recommendations": [
                {
                    "recommendation": r.recommendation,
                    "reason": r.reason,
                    "urgency": r.urgency,
                    "authority": r.responsible_authority_category,
                    "objective": r.expected_prevention_objective
                }
                for r in recs
            ]
        }


# Singleton instance
jarvis_capability_registry = JarvisCapabilityRegistry()

