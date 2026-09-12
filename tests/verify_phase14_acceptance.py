"""
AGNI-NETRA — JARVIS Phase 14 Acceptance Verification Script
Tests the 3 mandatory acceptance commands specified in Sections 23, 24, and 25:
1. Section 23: Primary Acceptance Command (Prepare for human verification + timeline + assessment history + unresolved requests + provenance + recommended next evidence)
2. Section 24: Assessment Comparison Command (Detailed delta comparison between versions)
3. Section 25: Case Closure Command (Write safety: proposal first, execution on human confirmation)
"""

import sys
import os
import time
import uuid

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.app.core.database import SessionLocal
from backend.app.models.jarvis_schemas import JarvisCommandRequest, StepStatus
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.services.jarvis.jarvis_workspace import workspace_manager
from backend.app.services.governance.case_management import case_management_engine


def run_phase14_acceptance_demonstration():
    db = SessionLocal()
    print("=" * 80)
    print("      AGNI-NETRA // JARVIS PHASE 14 CASE MANAGEMENT & GOVERNANCE ACCEPTANCE     ")
    print("=" * 80)

    try:
        session_id = f"demo-phase14-{uuid.uuid4().hex[:8]}"

        # Initialize workspace for EVT-827
        ws = workspace_manager.get_or_create_workspace(
            db=db,
            session_id=session_id,
            target_event_id="EVT-827",
            user_role="ANALYST",
            created_by="LEAD_ANALYST"
        )
        inv_id = ws.investigation_id
        print(f"\n[INIT] Active Investigation Case: {inv_id} for Event EVT-827")

        # Record Version 1 Assessment
        v1 = case_management_engine.record_assessment_version(
            db=db,
            case_id=inv_id,
            assessment_dict={
                "evidence_support_score": 82.5,
                "uncertainty_summary": {"level": "PARTIALLY_KNOWN"},
                "structured_statements": {
                    "ST-THERMAL": {"type": "THERMAL_CONFIRMATION", "confidence": 0.88},
                    "ST-CONTEXT": {"type": "REFINERY_PROXIMITY", "confidence": 0.94}
                }
            },
            created_by="ANALYST_ALICE",
            trigger="INITIAL_SYNTHESIS"
        )
        print(f"       Recorded Assessment v{v1.version_number} (Score: 82.5%, Hash: {v1.provenance['sha256'][:12]}...)")

        # Record Version 2 Assessment with added SAR radar evidence
        v2 = case_management_engine.record_assessment_version(
            db=db,
            case_id=inv_id,
            assessment_dict={
                "evidence_support_score": 91.0,
                "uncertainty_summary": {"level": "KNOWN"},
                "structured_statements": {
                    "ST-THERMAL": {"type": "THERMAL_CONFIRMATION", "confidence": 0.88},
                    "ST-CONTEXT": {"type": "REFINERY_PROXIMITY", "confidence": 0.94},
                    "ST-SAR": {"type": "SENTINEL1_RADAR_STRUCTURE", "confidence": 0.92}
                }
            },
            created_by="ANALYST_ALICE",
            trigger="SAR_DATA_ACQUISITION"
        )
        print(f"       Recorded Assessment v{v2.version_number} (Score: 91.0%, Hash: {v2.provenance['sha256'][:12]}...)")

        # Create an unresolved evidence request
        req = case_management_engine.create_evidence_request(
            db=db,
            case_id=inv_id,
            requested_source="OPTICAL_2M",
            reason="Verify flare stack perimeter containment via sub-2m resolution optical imagery.",
            uncertainty_target="Perimeter flare containment",
            priority="HIGH",
            requested_by="ANALYST_ALICE",
            actor_role="ANALYST"
        )
        print(f"       Created Evidence Request: {req.request_id} ({req.requested_source}, Priority: {req.priority})")

        # =========================================================================
        # SECTION 23: PRIMARY ACCEPTANCE COMMAND
        # =========================================================================
        print("\n" + "=" * 80)
        print("[SECTION 23] PRIMARY ACCEPTANCE COMMAND:")
        cmd23 = "JARVIS, prepare EVT-827 for human verification and show the complete case timeline, assessment history, unresolved evidence requests, latest assessment provenance, and recommended next evidence."
        print(f"Command: \"{cmd23}\"")
        t0 = time.time()
        res23 = master_orchestrator.execute_command(
            db,
            JarvisCommandRequest(command=cmd23, session_id=session_id),
            user_role="ANALYST"
        )
        dt23 = (time.time() - t0) * 1000.0
        print(f"Latency: {dt23:.1f} ms | Status: {res23.execution_trace.status}")
        assert res23.execution_trace.status == StepStatus.COMPLETED
        assert "CASE TIMELINE" in res23.summary
        assert "ASSESSMENT HISTORY" in res23.summary
        assert "UNRESOLVED EVIDENCE REQUESTS" in res23.summary
        assert "LATEST ASSESSMENT PROVENANCE" in res23.summary
        assert "RECOMMENDED NEXT EVIDENCE" in res23.summary
        print("\n--- Command Output (Excerpt) ---")
        print("\n".join(res23.summary.splitlines()[:25]))
        print("...\n[SECTION 23 VERIFIED: PASS]")

        # =========================================================================
        # SECTION 24: ASSESSMENT COMPARISON COMMAND
        # =========================================================================
        print("\n" + "=" * 80)
        print("[SECTION 24] ASSESSMENT COMPARISON COMMAND:")
        cmd24 = "JARVIS, show me exactly why the assessment changed between the previous and current versions."
        print(f"Command: \"{cmd24}\"")
        t0 = time.time()
        res24 = master_orchestrator.execute_command(
            db,
            JarvisCommandRequest(command=cmd24, session_id=session_id),
            user_role="ANALYST"
        )
        dt24 = (time.time() - t0) * 1000.0
        print(f"Latency: {dt24:.1f} ms | Status: {res24.execution_trace.status}")
        assert res24.execution_trace.status == StepStatus.COMPLETED
        assert "ASSESSMENT DELTA ANALYSIS" in res24.summary
        assert "Score Delta" in res24.summary or "Score Change" in res24.summary
        print("\n--- Command Output ---")
        print(res24.summary)
        print("[SECTION 24 VERIFIED: PASS]")

        # =========================================================================
        # SECTION 25: CASE CLOSURE COMMAND & WRITE SAFETY GUARD
        # =========================================================================
        print("\n" + "=" * 80)
        print("[SECTION 25] CASE CLOSURE COMMAND & WRITE SAFETY GUARD:")
        cmd25 = "JARVIS, close the investigation."
        print(f"Step 1: Autonomous / Unconfirmed Close Request: \"{cmd25}\"")
        res25_unconfirmed = master_orchestrator.execute_command(
            db,
            JarvisCommandRequest(command=cmd25, session_id=session_id),
            user_role="ANALYST"
        )
        print(f"Status: {res25_unconfirmed.execution_trace.status}")
        print(f"Summary: {res25_unconfirmed.summary}")
        assert "WRITE SAFETY ENFORCED" in res25_unconfirmed.summary
        assert "PROPOSED" in res25_unconfirmed.summary

        # Verify case was NOT closed in database
        ws_check = db.query(workspace_manager.get_workspace(db, inv_id)[0].__class__).filter_by(investigation_id=inv_id).first()
        print(f"Database Verification: Case state is still '{ws_check.status}' (NOT CLOSED).")
        assert ws_check.status != "CLOSED"

        print("\nStep 2: Explicit Human Confirmation Execution:")
        execution_result = case_management_engine.propose_or_execute_action(
            db=db,
            workspace=ws_check,
            action="CLOSE",
            actor_id="LEAD_ANALYST_HUMAN",
            actor_role="ANALYST",
            confirm_governed_action=True,
            is_autonomous_call=False,
            reason="Investigation concluded: permitted industrial flaring within CTO limits."
        )
        print(f"Result Status: {execution_result['status']}")
        print(f"New State:     {execution_result['new_state']}")
        print(f"Audit ID:      {execution_result['audit_id']}")
        assert execution_result["status"] == "EXECUTED"
        assert execution_result["new_state"] == "CLOSED"
        assert ws_check.status == "CLOSED"
        print("[SECTION 25 VERIFIED: PASS]")

        print("\n" + "=" * 80)
        print("      ALL PHASE 14 ACCEPTANCE VERIFICATIONS COMPLETED SUCCESSFULLY       ")
        print("=" * 80)
        return True

    finally:
        db.close()


if __name__ == "__main__":
    success = run_phase14_acceptance_demonstration()
    sys.exit(0 if success else 1)
