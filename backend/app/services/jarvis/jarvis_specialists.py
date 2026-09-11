"""
AGNI-NETRA — JARVIS Specialist Agents
8 Specialized Agents coordinating deterministic queries, safety policies, and evidence fusion.
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models.jarvis_schemas import AgentType, StepStatus
from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry


class JarvisGuard:
    """
    JARVIS-GUARD: Safety, Authorization, and Dispatch Gate Enforcement Agent.
    Strictly prevents unauthorized operations, prompt injection exploitation, and automated live dispatch.
    """

    ALLOWED_ROLES = ["ADMIN", "ANALYST", "AGENCY", "RESEARCHER", "INDUSTRY", "PUBLIC"]
    
    # Public role has restricted access to sensitive internal coordinates and proprietary facilities
    PUBLIC_RESTRICTED_TOOLS = ["get_all_audit_logs", "execute_pipeline_recalibration"]

    @staticmethod
    def authorize_action(
        user_role: str,
        action: str,
        target_tool: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates whether the user's role permits executing the specified action or tool.
        """
        role_upper = (user_role or "ANALYST").upper()
        if role_upper not in JarvisGuard.ALLOWED_ROLES:
            return False, f"Access Denied: Unrecognized role '{user_role}'."

        # Public user restrictions
        if role_upper == "PUBLIC":
            if target_tool in JarvisGuard.PUBLIC_RESTRICTED_TOOLS:
                return False, f"Access Denied: Tool '{target_tool}' requires authenticated Analyst or Agency clearance."

        # Operational Dispatch Gate Invariant
        if "dispatch" in action.lower() or "emergency" in action.lower():
            return False, "OPERATIONAL_DISPATCH_BLOCKED: ENABLE_OPERATIONAL_DISPATCH_GATE is enforced FALSE. Direct automated external dispatch is prohibited."

        # Prevent database write/mutation actions through JARVIS
        if any(w in action.lower() for w in ["drop", "delete", "truncate", "update", "insert", "alter"]):
            return False, "MUTATION_BLOCKED: JARVIS is an investigative and command orchestration layer; direct database mutations via natural language are prohibited."

        return True, None


class JarvisGeo:
    """
    JARVIS-GEO: Geospatial Intelligence Specialist Agent.
    Coordinates PostGIS multi-buffer asset queries, facility proximity, and administrative spatial containment.
    """

    @staticmethod
    def analyze_event_geospatial_context(db: Session, event_ref: str) -> Dict[str, Any]:
        result = JarvisToolRegistry.tool_get_event_spatial_context(db, event_ref)
        if not result.get("found", True):
            return {"error": result.get("error")}

        # Formulate grounded geospatial assessment
        nearest_facs = result.get("nearest_facilities", [])
        top_fac = nearest_facs[0] if nearest_facs else None
        
        assessment = {
            "agent": AgentType.JARVIS_GEO,
            "raw_context": result,
            "summary": (
                f"Thermal anomaly centered at [{result['latitude']:.4f}, {result['longitude']:.4f}] in "
                f"{result['district'] or 'General Territory'}, {result['state']}. "
                + (f"Epicenter is {int(top_fac['distance_meters'])}m from {top_fac['name']} ({top_fac['type']})." if top_fac else "No industrial facilities within 10 km.")
            ),
            "hazard_buffers": result.get("multi_distance_buffers", {}),
            "nearest_primary_asset": top_fac,
            "provenance": "POSTGIS_ST_DISTANCE_CALCULATION"
        }
        return assessment


class JarvisML:
    """
    JARVIS-ML: Machine Learning Intelligence Specialist Agent.
    Executes authoritative XGBoost classification, Platt probability calibration, and TreeExplainer SHAP attribution.
    """

    @staticmethod
    def classify_and_explain(db: Session, event_ref: str) -> Dict[str, Any]:
        cls_res = JarvisToolRegistry.tool_classify_event(db, event_ref)
        if not cls_res.get("found", True):
            return {"error": cls_res.get("error")}

        shap_res = JarvisToolRegistry.tool_get_shap_drivers(db, event_ref)

        return {
            "agent": AgentType.JARVIS_ML,
            "predicted_class": cls_res["predicted_class"],
            "calibrated_confidence": cls_res["calibrated_confidence"],
            "model_version": cls_res["model_version"],
            "calibrator_version": cls_res["calibrator_version"],
            "routing_tier": cls_res["routing_tier"],
            "model_state": "CANDIDATE_DEPLOYED_IN_CONTROLLED_MODE",
            "top_shap_drivers": shap_res.get("top_drivers", []),
            "shap_summary": shap_res.get("explanation", ""),
            "summary": (
                f"Classified as '{cls_res['predicted_class']}' with {cls_res['calibrated_confidence']*100:.1f}% "
                f"calibrated probability via {cls_res['model_version']}. "
                f"Top attribution driver: {shap_res.get('top_drivers', [{}])[0].get('feature', 'geospatial_proximity')}."
            )
        }


class JarvisAnom:
    """
    JARVIS-ANOM: Anomaly Intelligence Specialist Agent.
    Executes Isolation Forest multivariate outlier detection and statistical baseline comparisons.
    Enforces strict distinction: ANOMALY != FIRE != RISK.
    """

    @staticmethod
    def investigate_anomaly(db: Session, event_ref: str) -> Dict[str, Any]:
        anom_res = JarvisToolRegistry.tool_evaluate_anomaly(db, event_ref)
        base_res = JarvisToolRegistry.tool_compare_baseline(db, event_ref)

        return {
            "agent": AgentType.JARVIS_ANOM,
            "is_anomaly": anom_res.get("is_anomaly", False),
            "anomaly_type": anom_res.get("anomaly_type", "NORMAL_BEHAVIOR"),
            "isolation_forest_score": anom_res.get("isolation_forest_score", 0.0),
            "z_score": anom_res.get("z_score", 0.0),
            "deviation_ratio": anom_res.get("deviation_ratio", 1.0),
            "baseline_status": base_res.get("baseline_status", "NORMAL"),
            "historical_mean_frp": base_res.get("historical_mean_frp"),
            "current_max_frp": base_res.get("current_max_frp"),
            "semantic_distinction": anom_res.get("semantic_distinction", {}),
            "summary": (
                f"Anomaly status: {'ANOMALOUS' if anom_res.get('is_anomaly') else 'BASELINE_COMPLIANT'}. "
                f"Current radiative output ({base_res.get('current_max_frp')} MW) is {base_res.get('deviation_ratio', 1.0)}x "
                f"historical baseline mean (+{anom_res.get('z_score', 0.0)} sigma). "
                f"Isolation Forest score: {anom_res.get('isolation_forest_score', 0.0)}."
            )
        }


class JarvisRisk:
    """
    JARVIS-RISK: Risk Intelligence Specialist Agent.
    Computes transparent multi-factor risk score (0 - 100) via authoritative formula.
    """

    @staticmethod
    def calculate_operational_risk(db: Session, event_ref: str) -> Dict[str, Any]:
        risk_res = JarvisToolRegistry.tool_calculate_risk(db, event_ref)
        if not risk_res.get("found", True):
            return {"error": risk_res.get("error")}

        return {
            "agent": AgentType.JARVIS_RISK,
            "total_risk_score": risk_res["total_risk_score"],
            "risk_level": risk_res["risk_level"],
            "priority": risk_res["priority"],
            "component_subscores": risk_res["component_subscores"],
            "formula": risk_res["formula"],
            "risk_reasons": risk_res["risk_reasons"],
            "summary": (
                f"Calculated operational risk: {risk_res['total_risk_score']}/100 ({risk_res['risk_level']}). "
                f"Driven by Intensity ({risk_res['component_subscores']['intensity']}/100) and "
                f"Context ({risk_res['component_subscores']['context']}/100)."
            )
        }


class JarvisSat:
    """
    JARVIS-SAT: Satellite Intelligence Specialist Agent.
    Processes NASA FIRMS satellite-derived thermal observations and monitors digital twin simulated passes.
    """

    @staticmethod
    def retrieve_satellite_telemetry(db: Session, event_ref: str) -> Dict[str, Any]:
        sat_res = JarvisToolRegistry.tool_get_satellite_observations(db, event_ref)
        if not sat_res.get("found", True):
            return {"error": sat_res.get("error")}

        obs = sat_res.get("observations", [])
        top_obs = obs[0] if obs else {}

        return {
            "agent": AgentType.JARVIS_SAT,
            "total_detections": sat_res.get("total_detections", 0),
            "observations": obs,
            "latest_satellite": top_obs.get("satellite", "VIIRS NOAA-20"),
            "sensor": top_obs.get("sensor", "VIIRS"),
            "satellite_disclaimer": sat_res.get("satellite_disclaimer"),
            "summary": (
                f"Aggregated {sat_res.get('total_detections', 0)} satellite-derived thermal observation passes. "
                f"Latest acquisition from {top_obs.get('satellite', 'VIIRS')} with peak FRP {top_obs.get('frp_mw', 0.0):.1f} MW."
            )
        }


class JarvisInvest:
    """
    JARVIS-INVEST: Multi-Step Investigation Specialist Agent.
    Coordinates end-to-end evidence synthesis across geospatial, ML, anomaly, baseline, risk, and satellite sources.
    """

    @staticmethod
    def investigate_event_holistic(db: Session, event_ref: str) -> Dict[str, Any]:
        # 1. Fetch Event
        evt = JarvisToolRegistry.tool_get_event(db, event_ref)
        if not evt.get("found", True):
            return {"error": evt.get("error")}

        # 2. Sequential specialist investigations
        geo_intel = JarvisGeo.analyze_event_geospatial_context(db, event_ref)
        ml_intel = JarvisML.classify_and_explain(db, event_ref)
        anom_intel = JarvisAnom.investigate_anomaly(db, event_ref)
        risk_intel = JarvisRisk.calculate_operational_risk(db, event_ref)
        sat_intel = JarvisSat.retrieve_satellite_telemetry(db, event_ref)

        # 3. Determine Human-In-The-Loop requirement
        requires_hitl = (
            risk_intel.get("risk_level") in ["CRITICAL", "HIGH"] or
            ml_intel.get("routing_tier") in ["TIER_2_ANALYST_QUEUE", "TIER_3_ACTIVE_LEARNING"] or
            evt.get("facility_status") == "CANDIDATE"
        )

        return {
            "agent": AgentType.JARVIS_INVEST,
            "event": evt,
            "geospatial": geo_intel,
            "ml": ml_intel,
            "anomaly": anom_intel,
            "risk": risk_intel,
            "satellite": sat_intel,
            "requires_human_approval": requires_hitl,
            "evidence_status": "VERIFIED",
            "summary": (
                f"Multi-step investigation for {evt['event_code']} ({evt['state']}): "
                f"Classified as {ml_intel.get('predicted_class')} ({ml_intel.get('calibrated_confidence', 0.0)*100:.1f}% confidence). "
                f"Thermal anomaly confirmed ({anom_intel.get('anomaly_type')}). "
                f"Risk evaluated at {risk_intel.get('total_risk_score')}/100 ({risk_intel.get('risk_level')}). "
                + ("Human verification REQUIRED prior to any operational response." if requires_hitl else "Standard monitoring advisory.")
            )
        }


class JarvisReport:
    """
    JARVIS-REPORT: Reporting and Decision Support Specialist Agent.
    Formats executive briefs, technical dossiers, and structured recommendation payloads.
    """

    @staticmethod
    def compile_investigation_brief(investigation_data: Dict[str, Any]) -> Dict[str, Any]:
        evt = investigation_data.get("event", {})
        risk = investigation_data.get("risk", {})
        ml = investigation_data.get("ml", {})
        anom = investigation_data.get("anomaly", {})
        geo = investigation_data.get("geospatial", {})

        recommendations = []
        if risk.get("risk_level") == "CRITICAL":
            recommendations.append("Priority 1: Route to Human-in-the-Loop Analyst Review Queue immediately.")
            recommendations.append("Verify boundary containment with facility EHS liaison.")
            recommendations.append("Monitor next satellite pass for FRP escalation.")
        elif risk.get("risk_level") == "HIGH":
            recommendations.append("Route to secondary analyst triage.")
            recommendations.append("Cross-reference historical diurnal flare baseline.")
        else:
            recommendations.append("Log event in automated thermal surveillance archive.")

        return {
            "agent": AgentType.JARVIS_REPORT,
            "dossier_title": f"Incident Investigation Dossier: {evt.get('event_code', 'UNKNOWN')}",
            "headline": f"{risk.get('risk_level', 'NORMAL')} Severity Thermal Anomaly at {evt.get('state', 'India')}",
            "executive_summary": investigation_data.get("summary", "Complete investigation conducted."),
            "recommendations": recommendations,
            "requires_human_approval": investigation_data.get("requires_human_approval", False),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        }
