"""
AGNI-NETRA — Live Behavior Refinement Verification Script
Validates:
1. Primary Acceptance Test:
   "JARVIS, find the highest-risk thermal event near an industrial facility, investigate it, explain the major risk factors, compare it with its historical baseline, and generate an intelligence dossier."
2. Secondary Stateful Sequence:
   - "JARVIS, investigate Event 827."
   - "JARVIS, explain its risk."
   - "JARVIS, compare it with its historical baseline."
   - "JARVIS, show the strongest evidence for it."
   - "JARVIS, generate its intelligence dossier."
3. Targeted Regional Query:
   - "JARVIS, investigate the most critical thermal anomaly in Gujarat and tell me why it is high risk."
"""

import os
import sys
import uuid

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.models.jarvis_schemas import JarvisCommandRequest, JarvisState
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.services.jarvis.jarvis_memory import session_memory


def run_test_suite():
    print("=" * 80)
    print("AGNI-NETRA — JARVIS LIVE BEHAVIOR REFINEMENT VERIFICATION")
    print("=" * 80)

    db = SessionLocal()
    session_id = f"test-sess-{uuid.uuid4().hex[:8]}"

    try:
        # =========================================================================
        # 1. PRIMARY ACCEPTANCE TEST
        # =========================================================================
        print("\n--- [TEST 1] PRIMARY ACCEPTANCE COMMAND ---")
        cmd1 = (
            "JARVIS, find the highest-risk thermal event near an industrial facility, "
            "investigate it, explain the major risk factors, compare it with its historical baseline, "
            "and generate an intelligence dossier."
        )
        print(f"Command: '{cmd1}'")
        
        req1 = JarvisCommandRequest(command=cmd1, session_id=session_id)
        res1 = master_orchestrator.execute_command(db, req1, user_role="ANALYST")

        print(f"Status State: {res1.state.value}")
        print(f"Summary: {res1.summary}")
        print(f"Capabilities Used: {res1.capabilities_used}")
        print(f"Steps Executed: {len(res1.execution_trace.steps)}")

        for s in res1.execution_trace.steps:
            print(f"  Step {s.step_number}: [{s.capability}] {s.action} ({s.duration_ms}ms) -> {s.tool}")

        # Assertions
        assert res1.dispatch_gate_blocked is True, "Dispatch gate invariant violated!"
        assert all(s.agent == "JARVIS" for s in res1.execution_trace.steps), "Non-JARVIS agent detected!"
        assert any("[PARALLEL]" in s.action for s in res1.execution_trace.steps), "Parallel execution tag missing!"
        assert "pdf_export" in res1.details, "PDF dossier export missing for primary acceptance test!"
        assert res1.details["pdf_export"].get("pdf_size_bytes", 0) > 0, "Empty PDF file generated!"
        if res1.requires_human_approval:
            assert res1.summary.startswith("[HUMAN APPROVAL REQUIRED]"), "Missing [HUMAN APPROVAL REQUIRED] prefix!"
        print(">>> [TEST 1 PASSED]: Primary acceptance command succeeded with parallel execution, evidence fusion, and valid PDF dossier.")

        # =========================================================================
        # 2. SECONDARY STATEFUL SEQUENCE
        # =========================================================================
        print("\n--- [TEST 2.1] 'JARVIS, investigate Event 827.' ---")
        seq_session_id = f"seq-sess-{uuid.uuid4().hex[:8]}"
        req2_1 = JarvisCommandRequest(command="JARVIS, investigate Event 827.", session_id=seq_session_id)
        res2_1 = master_orchestrator.execute_command(db, req2_1, user_role="ANALYST")
        
        print(f"State: {res2_1.state.value}")
        print(f"Summary: {res2_1.summary[:120]}...")
        print(f"Steps: {len(res2_1.execution_trace.steps)}")
        assert "pdf_export" not in res2_1.details, "Dossier should NOT be generated when not requested!"
        assert res2_1.execution_trace.target_event in ["827", "EVT-827"], f"Unexpected target event: {res2_1.execution_trace.target_event}"
        print(">>> [TEST 2.1 PASSED]: Investigated Event 827 without unprompted dossier.")

        print("\n--- [TEST 2.2] 'JARVIS, explain its risk.' ---")
        req2_2 = JarvisCommandRequest(command="JARVIS, explain its risk.", session_id=seq_session_id)
        res2_2 = master_orchestrator.execute_command(db, req2_2, user_role="ANALYST")
        
        print(f"State: {res2_2.state.value}")
        print(f"Summary: {res2_2.summary[:120]}...")
        print(f"Steps: {len(res2_2.execution_trace.steps)}")
        for s in res2_2.execution_trace.steps:
            print(f"  Step {s.step_number}: {s.action} -> {s.tool}")
        # Stopping boundary check: only guardian + event + risk
        assert len(res2_2.execution_trace.steps) <= 3, f"Too many steps executed for explain risk: {len(res2_2.execution_trace.steps)}"
        assert "risk_decomposition" in res2_2.details, "Risk decomposition missing from details!"
        assert "pdf_export" not in res2_2.details, "PDF dossier generated unnecessarily!"
        print(">>> [TEST 2.2 PASSED]: Explained risk with strict surgical stopping boundary.")

        print("\n--- [TEST 2.3] 'JARVIS, compare it with its historical baseline.' ---")
        req2_3 = JarvisCommandRequest(command="JARVIS, compare it with its historical baseline.", session_id=seq_session_id)
        res2_3 = master_orchestrator.execute_command(db, req2_3, user_role="ANALYST")
        
        print(f"State: {res2_3.state.value}")
        print(f"Summary: {res2_3.summary[:120]}...")
        print(f"Steps: {len(res2_3.execution_trace.steps)}")
        for s in res2_3.execution_trace.steps:
            print(f"  Step {s.step_number}: {s.action} -> {s.tool}")
        assert len(res2_3.execution_trace.steps) <= 3, f"Too many steps executed for compare baseline: {len(res2_3.execution_trace.steps)}"
        assert "baseline_comparison" in res2_3.details, "Baseline comparison missing from details!"
        assert "pdf_export" not in res2_3.details, "PDF dossier generated unnecessarily!"
        print(">>> [TEST 2.3 PASSED]: Baseline compared with strict surgical stopping boundary.")

        print("\n--- [TEST 2.4] 'JARVIS, show the strongest evidence for it.' ---")
        req2_4 = JarvisCommandRequest(command="JARVIS, show the strongest evidence for it.", session_id=seq_session_id)
        res2_4 = master_orchestrator.execute_command(db, req2_4, user_role="ANALYST")
        
        print(f"State: {res2_4.state.value}")
        print(f"Summary: {res2_4.summary}")
        print(f"Steps: {len(res2_4.execution_trace.steps)}")
        assert any("[PARALLEL]" in s.action for s in res2_4.execution_trace.steps), "Parallel execution missing from evidence evaluation!"
        assert "pdf_export" not in res2_4.details, "Dossier PDF should NOT be generated for evidence summary!"
        assert "Strongest Multimodal Evidence" in res2_4.summary, "Summary missing evidence synthesis header!"
        print(">>> [TEST 2.4 PASSED]: Strongest evidence synthesized across dimensions without PDF generation.")

        print("\n--- [TEST 2.5] 'JARVIS, generate its intelligence dossier.' ---")
        req2_5 = JarvisCommandRequest(command="JARVIS, generate its intelligence dossier.", session_id=seq_session_id)
        res2_5 = master_orchestrator.execute_command(db, req2_5, user_role="ANALYST")
        
        print(f"State: {res2_5.state.value}")
        print(f"Summary: {res2_5.summary[:120]}...")
        print(f"PDF Size: {res2_5.details.get('pdf_export', {}).get('pdf_size_bytes', 0)} bytes")
        assert "pdf_export" in res2_5.details, "PDF export missing for dossier generation command!"
        assert res2_5.details["pdf_export"].get("pdf_size_bytes", 0) > 0, "PDF size is 0 bytes!"
        print(">>> [TEST 2.5 PASSED]: Intelligence dossier and PDF generated on explicit request.")

        # =========================================================================
        # 3. TARGETED DISCOVERY TEST
        # =========================================================================
        print("\n--- [TEST 3] TARGETED GUJARAT DISCOVERY ---")
        cmd3 = "JARVIS, investigate the most critical thermal anomaly in Gujarat and tell me why it is high risk."
        print(f"Command: '{cmd3}'")
        req3 = JarvisCommandRequest(command=cmd3, session_id=f"guj-sess-{uuid.uuid4().hex[:8]}")
        res3 = master_orchestrator.execute_command(db, req3, user_role="ANALYST")

        print(f"State: {res3.state.value}")
        print(f"Summary: {res3.summary}")
        print(f"Target Event: {res3.execution_trace.target_event}")
        print(f"Target Region: {res3.execution_trace.target_region}")
        print(f"Steps: {len(res3.execution_trace.steps)}")

        assert "pdf_export" not in res3.details, "Dossier should NOT be generated when not requested!"
        assert "Risk Factors Breakdown" in res3.summary or "Risk Score" in res3.summary, "Risk factors explanation missing!"
        if res3.requires_human_approval:
            assert res3.summary.startswith("[HUMAN APPROVAL REQUIRED]"), "Missing [HUMAN APPROVAL REQUIRED] prefix!"
        print(">>> [TEST 3 PASSED]: Targeted Gujarat discovery completed with risk factor explanation and no superfluous PDF.")

        print("\n" + "=" * 80)
        print("ALL LIVE BEHAVIOR REFINEMENT TESTS PASSED SUCCESSFULLY (ONE MASTER AGENT)!")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    run_test_suite()
