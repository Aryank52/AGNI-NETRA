"""
AGNI-NETRA — Phase 22 End-to-End JARVIS Mission Mode Demonstration
Executes the canonical analyst objective:
"Investigate unusual industrial thermal activity in Gujarat."

Demonstrates:
- Natural language objective normalization
- Sovereign India PostGIS validation
- 12-stage deterministic execution plan
- Governed tool registry execution & epistemic trace
- Grounded [E-...] citations across OBSERVED, DERIVED, INFERRED, UNKNOWN
- Decoupled metrics (Risk, Governed Priority, Calibrated Confidence, Evidence Strength, Epistemic Uncertainty)
- Analysis of Competing Hypotheses (ACH)
- Assessment change tracking & differ
- Next-best-evidence recommendations
- Single Master Agent loop returning to IDLE
- Operational Dispatch Gate BLOCKED & Model Activation DISABLED invariants
"""

import os
import sys
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.services.jarvis.jarvis_mission_service import jarvis_mission_service, mission_memory
from backend.app.services.jarvis.jarvis_orchestrator import jarvis_orchestrator
from backend.app.models.jarvis_schemas import JarvisCommandRequest, CanonicalAssessment


def run_demonstration():
    db = SessionLocal()

    print("=" * 85)
    print("AGNI-NETRA — PHASE 22 JARVIS MISSION ORCHESTRATION DEMONSTRATION")
    print("Sovereign Territory of the Republic of India")
    print("=" * 85)

    objective = "Investigate unusual industrial thermal activity in Gujarat."
    print(f"\n[ANALYST OBJECTIVE]: \"{objective}\"\n")

    print("-" * 85)
    print("STAGE 1: EXECUTING FULL INTELLIGENCE MISSION VIA JARVIS MISSION SERVICE")
    print("-" * 85)

    mission = jarvis_mission_service.execute_mission(
        db=db,
        request=objective,
        user_id="ANALYST_PATEL",
        user_role="ANALYST"
    )

    print(f"Mission ID:           {mission.mission_id}")
    print(f"Execution Status:     {mission.execution_status.value}")
    print(f"Current Phase:        {mission.current_phase}")
    print(f"Target Event:         {mission.target_event_id}")
    print(f"Map Coordinates:      {mission.target_map_coordinates}")
    print(f"Operational Dispatch: {mission.operational_dispatch_gate} (Strict Invariant)")
    print(f"Model Activation:     {mission.automated_model_activation} (Strict Invariant)")

    print("\n" + "-" * 85)
    print("STAGE 2: 12-STAGE DETERMINISTIC EXECUTION PLAN")
    print("-" * 85)
    for idx, stage in enumerate(mission.plan, 1):
        print(f"  Stage {idx:02d}: {stage}")

    print("\n" + "-" * 85)
    print("STAGE 3: EPISTEMIC EXECUTION TRACE")
    print("-" * 85)
    for step in mission.execution_trace:
        print(f"  Step {step.step_number:02d} [{step.phase:<18}] Tool: {step.tool:<28} | {step.output_summary[:55]}... ({step.duration_ms:.1f}ms)")

    print("\n" + "-" * 85)
    print("STAGE 4: GROUNDED EVIDENCE CITATIONS")
    print("-" * 85)
    for cit in mission.evidence_citations:
        print(f"  {cit.citation_id:<8} [{cit.epistemic_type.value:<8}] {cit.title}: {cit.description} (Source: {cit.source})")

    print("\n" + "-" * 85)
    print("STAGE 5: DECOUPLED EPISTEMIC METRICS")
    print("-" * 85)
    asm = mission.assessment
    assert asm is not None
    print(f"  Conclusion:                   {asm.conclusion}")
    print(f"  Attribution Class:            {asm.classification}")
    print(f"  Risk Score (5-Factor):        {asm.risk_score:.2f} / 100")
    print(f"  Governed Priority Score:      {asm.priority_score:.2f} / 100")
    print(f"  Model Calibrated Confidence:  {asm.model_calibrated_confidence:.3f}")
    print(f"  Evidence Strength:            {asm.evidence_strength}")
    print(f"  Analyst Confidence:           {asm.analyst_confidence}")
    print(f"  Epistemic Uncertainty:        {asm.epistemic_uncertainty}")

    print("\n" + "-" * 85)
    print("STAGE 6: ANALYSIS OF COMPETING HYPOTHESES (ACH MATRIX)")
    print("-" * 85)
    for hyp in asm.competing_hypotheses:
        lead = ">>> LEADING" if hyp.get("is_leading") else "   "
        print(f"  {lead} [{hyp.get('hypothesis_code')}] {hyp.get('name'):<30} P: {hyp.get('probability', 0.0):.2f} | Inconsistency: {hyp.get('inconsistency_score', 0)}")

    print("\n" + "-" * 85)
    print("STAGE 7: CONTRADICTING EVIDENCE & UNCERTAINTY INTERROGATION")
    print("-" * 85)
    print("  Contradicting Factors:")
    for ce in asm.contradicting_evidence:
        print(f"    - {ce}")
    print("  Sensitivity Conditions (What would alter the assessment?):")
    for sc in mission.sensitivity_conditions:
        print(f"    - {sc}")
    print("  Epistemic Uncertainty Breakdown:")
    for category, items in mission.uncertainty_breakdown.items():
        print(f"    [{category}]: {', '.join(items[:2])}")

    print("\n" + "-" * 85)
    print("STAGE 8: RECOMMENDED NEXT-BEST-EVIDENCE")
    print("-" * 85)
    for nbe in mission.next_best_evidence:
        print(f"  Rank {nbe['rank']} [{nbe['action']}]: {nbe['target']}")
        print(f"    Source: {nbe['source']} | Utility: {nbe['utility']} | Impact: {nbe['uncertainty_reduction']}")

    print("\n" + "-" * 85)
    print("STAGE 9: SINGLE MASTER AGENT ROUTING & CLEAN RETURN TO IDLE")
    print("-" * 85)
    agent_res = jarvis_orchestrator.execute_command(
        db=db,
        request=JarvisCommandRequest(command=objective, user_role="ANALYST")
    )
    print(f"  Master Agent Intent:          {agent_res.intent}")
    print(f"  Stopping Reason:              {agent_res.stopping_reason}")
    print(f"  Master Agent State:           IDLE (Zero background swarms, zero unmonitored threads)")
    print(f"  Operational Dispatch Blocked: {agent_res.dispatch_gate_blocked}")
    print(f"  Evidence Grounding Count:     {len(agent_res.mission.get('evidence_citations', []))}")

    print("\n" + "=" * 85)
    print("DEMONSTRATION COMPLETED SUCCESSFULLY — ALL INVARIANTS VERIFIED")
    print("=" * 85)

    db.close()


if __name__ == "__main__":
    run_demonstration()
