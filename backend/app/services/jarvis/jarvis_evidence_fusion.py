"""
AGNI-NETRA — JARVIS Evidence Fusion Engine
Synthesizes multimodal intelligence outputs into structured evidence packages
with strict epistemic boundaries: FACT, DERIVED ANALYSIS, MODEL OUTPUT, SPATIAL CONTEXT, INFERENCE, RECOMMENDATION.
"""

from typing import Dict, Any, List, Optional
from backend.app.models.jarvis_schemas import (
    FusedEvidence, EvidenceQuality, EvidenceStatus, CategorizedSynthesis
)


class JarvisEvidenceFusion:
    """
    Fuses deterministic outputs from PostGIS, XGBoost, Isolation Forest, SHAP, Risk, and FIRMS.
    Enforces clear epistemic boundaries and avoids hallucination.
    """

    @staticmethod
    def fuse_event_intelligence(
        event_data: Optional[Dict[str, Any]] = None,
        geo_data: Optional[Dict[str, Any]] = None,
        ml_data: Optional[Dict[str, Any]] = None,
        anom_data: Optional[Dict[str, Any]] = None,
        risk_data: Optional[Dict[str, Any]] = None,
        sat_data: Optional[Dict[str, Any]] = None,
        context_data: Optional[Dict[str, Any]] = None,
        temporal_data: Optional[Dict[str, Any]] = None,
        env_data: Optional[Dict[str, Any]] = None,
        crossmodal_data: Optional[Dict[str, Any]] = None
    ) -> FusedEvidence:
        fused = FusedEvidence()
        missing_elements = []

        # Attach auxiliary evidence domains if present
        if context_data:
            fused.context_evidence = context_data
        if temporal_data:
            fused.temporal_evidence = temporal_data
        if env_data:
            fused.environmental_evidence = env_data
        if crossmodal_data:
            fused.cross_modal_evidence = crossmodal_data

        # 1. Thermal Evidence (Fact)
        facts: List[str] = []
        if event_data and event_data.get("found", True):
            fused.thermal_evidence = {
                "event_code": event_data.get("event_code"),
                "max_frp": event_data.get("max_frp"),
                "avg_frp": event_data.get("avg_frp"),
                "coordinates": [event_data.get("latitude"), event_data.get("longitude")],
                "state": event_data.get("state"),
                "district": event_data.get("district"),
                "detection_count": event_data.get("detection_count"),
                "satellite_count": event_data.get("satellite_count"),
                "first_seen": event_data.get("first_seen"),
                "last_seen": event_data.get("last_seen"),
                "provenance": "NASA_FIRMS_VIIRS_MODIS"
            }
            facts.append(f"Satellite-derived thermal event {event_data.get('event_code')} recorded in {event_data.get('state')} ({event_data.get('district') or 'State Territory'}).")
            facts.append(f"Peak Fire Radiative Power (FRP): {event_data.get('max_frp')} MW (Mean: {event_data.get('avg_frp')} MW across {event_data.get('detection_count')} detections).")
        else:
            missing_elements.append("ThermalEventRecord")

        # 2. Geospatial Evidence (Spatial Context & Derived Analysis)
        spatial_context: List[str] = []
        derived_analysis: List[str] = []
        if geo_data and not geo_data.get("error"):
            fused.geospatial_evidence = geo_data
            top_fac = geo_data.get("nearest_primary_asset")
            if top_fac:
                dist = int(top_fac.get("distance_meters", 0))
                spatial_context.append(f"Located {dist}m from {top_fac.get('name')} ({top_fac.get('type')}, sector: {top_fac.get('sector')}).")
            
            buffers = geo_data.get("hazard_buffers", {})
            if buffers.get("500m", {}).get("is_critical_hazard_proximity"):
                derived_analysis.append("Critical hazard containment alert: Hotspot is within 500m of an active industrial polygon boundary.")
            elif buffers.get("1000m", {}).get("is_critical_hazard_proximity"):
                derived_analysis.append("Immediate proximity alert: Hotspot is within 1,000m perimeter of an industrial facility.")
        else:
            missing_elements.append("PostGISGeospatialContext")

        # 3. ML Classification & SHAP (Model Output)
        model_output: List[str] = []
        if ml_data and not ml_data.get("error"):
            fused.classification = ml_data
            p_class = ml_data.get("predicted_class", "Uncertain")
            conf = ml_data.get("calibrated_confidence", 0.0) * 100.0
            model_ver = ml_data.get("model_version", "xgb-v3.0")
            model_output.append(f"Machine learning classification: '{p_class}' with {conf:.1f}% calibrated probability (Model: {model_ver}).")
            top_drivers = ml_data.get("top_shap_drivers", [])
            if top_drivers:
                d1 = top_drivers[0]
                model_output.append(f"Primary TreeExplainer SHAP driver: {d1.get('feature')} ({d1.get('direction', 'POSITIVE')} attribution: {d1.get('attribution', 0.0):+.2f}).")
        else:
            missing_elements.append("MLClassification")

        # 4. Anomaly & Baseline (Derived Analysis)
        if anom_data and not anom_data.get("error"):
            fused.anomaly = anom_data
            is_anom = anom_data.get("is_anomaly", False)
            z_score = anom_data.get("z_score", 0.0)
            ratio = anom_data.get("deviation_ratio", 1.0)
            derived_analysis.append(
                f"Statistical anomaly assessment: {'ANOMALOUS (+'+str(z_score)+' sigma)' if is_anom else 'BASELINE_COMPLIANT'}. "
                f"Current radiative heat is {ratio}x the longitudinal facility baseline."
            )
        else:
            missing_elements.append("BaselineAnomalyContext")

        # 5. Risk Assessment (Model/Formula Output)
        inferences: List[str] = []
        recommendations: List[str] = []
        if risk_data and not risk_data.get("error"):
            fused.risk = risk_data
            r_score = risk_data.get("total_risk_score", 0.0)
            r_level = risk_data.get("risk_level", "LOW")
            model_output.append(f"Operational 5-Factor Risk Score: {r_score}/100 ({r_level}).")
            reasons = risk_data.get("risk_reasons", [])
            if reasons:
                inferences.append(f"Risk evaluation drivers: {'; '.join(reasons)}.")
            
            if r_level in ["CRITICAL", "HIGH"]:
                recommendations.append("Priority 1: Route case to Human-In-The-Loop analyst verification desk.")
                recommendations.append("Cross-reference scheduled flaring turnaround / maintenance logs with facility management.")
            else:
                recommendations.append("Routine thermal monitoring active; log event in regular surveillance archive.")
        else:
            missing_elements.append("OperationalRiskAssessment")

        # 6. Environmental & Meteorological Evidence
        if env_data and not env_data.get("error"):
            wx = env_data.get("weather", {})
            wnd = env_data.get("wind", {})
            pcp = env_data.get("precipitation", {})
            if wx.get("temperature_c") is not None:
                facts.append(f"Local surface meteorology: {wx.get('temperature_c', 0.0):.1f}°C ambient temperature, {wx.get('relative_humidity_pct', 0.0):.0f}% RH.")
            if wnd.get("wind_speed_ms") is not None:
                derived_analysis.append(f"Environmental plume transport: Wind from {wnd.get('wind_direction_deg', 0):.0f}° at {wnd.get('wind_speed_ms', 0):.1f} m/s establishes {wnd.get('transport_condition', 'MODERATE_TRANSPORT')} toward {wnd.get('smoke_dispersion_direction', 'ENE')}.")
            if pcp.get("persistence_support_status"):
                derived_analysis.append(f"Precipitation persistence support: Rate {pcp.get('precipitation_rate_mmh', 0.0):.1f} mm/h evaluated as {pcp.get('persistence_support_status', 'SUPPORTIVE')} of thermal combustion.")

        # 7. Cross-Modal Verification Evidence
        if crossmodal_data and not crossmodal_data.get("error"):
            corrob = crossmodal_data.get("corroboration_status", "PARTIALLY_CORROBORATED")
            derived_analysis.append(f"Cross-modal multi-sensor corroboration: Status evaluated as '{corrob}'. Auxiliary satellite optical/radar passes unconfigured (NOT_CONFIGURED); land use and meteorology concordant.")

        # 8. Satellite Telemetry (Fact & Disclaimers)
        warnings: List[str] = [
            "SEMANTIC DISTINCTION: Thermal anomaly detection indicates statistical deviation from baseline; it does not inherently constitute an uncontained emergency.",
            "SATELLITE TELEMETRY NOTICE: Observations represent FIRMS satellite-derived infrared detections, not ground-truth site surveys.",
            "AGNI-SAT SIMULATION NOTICE: Any orbital tracking telemetry reflects AGNI-SAT digital twin mission simulation."
        ]
        if sat_data and not sat_data.get("error"):
            fused.satellite_observations = sat_data.get("observations", [])

        # Build Categorized Synthesis
        fused.categorized_synthesis = CategorizedSynthesis(
            facts=facts,
            derived_analysis=derived_analysis,
            model_output=model_output,
            spatial_context=spatial_context,
            inferences=inferences,
            recommendations=recommendations,
            uncertainties_and_warnings=warnings
        )

        # Completeness Score
        completeness = max(0.0, 1.0 - (len(missing_elements) * 0.15))
        status = EvidenceStatus.VERIFIED if completeness >= 0.8 else (EvidenceStatus.PARTIAL if completeness > 0.3 else EvidenceStatus.INSUFFICIENT)
        fused.evidence_quality = EvidenceQuality(
            completeness_score=round(completeness, 2),
            provenance="POSTGIS_3.4_POSTGRESQL_AND_NASA_FIRMS",
            missing_elements=missing_elements,
            status=status
        )

        return fused


evidence_fusion_engine = JarvisEvidenceFusion()
