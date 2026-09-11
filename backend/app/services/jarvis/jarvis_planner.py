"""
AGNI-NETRA — JARVIS Execution Planner
Translates parsed intent, extracted entities, and operational constraints into a dynamic,
declarative multi-step execution plan controlled by ONE Master Agent (JARVIS).
"""

from typing import Dict, Any, List, Optional
from backend.app.models.jarvis_schemas import (
    CommandIntent, AgentType, StepStatus, ExecutionStep, JarvisCapability
)


class JarvisExecutionPlanner:
    """
    Constructs declarative execution plans dynamically based on command intent and entities.
    Enforces ONE master agent (JARVIS) invoking specialized internal capabilities.
    """

    @staticmethod
    def build_plan(
        intent: CommandIntent,
        entities: Dict[str, Any],
        user_role: str = "ANALYST"
    ) -> List[ExecutionStep]:
        steps: List[ExecutionStep] = []
        event_ref = entities.get("event_ref", "EVT-827")
        state = entities.get("state")
        dist_m = entities.get("distance_m", 5000.0)
        is_composite = entities.get("is_composite", False)

        # Step 1: Invariant Safety & Guardian Gate Check (All Plans)
        steps.append(ExecutionStep(
            step_number=1,
            agent="JARVIS",
            capability=JarvisCapability.SYSTEM_GOVERNANCE.value,
            action="Validate Permissions, Safety Invariants, and Dispatch Gate",
            tool="guard_authorize_action",
            parameters={"user_role": user_role, "intent": str(intent)},
            status=StepStatus.PENDING
        ))

        # Branch on Intent
        if intent == CommandIntent.DISPATCH_REQUEST:
            # Plan only contains the blocked step
            return steps

        objective = entities.get("objective")

        # Branch: Multi-Event Comparative Investigation & Strongest Case Identification
        is_multi_compare = (
            entities.get("multi_candidate", False) or
            entities.get("compare_with_others", False) or
            (objective and getattr(objective, "primary_goal", None) in ["MULTI_EVENT_COMPARE", "INVESTIGATE_AND_IDENTIFY_STRONGEST"])
        )
        if is_multi_compare:
            cand_count = entities.get("candidate_count", 3)
            target_hypo = entities.get("target_hypothesis", "Industrial Fire")
            step_num = 2
            
            if event_ref and entities.get("compare_with_others"):
                steps.append(ExecutionStep(
                    step_number=step_num,
                    agent="JARVIS",
                    capability=JarvisCapability.THERMAL_INTELLIGENCE.value,
                    action=f"Retrieve Benchmark Target Entity ({event_ref})",
                    tool="tool_get_event",
                    parameters={"event_ref": event_ref},
                    status=StepStatus.PENDING
                ))
                step_num += 1

            steps.append(ExecutionStep(
                step_number=step_num,
                agent="JARVIS",
                capability=JarvisCapability.THERMAL_INTELLIGENCE.value,
                action=f"Retrieve {cand_count} High-Priority Candidate Events ({state or 'All Regions'})",
                tool="tool_get_recent_events",
                parameters={"limit": cand_count + (1 if event_ref else 0), "state": state, "risk_level": "CRITICAL"},
                status=StepStatus.PENDING
            ))
            step_num += 1

            steps.append(ExecutionStep(
                step_number=step_num,
                agent="JARVIS",
                capability=JarvisCapability.THERMAL_INTELLIGENCE.value,
                action=f"Execute Comparative Multi-Event Evaluation against '{target_hypo}'",
                tool="tool_compare_candidate_events",
                parameters={"event_refs": [event_ref] if event_ref else [], "target_hypothesis": target_hypo},
                status=StepStatus.PENDING
            ))
            step_num += 1

            steps.append(ExecutionStep(
                step_number=step_num,
                agent="JARVIS",
                capability=JarvisCapability.THERMAL_INTELLIGENCE.value,
                action="Synthesize Comparative Ranking & Identify Strongest Empirical Case",
                tool="fuse_evidence",
                status=StepStatus.PENDING
            ))
            return steps

        # Branch: Multi-Constraint Spatial & Historical Baseline Filter
        is_multi_constraint = (
            (objective and getattr(objective, "primary_goal", None) == "MULTI_CONSTRAINT_FILTER") or
            (
                entities.get("baseline_condition", False)
                and not event_ref
                and not entities.get("is_composite", False)
                and not entities.get("require_dossier", False)
            )
        )
        if is_multi_constraint:
            steps.append(ExecutionStep(
                step_number=2,
                agent="JARVIS",
                capability=JarvisCapability.GEOINT.value,
                action=f"Filter High-Risk Anomalies within {int(dist_m/1000)}km of Facilities with Anomalous Historical Baseline",
                tool="tool_search_critical_anomalies_near_facilities",
                parameters={
                    "state": state,
                    "max_dist_m": dist_m,
                    "risk_level": entities.get("risk_level", "HIGH"),
                    "baseline_anomalous_only": True
                },
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=3,
                agent="JARVIS",
                capability=JarvisCapability.GEOINT.value,
                action="Synthesize Multi-Constraint Spatial & Historical Baseline Findings",
                tool="fuse_evidence",
                status=StepStatus.PENDING
            ))
            return steps

        # Branch: Surgical Stop Investigation (Explain Classification and Risk only)
        is_surgical = (
            entities.get("surgical_stop", False) or
            (objective and getattr(objective, "primary_goal", None) == "SURGICAL_EXPLANATION")
        )
        if is_surgical:
            steps.append(ExecutionStep(
                step_number=2,
                agent="JARVIS",
                capability=JarvisCapability.THERMAL_INTELLIGENCE.value,
                action=f"Retrieve Entity Record for {event_ref}",
                tool="tool_get_event",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=3,
                agent="JARVIS",
                capability=JarvisCapability.GEOINT.value,
                action="Evaluate PostGIS Spatial Proximity and Buffer Boundaries",
                tool="tool_get_event_spatial_context",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=4,
                agent="JARVIS",
                capability=JarvisCapability.CLASSIFICATION.value,
                action="Execute XGBoost Multi-Class Inference & Balanced Platt Calibration",
                tool="tool_classify_event",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=5,
                agent="JARVIS",
                capability=JarvisCapability.CLASSIFICATION.value,
                action="Extract TreeExplainer SHAP Local Feature Attributions",
                tool="tool_get_shap_drivers",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=6,
                agent="JARVIS",
                capability=JarvisCapability.RISK_ANALYSIS.value,
                action="Deconstruct 5-Factor Authoritative Operational Risk Score",
                tool="tool_calculate_risk",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=7,
                agent="JARVIS",
                capability=JarvisCapability.SYSTEM_GOVERNANCE.value,
                action="Synthesize Classification and Risk Evidence with Strict Sufficiency Stop",
                tool="fuse_evidence",
                status=StepStatus.PENDING
            ))
            return steps

        elif intent == CommandIntent.QUERY or intent == CommandIntent.RANK:
            steps.append(ExecutionStep(
                step_number=2,
                agent="JARVIS",
                capability=JarvisCapability.THERMAL_INTELLIGENCE.value,
                action="Retrieve Recent High-Priority Thermal Events from Database",
                tool="tool_get_recent_events",
                parameters={"limit": 10, "state": state, "risk_level": entities.get("risk_level", "CRITICAL")},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=3,
                agent="JARVIS",
                capability=JarvisCapability.THERMAL_INTELLIGENCE.value,
                action="Fuse Event List Evidence and Assess Triage Priorities",
                tool="fuse_evidence",
                status=StepStatus.PENDING
            ))

        elif intent == CommandIntent.VERIFY:
            steps.append(ExecutionStep(
                step_number=2,
                agent="JARVIS",
                capability=JarvisCapability.VERIFICATION.value,
                action="Query Tri-Tier Human-In-The-Loop Operational Review Queue",
                tool="tool_get_human_verification_queue",
                parameters={"limit": 10},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=3,
                agent="JARVIS",
                capability=JarvisCapability.VERIFICATION.value,
                action="Synthesize HITL Triage Requirements",
                tool="fuse_evidence",
                status=StepStatus.PENDING
            ))

        elif intent == CommandIntent.STATUS:
            steps.append(ExecutionStep(
                step_number=2,
                agent="JARVIS",
                capability=JarvisCapability.SYSTEM_GOVERNANCE.value,
                action="Query Real-Time Telemetry, PostGIS, FIRMS Ingestion, and ML Model Governance",
                tool="tool_get_system_status",
                parameters={},
                status=StepStatus.PENDING
            ))

        elif intent == CommandIntent.LOCATE and not is_composite:
            steps.append(ExecutionStep(
                step_number=2,
                agent="JARVIS",
                capability=JarvisCapability.GEOINT.value,
                action=f"Execute PostGIS Spatial Join (Buffer {int(dist_m/1000)}km near Industrial Polygons)",
                tool="tool_search_critical_anomalies_near_facilities",
                parameters={"state": state or "Gujarat", "max_dist_m": dist_m, "risk_level": "CRITICAL"},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=3,
                agent="JARVIS",
                capability=JarvisCapability.GEOINT.value,
                action="Synthesize Spatial Proximity Results & Flag Vulnerabilities",
                tool="fuse_evidence",
                status=StepStatus.PENDING
            ))

        elif intent == CommandIntent.COMPARE and not is_composite:
            steps.append(ExecutionStep(
                step_number=2,
                agent="JARVIS",
                capability=JarvisCapability.THERMAL_INTELLIGENCE.value,
                action="Retrieve Entity Attributes for Thermal Event",
                tool="tool_get_event",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=3,
                agent="JARVIS",
                capability=JarvisCapability.HISTORICAL_ANALYSIS.value,
                action="Compare Current FRP against Longitudinal Facility & Regional Baseline",
                tool="tool_compare_baseline",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=4,
                agent="JARVIS",
                capability=JarvisCapability.HISTORICAL_ANALYSIS.value,
                action="Fuse Baseline Deviation & Diurnal Context",
                tool="fuse_evidence",
                status=StepStatus.PENDING
            ))

        elif intent == CommandIntent.EXPLAIN and not is_composite:
            explain_type = entities.get("explain_type", "RISK")
            steps.append(ExecutionStep(
                step_number=2,
                agent="JARVIS",
                capability=JarvisCapability.THERMAL_INTELLIGENCE.value,
                action="Retrieve Event Entity and Attributes",
                tool="tool_get_event",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            if explain_type == "SHAP":
                steps.append(ExecutionStep(
                    step_number=3,
                    agent="JARVIS",
                    capability=JarvisCapability.CLASSIFICATION.value,
                    action="Extract TreeExplainer SHAP Local Feature Attributions",
                    tool="tool_get_shap_drivers",
                    parameters={"event_ref": event_ref},
                    status=StepStatus.PENDING
                ))
            else:
                steps.append(ExecutionStep(
                    step_number=3,
                    agent="JARVIS",
                    capability=JarvisCapability.RISK_ANALYSIS.value,
                    action="Deconstruct Multi-Factor Risk Score (Intensity, Abnormality, Exposure, Persistence, Context)",
                    tool="tool_calculate_risk",
                    parameters={"event_ref": event_ref},
                    status=StepStatus.PENDING
                ))
            steps.append(ExecutionStep(
                step_number=4,
                agent="JARVIS",
                capability=JarvisCapability.RISK_ANALYSIS.value,
                action="Synthesize Grounded Explanations with Quantitative Drivers",
                tool="fuse_evidence",
                status=StepStatus.PENDING
            ))

        elif intent == CommandIntent.GENERATE_REPORT and not is_composite:
            steps.append(ExecutionStep(
                step_number=2,
                agent="JARVIS",
                capability=JarvisCapability.THERMAL_INTELLIGENCE.value,
                action="Compile Multi-Source Investigation Data",
                tool="tool_get_event",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=3,
                agent="JARVIS",
                capability=JarvisCapability.REPORTING.value,
                action="Compile Formal Technical Dossier & Generate PDF Stream",
                tool="tool_generate_investigation_dossier",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))

        elif is_composite or entities.get("near_facility"):
            # Composite Multi-Capability Command Plan
            # e.g., "find highest risk near facility -> investigate -> explain risk -> compare baseline -> generate dossier"
            cur_step = 2
            if entities.get("near_facility") or not entities.get("event_ref"):
                steps.append(ExecutionStep(
                    step_number=cur_step,
                    agent="JARVIS",
                    capability=JarvisCapability.GEOINT.value,
                    action=f"Search Critical Thermal Anomalies Near Industrial Facilities ({state or 'Gujarat'})",
                    tool="tool_search_critical_anomalies_near_facilities",
                    parameters={"state": state or "Gujarat", "max_dist_m": dist_m, "risk_level": "CRITICAL"},
                    status=StepStatus.PENDING
                ))
                cur_step += 1

            steps.append(ExecutionStep(
                step_number=cur_step,
                agent="JARVIS",
                capability=JarvisCapability.THERMAL_INTELLIGENCE.value,
                action="Retrieve Thermal Event Entity and Detections",
                tool="tool_get_event",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            cur_step += 1

            steps.append(ExecutionStep(
                step_number=cur_step,
                agent="JARVIS",
                capability=JarvisCapability.GEOINT.value,
                action="[PARALLEL] Evaluate PostGIS Spatial Proximity and Buffer Boundaries",
                tool="tool_get_event_spatial_context",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            cur_step += 1

            steps.append(ExecutionStep(
                step_number=cur_step,
                agent="JARVIS",
                capability=JarvisCapability.CLASSIFICATION.value,
                action="[PARALLEL] Execute XGBoost Multi-Class Inference & Balanced Platt Calibration",
                tool="tool_classify_event",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            cur_step += 1

            steps.append(ExecutionStep(
                step_number=cur_step,
                agent="JARVIS",
                capability=JarvisCapability.CLASSIFICATION.value,
                action="[PARALLEL] Extract TreeExplainer SHAP Local Waterfall Drivers",
                tool="tool_get_shap_drivers",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            cur_step += 1

            steps.append(ExecutionStep(
                step_number=cur_step,
                agent="JARVIS",
                capability=JarvisCapability.HISTORICAL_ANALYSIS.value,
                action="[PARALLEL] Compare Current Radiative Heat Output with Longitudinal Baseline",
                tool="tool_compare_baseline",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            cur_step += 1

            steps.append(ExecutionStep(
                step_number=cur_step,
                agent="JARVIS",
                capability=JarvisCapability.RISK_ANALYSIS.value,
                action="[PARALLEL] Compute 5-Factor Authoritative Operational Risk Score",
                tool="tool_calculate_risk",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            cur_step += 1

            steps.append(ExecutionStep(
                step_number=cur_step,
                agent="JARVIS",
                capability=JarvisCapability.THERMAL_INTELLIGENCE.value,
                action="[PARALLEL] Aggregate NASA FIRMS Multi-Sensor Observation Telemetry",
                tool="tool_get_satellite_observations",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            cur_step += 1

            steps.append(ExecutionStep(
                step_number=cur_step,
                agent="JARVIS",
                capability=JarvisCapability.SYSTEM_GOVERNANCE.value,
                action="Fuse Multimodal Evidence Package & Enforce HITL Verification Rules",
                tool="fuse_evidence",
                status=StepStatus.PENDING
            ))
            cur_step += 1

            if entities.get("require_dossier", False):
                steps.append(ExecutionStep(
                    step_number=cur_step,
                    agent="JARVIS",
                    capability=JarvisCapability.REPORTING.value,
                    action="Compile Formal Technical Dossier & Generate PDF Stream",
                    tool="tool_generate_investigation_dossier",
                    parameters={"event_ref": event_ref},
                    status=StepStatus.PENDING
                ))

        elif intent == CommandIntent.SUMMARIZE:
            # Evidence Synthesis Plan without Dossier
            steps.append(ExecutionStep(
                step_number=2,
                agent="JARVIS",
                capability=JarvisCapability.THERMAL_INTELLIGENCE.value,
                action="Retrieve Thermal Event Entity and Detections",
                tool="tool_get_event",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=3,
                agent="JARVIS",
                capability=JarvisCapability.GEOINT.value,
                action="[PARALLEL] Evaluate PostGIS Spatial Proximity and Buffer Boundaries",
                tool="tool_get_event_spatial_context",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=4,
                agent="JARVIS",
                capability=JarvisCapability.CLASSIFICATION.value,
                action="[PARALLEL] Execute XGBoost Multi-Class Inference & Balanced Platt Calibration",
                tool="tool_classify_event",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=5,
                agent="JARVIS",
                capability=JarvisCapability.CLASSIFICATION.value,
                action="[PARALLEL] Extract TreeExplainer SHAP Local Waterfall Drivers",
                tool="tool_get_shap_drivers",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=6,
                agent="JARVIS",
                capability=JarvisCapability.HISTORICAL_ANALYSIS.value,
                action="[PARALLEL] Compare Current Radiative Heat Output with Longitudinal Baseline",
                tool="tool_compare_baseline",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=7,
                agent="JARVIS",
                capability=JarvisCapability.RISK_ANALYSIS.value,
                action="[PARALLEL] Compute 5-Factor Authoritative Operational Risk Score",
                tool="tool_calculate_risk",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=8,
                agent="JARVIS",
                capability=JarvisCapability.THERMAL_INTELLIGENCE.value,
                action="[PARALLEL] Aggregate NASA FIRMS Multi-Sensor Observation Telemetry",
                tool="tool_get_satellite_observations",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=9,
                agent="JARVIS",
                capability=JarvisCapability.SYSTEM_GOVERNANCE.value,
                action="Fuse Multimodal Evidence Package & Enforce HITL Verification Rules",
                tool="fuse_evidence",
                status=StepStatus.PENDING
            ))

        else:
            # Full Comprehensive Investigation (INVESTIGATE / GENERAL)
            steps.append(ExecutionStep(
                step_number=2,
                agent="JARVIS",
                capability=JarvisCapability.THERMAL_INTELLIGENCE.value,
                action="Retrieve Thermal Event Entity and Detections",
                tool="tool_get_event",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=3,
                agent="JARVIS",
                capability=JarvisCapability.GEOINT.value,
                action="[PARALLEL] Evaluate PostGIS Spatial Proximity and Buffer Boundaries",
                tool="tool_get_event_spatial_context",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=4,
                agent="JARVIS",
                capability=JarvisCapability.CLASSIFICATION.value,
                action="[PARALLEL] Execute XGBoost Multi-Class Inference & Balanced Platt Calibration",
                tool="tool_classify_event",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=5,
                agent="JARVIS",
                capability=JarvisCapability.CLASSIFICATION.value,
                action="[PARALLEL] Extract TreeExplainer SHAP Local Waterfall Drivers",
                tool="tool_get_shap_drivers",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=6,
                agent="JARVIS",
                capability=JarvisCapability.HISTORICAL_ANALYSIS.value,
                action="[PARALLEL] Compare Current Radiative Heat Output with Longitudinal Baseline",
                tool="tool_compare_baseline",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=7,
                agent="JARVIS",
                capability=JarvisCapability.RISK_ANALYSIS.value,
                action="[PARALLEL] Compute 5-Factor Authoritative Operational Risk Score",
                tool="tool_calculate_risk",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=8,
                agent="JARVIS",
                capability=JarvisCapability.THERMAL_INTELLIGENCE.value,
                action="[PARALLEL] Aggregate NASA FIRMS Multi-Sensor Observation Telemetry",
                tool="tool_get_satellite_observations",
                parameters={"event_ref": event_ref},
                status=StepStatus.PENDING
            ))
            steps.append(ExecutionStep(
                step_number=9,
                agent="JARVIS",
                capability=JarvisCapability.SYSTEM_GOVERNANCE.value,
                action="Fuse Multimodal Evidence Package & Enforce HITL Verification Rules",
                tool="fuse_evidence",
                status=StepStatus.PENDING
            ))

            if entities.get("require_dossier", False):
                steps.append(ExecutionStep(
                    step_number=10,
                    agent="JARVIS",
                    capability=JarvisCapability.REPORTING.value,
                    action="Compile Formal Technical Dossier & Generate PDF Stream",
                    tool="tool_generate_investigation_dossier",
                    parameters={"event_ref": event_ref},
                    status=StepStatus.PENDING
                ))

        return steps


execution_planner = JarvisExecutionPlanner()
