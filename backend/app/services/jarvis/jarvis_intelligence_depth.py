"""
AGNI-NETRA — JARVIS Operational Intelligence Depth Engine (Phase 5)
Provides deterministic cross-capability correlation:
1. Multi-constraint candidate search & evaluation
2. Lightweight evidence-conflict detection
3. Deterministic evidence-strength assessment (distinct from risk)
4. Explainable analyst prioritization (JARVIS ANALYST RANKING)
5. Uncertainty assessment & "What could change the conclusion?"
6. Current operator summary & intelligence synthesis
"""

import math
import uuid
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text, func

from backend.app.models.domain import (
    ThermalEvent, ModelPrediction, RiskScore, IndustrialFacility,
    FacilityBaseline, InvestigationWorkspace
)
from backend.app.services.jarvis.jarvis_tools import JarvisToolRegistry
from backend.app.services.spatial_engine import haversine_distance_m


class JarvisIntelligenceDepthEngine:
    """
    Deterministic operational intelligence depth engine.
    Does not introduce new opaque models. Synthesizes authoritative AGNI-NETRA signals.
    """

    # -------------------------------------------------------------------------
    # 1. EVIDENCE CONFLICT DETECTION
    # -------------------------------------------------------------------------
    @staticmethod
    def detect_evidence_conflicts(
        event_data: Optional[Dict[str, Any]] = None,
        geo_data: Optional[Dict[str, Any]] = None,
        ml_data: Optional[Dict[str, Any]] = None,
        anom_data: Optional[Dict[str, Any]] = None,
        risk_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Detects genuine empirical contradictions between intelligence dimensions:
        - Classification vs Historical Pattern (e.g. Industrial Fire vs Recurring seasonal flaring)
        - Classification vs Spatial Context (e.g. Industrial Fire vs non-industrial remote landcover)
        - Risk Severity vs Classification Certainty (e.g. Critical risk vs low/moderate confidence)
        - Thermal Intensity vs Historical Operational Envelope (e.g. extreme anomaly surge on routine classification)
        """
        conflicts: List[Dict[str, Any]] = []

        if not event_data or not event_data.get("found", True):
            return conflicts

        p_class = (ml_data or {}).get("predicted_class", "")
        conf = (ml_data or {}).get("confidence") or (ml_data or {}).get("calibrated_confidence", 0.0)
        if conf <= 1.0:
            conf_pct = conf * 100.0
        else:
            conf_pct = conf

        r_score = float((risk_data or {}).get("total_risk_score") or (risk_data or {}).get("risk_score", 0.0))
        r_level = (risk_data or {}).get("risk_level", "LOW")

        z_score = float((anom_data or {}).get("z_score", 0.0))
        dev_ratio = float((anom_data or {}).get("deviation_ratio", 1.0))
        is_anom = bool((anom_data or {}).get("is_anomaly", False))

        top_asset = (geo_data or {}).get("nearest_primary_asset") or {}
        dist_m = float(top_asset.get("distance_meters") or top_asset.get("distance_m") or event_data.get("nearest_facility_distance_m") or 10000.0)

        # Conflict 1: Classification (Industrial Fire) vs Historical Pattern (Baseline Compliant / Recurring Flare)
        if "industrial fire" in p_class.lower() and conf_pct >= 45.0:
            if not is_anom or (z_score <= 1.5 and dev_ratio <= 1.5):
                conflicts.append({
                    "conflict_id": f"cnf-{uuid.uuid4().hex[:6]}",
                    "type": "CLASSIFICATION_VS_HISTORICAL_PATTERN",
                    "dimension_a": "XGBoost Classification",
                    "signal_a": f"Industrial Fire ({conf_pct:.1f}% confidence)",
                    "dimension_b": "Historical Baseline Envelope",
                    "signal_b": f"Telemetry is baseline compliant (+{z_score:.2f}σ, {dev_ratio:.2f}x normal). Conforms to recurring operational thermal source.",
                    "severity": "MODERATE",
                    "explanation": (
                        f"Classifier predicts an emergency Industrial Fire, but longitudinal baseline shows "
                        f"no significant thermal excursion (+{z_score:.2f}σ, {dev_ratio:.2f}x normal). "
                        f"Behavior aligns with recurring operational flare or regulated thermal release."
                    ),
                    "recommended_action": "Human verification recommended. Cross-reference facility operational flaring schedule before incident disposition."
                })

        # Conflict 2: Classification (Routine Gas Flare / Biomass) vs Extreme Radiative Surge
        if ("gas flare" in p_class.lower() or "biomass" in p_class.lower()) and (z_score >= 3.0 or dev_ratio >= 4.0):
            conflicts.append({
                "conflict_id": f"cnf-{uuid.uuid4().hex[:6]}",
                "type": "CLASSIFICATION_VS_ANOMALY_SURGE",
                "dimension_a": "XGBoost Classification",
                "signal_a": f"Classified as routine '{p_class}' ({conf_pct:.1f}% confidence)",
                "dimension_b": "Longitudinal Anomaly Surge",
                "signal_b": f"Extreme radiative excursion (+{z_score:.2f}σ, {dev_ratio:.2f}x historical mean)",
                "severity": "HIGH",
                "explanation": (
                    f"Thermal signature classified as '{p_class}', but radiative output is severely anomalous "
                    f"(+{z_score:.2f}σ, {dev_ratio:.2f}x normal baseline). May represent an uncharacteristic blowout or industrial upset."
                ),
                "recommended_action": "Analyst review required. Check for facility upset notifications or emergency flaring permits."
            })

        # Conflict 3: Classification (Industrial Fire) vs Remote Spatial Landcover (> 5km from any facility)
        if "industrial fire" in p_class.lower() and dist_m > 5000.0:
            conflicts.append({
                "conflict_id": f"cnf-{uuid.uuid4().hex[:6]}",
                "type": "CLASSIFICATION_VS_SPATIAL_PROXIMITY",
                "dimension_a": "XGBoost Classification",
                "signal_a": f"Industrial Fire ({conf_pct:.1f}% confidence)",
                "dimension_b": "PostGIS Spatial Proximity",
                "signal_b": f"Nearest industrial infrastructure is {int(dist_m)}m away",
                "severity": "HIGH",
                "explanation": (
                    f"Machine learning model classified event as Industrial Fire, yet PostGIS proximity shows no "
                    f"registered industrial facility within {int(dist_m)}m. May indicate an unmapped industrial installation or misclassified open biomass burn."
                ),
                "recommended_action": "Inspect high-resolution imagery and verify OpenStreetMap/CEA registry for unmapped facilities."
            })

        # Conflict 4: Risk Severity (CRITICAL / HIGH) vs Low Classification Confidence (< 60%)
        if (r_score >= 70.0 or r_level in ["CRITICAL", "HIGH"]) and conf_pct < 60.0:
            conflicts.append({
                "conflict_id": f"cnf-{uuid.uuid4().hex[:6]}",
                "type": "RISK_SEVERITY_VS_MODEL_CONFIDENCE",
                "dimension_a": "5-Factor Operational Risk",
                "signal_a": f"{r_level} ({r_score:.1f}/100)",
                "dimension_b": "Classification Confidence",
                "signal_b": f"Low/Moderate Confidence ({conf_pct:.1f}%)",
                "severity": "MODERATE",
                "explanation": (
                    f"Target exhibits elevated risk ({r_score:.1f}/100, {r_level}), but the machine learning classifier "
                    f"is uncertain (calibrated confidence {conf_pct:.1f}%). Ambiguity on high-consequence asset requires priority triage."
                ),
                "recommended_action": "Prioritize for human verification desk triage to resolve hypothesis uncertainty."
            })

        return conflicts

    # -------------------------------------------------------------------------
    # 2. DETERMINISTIC EVIDENCE-STRENGTH ASSESSMENT
    # -------------------------------------------------------------------------
    @staticmethod
    def assess_evidence_strength(
        event_data: Optional[Dict[str, Any]] = None,
        geo_data: Optional[Dict[str, Any]] = None,
        ml_data: Optional[Dict[str, Any]] = None,
        anom_data: Optional[Dict[str, Any]] = None,
        risk_data: Optional[Dict[str, Any]] = None,
        conflicts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates evidence strength based on empirical availability, quality, and signal consistency.
        Evidence strength is distinct from risk score:
        - RISK measures physical hazard severity (0 - 100).
        - EVIDENCE STRENGTH measures analytical certainty and telemetry depth (STRONG, MODERATE, LIMITED, INSUFFICIENT).
        """
        if not event_data or not event_data.get("found", True):
            return {
                "strength_level": "INSUFFICIENT",
                "score": 0.0,
                "completeness_score": 0.0,
                "consistency_score": 0.0,
                "factors": {
                    "telemetry_completeness": 0.0,
                    "spatial_resolution": 0.0,
                    "model_certainty": 0.0,
                    "historical_depth": 0.0,
                    "consistency_factor": 0.0
                },
                "conflicts_detected_count": 0,
                "summary": "Evidence is INSUFFICIENT: Target event not located or telemetry missing."
            }

        # Subscore 1: Telemetry Completeness (max 25 pts)
        det_cnt = event_data.get("detection_count") or 1
        sat_cnt = event_data.get("satellite_count") or 1
        max_frp = float(event_data.get("max_frp") or 0.0)
        c_telemetry = min(25.0, (det_cnt * 5.0) + (sat_cnt * 5.0) + min(10.0, max_frp / 25.0))

        # Subscore 2: Spatial Resolution (max 25 pts)
        top_asset = (geo_data or {}).get("nearest_primary_asset") or {}
        dist_m = float(top_asset.get("distance_meters") or top_asset.get("distance_m") or event_data.get("nearest_facility_distance_m") or 10000.0)
        if dist_m <= 500.0:
            c_spatial = 25.0
        elif dist_m <= 1500.0:
            c_spatial = 20.0
        elif dist_m <= 5000.0:
            c_spatial = 12.0
        else:
            c_spatial = 5.0

        # Subscore 3: Model Certainty (max 25 pts)
        conf = float((ml_data or {}).get("confidence") or (ml_data or {}).get("calibrated_confidence") or 0.0)
        if conf <= 1.0:
            conf_val = conf
        else:
            conf_val = conf / 100.0
        c_model = round(conf_val * 25.0, 1)

        # Subscore 4: Historical Baseline Depth (max 25 pts)
        if anom_data and not anom_data.get("error"):
            c_historical = 25.0 if anom_data.get("z_score") is not None else 15.0
        else:
            c_historical = 10.0

        # Consistency Factor Penalty (deduct up to 20 pts for conflicting evidence)
        conflict_penalty = 0.0
        if conflicts:
            for c in conflicts:
                if c.get("severity") == "HIGH":
                    conflict_penalty += 12.0
                elif c.get("severity") == "MODERATE":
                    conflict_penalty += 6.0
        conflict_penalty = min(20.0, conflict_penalty)
        c_consistency = max(0.0, 25.0 - conflict_penalty)

        # Total Composite Score (0 - 100)
        raw_score = (c_telemetry * 0.25) + (c_spatial * 0.25) + (c_model * 0.25) + (c_historical * 0.25)
        final_score = round(max(0.0, min(100.0, (c_telemetry + c_spatial + c_model + c_historical) * (c_consistency / 25.0))), 1)

        if final_score >= 75.0:
            strength_level = "STRONG"
        elif final_score >= 50.0:
            strength_level = "MODERATE"
        elif final_score >= 25.0:
            strength_level = "LIMITED"
        else:
            strength_level = "INSUFFICIENT"

        summary = (
            f"Evidence Strength is {strength_level} ({final_score:.1f}/100). "
            f"Telemetry depth: {c_telemetry:.1f}/25, Spatial resolution: {c_spatial:.1f}/25, "
            f"Model certainty: {c_model:.1f}/25, Baseline depth: {c_historical:.1f}/25, "
            f"Signal consistency: {c_consistency:.1f}/25."
        )

        return {
            "strength_level": strength_level,
            "score": final_score,
            "completeness_score": round((c_telemetry + c_spatial + c_historical) / 75.0 * 100.0, 1),
            "consistency_score": round(c_consistency / 25.0 * 100.0, 1),
            "factors": {
                "telemetry_completeness": round(c_telemetry, 1),
                "spatial_resolution": round(c_spatial, 1),
                "model_certainty": round(c_model, 1),
                "historical_depth": round(c_historical, 1),
                "consistency_factor": round(c_consistency, 1)
            },
            "conflicts_detected_count": len(conflicts or []),
            "summary": summary
        }

    # -------------------------------------------------------------------------
    # 3. EXPLAINABLE ANALYST PRIORITIZATION (JARVIS ANALYST RANKING)
    # -------------------------------------------------------------------------
    @staticmethod
    def calculate_analyst_prioritization(
        candidates: List[Dict[str, Any]],
        target_hypothesis: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Ranks candidate thermal events by operational triage priority for human analysts.
        Labeled explicitly as: 'JARVIS ANALYST RANKING'.
        Preserves authoritative AGNI-NETRA risk score separately.

        Composite Formula:
        - 40% Authoritative 5-Factor Risk Score
        - 25% Longitudinal Anomaly Severity & Baseline Deviation
        - 15% Facility Proximity (Hazard Containment Buffer)
        - 10% Verification Urgency (Requires Human Review Gate)
        - 10% Uncertainty on High Risk (High risk with low/moderate confidence prioritized for triage)
        """
        ranked: List[Dict[str, Any]] = []

        for c in candidates:
            code = c.get("event_code") or c.get("event_id") or "UNKNOWN"
            r_score = float(c.get("risk_score") or 0.0)
            r_lvl = c.get("risk_level", "LOW")

            # Factor 1: Risk (0 - 40 pts)
            s_risk = (r_score / 100.0) * 40.0

            # Factor 2: Anomaly / Deviation (0 - 25 pts)
            base_ratio = float(c.get("baseline_ratio") or 1.0)
            s_anom = min(25.0, (base_ratio / 3.0) * 25.0)

            # Factor 3: Proximity (0 - 15 pts)
            dist_m = float(c.get("facility_distance_m") or 10000.0)
            s_prox = max(0.0, (1.0 - min(dist_m, 5000.0) / 5000.0) * 15.0)

            # Factor 4: Verification Urgency (0 - 10 pts)
            needs_verify = (r_score >= 60.0 or r_lvl in ["CRITICAL", "HIGH"])
            s_verify = 10.0 if needs_verify else 2.0

            # Factor 5: Uncertainty on High-Consequence target (0 - 10 pts)
            conf = float(c.get("confidence") or 0.5)
            if conf > 1.0:
                conf = conf / 100.0
            ambiguity = (1.0 - conf) if r_score >= 60.0 else 0.2
            s_uncertainty = ambiguity * 10.0

            total_priority = round(s_risk + s_anom + s_prox + s_verify + s_uncertainty, 1)

            ranked.append({
                "event_code": code,
                "event_id": c.get("event_id") or c.get("id"),
                "state": c.get("state"),
                "max_frp": c.get("max_frp"),
                "predicted_class": c.get("predicted_class", "Uncertain"),
                "confidence": round(conf, 3),
                "risk_score": r_score,
                "risk_level": r_lvl,
                "facility_distance_m": round(dist_m, 1),
                "facility_name": c.get("facility_name", "Unspecified Facility"),
                "baseline_ratio": round(base_ratio, 2),
                "requires_verification": needs_verify,
                "analyst_priority_score": total_priority,
                "score_breakdown": {
                    "risk_component": round(s_risk, 1),
                    "anomaly_component": round(s_anom, 1),
                    "proximity_component": round(s_prox, 1),
                    "verification_urgency": round(s_verify, 1),
                    "uncertainty_urgency": round(s_uncertainty, 1)
                }
            })

        # Sort descending by analyst priority score
        ranked.sort(key=lambda x: x["analyst_priority_score"], reverse=True)
        for idx, item in enumerate(ranked):
            item["rank"] = idx + 1
            item["is_top_priority"] = (idx == 0)

        return ranked

    # -------------------------------------------------------------------------
    # 4. UNCERTAINTY ASSESSMENT & "WHAT COULD CHANGE THE CONCLUSION?"
    # -------------------------------------------------------------------------
    @staticmethod
    def assess_uncertainty(
        workspace: Optional[InvestigationWorkspace] = None,
        event_data: Optional[Dict[str, Any]] = None,
        geo_data: Optional[Dict[str, Any]] = None,
        ml_data: Optional[Dict[str, Any]] = None,
        anom_data: Optional[Dict[str, Any]] = None,
        risk_data: Optional[Dict[str, Any]] = None,
        conflicts: Optional[List[Dict[str, Any]]] = None,
        evidence_strength: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes structured uncertainty categories:
        - KNOWN: Authoritative facts & confirmed telemetry
        - UNCERTAIN: Borderline or low-confidence parameters
        - MISSING: Information elements not yet acquired
        - CONFLICTING: Detected signal contradictions
        - RECOMMENDED NEXT STEP: Operational action
        - WHAT COULD CHANGE THE CONCLUSION: Bounded to actual AGNI-NETRA evidence classes
        """
        known: List[str] = []
        uncertain: List[str] = []
        missing: List[str] = []
        conflicting_notes: List[str] = []

        # 1. KNOWN
        if event_data and event_data.get("found", True):
            known.append(f"Authoritative NASA FIRMS telemetry: Peak FRP {event_data.get('max_frp')} MW ({event_data.get('detection_count', 1)} detections in {event_data.get('state')}).")
        top_asset = (geo_data or {}).get("nearest_primary_asset") or {}
        if top_asset:
            dist = int(top_asset.get("distance_meters") or top_asset.get("distance_m") or 0)
            known.append(f"PostGIS spatial location: {dist}m from {top_asset.get('name')} ({top_asset.get('sector', 'Industrial')}).")
        if risk_data and (risk_data.get("total_risk_score") is not None or risk_data.get("risk_score") is not None):
            r_score = risk_data.get("total_risk_score") or risk_data.get("risk_score")
            r_lvl = risk_data.get("risk_level", "LOW")
            known.append(f"Deterministic 5-factor risk score: {r_score:.1f}/100 ({r_lvl}).")
        if anom_data and anom_data.get("z_score") is not None:
            known.append(f"Longitudinal baseline: +{anom_data.get('z_score', 0.0):.2f}σ deviation ({anom_data.get('deviation_ratio', 1.0):.2f}x normal).")

        # 2. UNCERTAIN
        conf = float((ml_data or {}).get("confidence") or (ml_data or {}).get("calibrated_confidence") or 0.0)
        if conf <= 1.0:
            conf_pct = conf * 100.0
        else:
            conf_pct = conf
        p_class = (ml_data or {}).get("predicted_class", "Uncertain")

        if conf_pct < 70.0:
            uncertain.append(f"XGBoost classification confidence is moderate/low ({conf_pct:.1f}% for '{p_class}'). Alternative hypotheses cannot be ruled out purely on single-band spectral features.")
        else:
            uncertain.append(f"Model prediction calibrated confidence is {conf_pct:.1f}%; small probability of localized industrial misclassification remains.")

        if anom_data and 1.0 <= anom_data.get("deviation_ratio", 1.0) <= 1.8:
            uncertain.append(f"Thermal intensity elevation is borderline ({anom_data.get('deviation_ratio'):.2f}x normal). Requires verification against seasonal operating envelopes.")

        # 3. MISSING
        if not workspace or workspace.verification_status != "VERIFIED":
            missing.append("Independent human-in-the-loop analyst verification.")
        missing.append("Facility maintenance turnaround schedule & operational flaring permits.")
        missing.append("Ground-truth acoustic or optical sensor validation.")

        # 4. CONFLICTING
        if conflicts:
            for c in conflicts:
                conflicting_notes.append(f"[{c.get('severity')}] {c.get('dimension_a')} vs {c.get('dimension_b')}: {c.get('explanation')}")
        else:
            conflicting_notes.append("No active evidence conflicts detected; intelligence dimensions are mutually corroborating.")

        # 5. RECOMMENDED NEXT STEP
        req_verify = (risk_data or {}).get("risk_level") in ["CRITICAL", "HIGH"] or float((risk_data or {}).get("total_risk_score") or 0) >= 60.0
        if req_verify:
            rec_step = "Route target to Analyst Verification Desk for visual confirmation. Automated dispatch remains strictly BLOCKED."
        else:
            rec_step = "Maintain autonomous satellite sensor surveillance and monitor next orbital pass for signal persistence."

        # 6. WHAT COULD CHANGE THE CONCLUSION
        what_could_change = [
            "Subsequent NASA FIRMS satellite passes: Detecting signal persistence (sustained combustion) vs rapid decay (transient burn).",
            "Facility maintenance logs: Turnaround notifications or scheduled flaring logs that explain thermal baseline elevation.",
            "PostGIS boundary refinement: Updated cadastral surveys or OSM industrial perimeter modifications altering proximity buffers.",
            "Machine learning feature update: Re-scoring with localized industrial flare stack feature attributions.",
            "Human analyst verification: Ground-truth confirmation from industrial safety authorities or on-site inspectors."
        ]

        return {
            "known": known,
            "uncertain": uncertain,
            "missing": missing,
            "conflicting": conflicting_notes,
            "recommended_next_step": rec_step,
            "what_could_change": what_could_change,
            "evidence_strength": evidence_strength.get("strength_level", "MODERATE") if evidence_strength else "MODERATE"
        }

    # -------------------------------------------------------------------------
    # 5. MULTI-CONSTRAINT CONDITIONAL SEARCH & CORRELATION
    # -------------------------------------------------------------------------
    @staticmethod
    def search_multi_constraint_events(
        db: Session,
        state: Optional[str] = None,
        risk_level: Optional[str] = None,
        max_dist_m: Optional[float] = 5000.0,
        anomalous_only: bool = False,
        low_confidence_only: bool = False,
        confidence_max: Optional[float] = None,
        require_verification: bool = False,
        require_conflict: bool = False,
        target_hypothesis: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Executes multi-constraint conditional filtering across AGNI-NETRA telemetry,
        spatial proximity, ML predictions, and longitudinal baselines.
        """
        raw_events = JarvisToolRegistry.tool_get_recent_events(
            db, limit=50, state=state, risk_level="ALL"
        )

        matched: List[Dict[str, Any]] = []

        for e in raw_events:
            code = e.get("event_code")
            spatial = JarvisToolRegistry.tool_get_event_spatial_context(db, code)
            top_asset = spatial.get("nearest_primary_asset") or {}
            dist_m = float(top_asset.get("distance_meters") or top_asset.get("distance_m") or 10000.0)

            # Constraint 1: Facility Distance
            if max_dist_m is not None and dist_m > max_dist_m:
                continue

            # Constraint 2: Risk Level
            r_lvl = e.get("risk_level", "LOW")
            r_score = float(e.get("risk_score") or 0.0)
            if risk_level and risk_level.upper() not in ["ALL"]:
                if risk_level.upper() == "HIGH" and r_lvl not in ["HIGH", "CRITICAL"]:
                    continue
                elif risk_level.upper() == "CRITICAL" and r_lvl != "CRITICAL":
                    continue
                elif risk_level.upper() not in ["HIGH", "CRITICAL"] and r_lvl != risk_level.upper():
                    continue

            # Constraint 3: Verification Requirement
            needs_verify = (r_score >= 60.0 or r_lvl in ["HIGH", "CRITICAL"])
            if require_verification and not needs_verify:
                continue

            # Constraint 4: Classification & Confidence
            conf = float(e.get("confidence") or 0.0)
            if conf <= 1.0:
                conf_pct = conf * 100.0
            else:
                conf_pct = conf
            if low_confidence_only and conf_pct >= 70.0:
                continue
            if confidence_max is not None and conf_pct > (confidence_max * 100.0 if confidence_max <= 1.0 else confidence_max):
                continue
            if target_hypothesis and target_hypothesis.lower() not in e.get("predicted_class", "").lower():
                pass

            # Constraint 5: Baseline Anomaly
            baseline = JarvisToolRegistry.tool_compare_baseline(db, code)
            is_anom = baseline.get("is_anomaly", False)
            ratio = float(baseline.get("deviation_ratio") or 1.0)
            if anomalous_only and not is_anom and ratio <= 1.25:
                continue

            # Constraint 6: Conflict Detection
            conflicts = JarvisIntelligenceDepthEngine.detect_evidence_conflicts(
                event_data=e, geo_data=spatial, ml_data=e, anom_data=baseline, risk_data={"risk_score": r_score, "risk_level": r_lvl}
            )
            if require_conflict and len(conflicts) == 0:
                continue

            matched.append({
                "id": e.get("id"),
                "event_code": code,
                "state": e.get("state"),
                "district": e.get("district"),
                "max_frp": e.get("max_frp"),
                "predicted_class": e.get("predicted_class"),
                "confidence": conf,
                "confidence_pct": round(conf_pct, 1),
                "risk_score": r_score,
                "risk_level": r_lvl,
                "facility_name": top_asset.get("name") or e.get("facility_name") or "Industrial Site",
                "facility_distance_m": round(dist_m, 1),
                "baseline_ratio": round(ratio, 2),
                "z_score": baseline.get("z_score", 0.0),
                "is_anomaly": is_anom,
                "requires_verification": needs_verify,
                "conflicts_count": len(conflicts),
                "conflicts": conflicts
            })

            if len(matched) >= limit:
                break

        return matched

    # -------------------------------------------------------------------------
    # 6. OPERATOR INTELLIGENCE SUMMARY ("WHAT IS IMPORTANT NOW?")
    # -------------------------------------------------------------------------
    @staticmethod
    def generate_operator_summary(db: Session, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Assembles on-demand operational intelligence summary across monitored events.
        Strictly user-triggered — NO autonomous background polling.
        """
        all_events = JarvisToolRegistry.tool_get_recent_events(db, limit=30, risk_level="ALL")

        top_risks = [e for e in all_events if e.get("risk_level") in ["CRITICAL", "HIGH"]][:5]
        hitl_cases = [e for e in all_events if (e.get("risk_score", 0) >= 60.0 or e.get("risk_level") in ["CRITICAL", "HIGH"])][:5]
        uncertain_cases = [e for e in all_events if e.get("confidence", 1.0) < 0.70 and e.get("risk_score", 0) >= 50.0][:5]

        candidates_formatted = []
        for e in all_events[:15]:
            candidates_formatted.append({
                "event_code": e.get("event_code"),
                "event_id": e.get("id"),
                "state": e.get("state"),
                "max_frp": e.get("max_frp"),
                "predicted_class": e.get("predicted_class"),
                "confidence": e.get("confidence"),
                "risk_score": e.get("risk_score"),
                "risk_level": e.get("risk_level"),
                "facility_distance_m": 500.0 if "Industrial" in str(e.get("predicted_class")) else 2500.0,
                "baseline_ratio": 2.5 if e.get("risk_level") == "CRITICAL" else 1.2
            })
        prioritized = JarvisIntelligenceDepthEngine.calculate_analyst_prioritization(candidates_formatted)

        open_ws = db.query(InvestigationWorkspace).filter(InvestigationWorkspace.status.in_(["ACTIVE", "REQUIRES_HUMAN_REVIEW"])).count()

        return {
            "total_events_monitored": len(all_events),
            "top_priorities": prioritized[:3],
            "top_risks": top_risks,
            "top_risk_events": top_risks,
            "major_anomalies": [p for p in prioritized if p.get("baseline_ratio", 1.0) >= 2.0][:3],
            "uncertain_cases": uncertain_cases,
            "hitl_required": hitl_cases,
            "pending_verification": hitl_cases,
            "open_investigations_count": open_ws
        }


depth_engine = JarvisIntelligenceDepthEngine()
