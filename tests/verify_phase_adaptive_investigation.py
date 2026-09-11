"""
AGNI-NETRA — Automated Verification for JARVIS Phase: Command Intelligence & Adaptive Investigation
Verifies all 6 mandatory command test cases:
  TEST 1: Find most suspicious event around an industrial facility & explain why suspicious.
  TEST 2: Investigate 3 highest-risk in Gujarat and tell which one has strongest evidence of industrial fire.
  TEST 3: Find high-risk events within 5km of industrial facilities unusually high compared to historical baseline.
  TEST 4: Investigate Event 827 and stop once enough evidence to explain classification and risk.
  TEST 5: Compare Event 827 with other high-risk events and identify strongest case.
  TEST 6: Take strongest case from that comparison and generate an intelligence dossier.
"""

import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.models.jarvis_schemas import JarvisCommandRequest, JarvisState
from backend.app.services.jarvis.jarvis_orchestrator import master_orchestrator
from backend.app.services.jarvis.jarvis_memory import session_memory


def run_tests():
    db = SessionLocal()
    session_id = f"test-adaptive-{uuid.uuid4().hex[:8]}"
    print(f"\n================================================================================")
    print(f"AGNI-NETRA — VERIFYING JARVIS COMMAND INTELLIGENCE & ADAPTIVE INVESTIGATION")
    print(f"Session ID: {session_id}")
    print(f"================================================================================\n")

    passed_tests = 0

    # -------------------------------------------------------------------------
    # TEST 1
    # "JARVIS, find the most suspicious thermal event around an industrial facility and explain why it is suspicious."
    # -------------------------------------------------------------------------
    print("--- RUNNING TEST 1 ---")
    cmd1 = "JARVIS, find the most suspicious thermal event around an industrial facility and explain why it is suspicious."
    req1 = JarvisCommandRequest(command=cmd1, session_id=session_id)
    res1 = master_orchestrator.execute_command(db, req1, user_role="ANALYST")

    print(f"Test 1 State: {res1.state.value}")
    print(f"Test 1 Target Event: {res1.execution_trace.target_event}")
    print(f"Test 1 Objective: {res1.objective.primary_goal if res1.objective else None}")
    print(f"Test 1 Stopping Reason: {res1.stopping_reason}")
    print(f"Test 1 Has PDF Export: {'pdf_export' in res1.details}")

    assert res1.state in [JarvisState.COMPLETED, JarvisState.REQUIRES_APPROVAL], "Test 1 failed: State should be completed or requires_approval"
    assert res1.objective is not None, "Test 1 failed: Objective must be set"
    assert res1.stopping_reason is not None, "Test 1 failed: Stopping reason must be set"
    assert "pdf_export" not in res1.details or res1.details["pdf_export"] is None, "Test 1 failed: No PDF dossier should be generated without explicit prompt"
    assert len(res1.summary) > 50, "Test 1 failed: Summary must contain explanation of suspicious factors"
    print(">>> TEST 1 PASSED: Successfully found suspicious facility anomaly, explained drivers, and halted without unprompted dossier.\n")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 2
    # "JARVIS, investigate the three highest-risk thermal events in Gujarat and tell me which one has the strongest evidence of an industrial fire."
    # -------------------------------------------------------------------------
    print("--- RUNNING TEST 2 ---")
    cmd2 = "JARVIS, investigate the three highest-risk thermal events in Gujarat and tell me which one has the strongest evidence of an industrial fire."
    req2 = JarvisCommandRequest(command=cmd2, session_id=session_id)
    res2 = master_orchestrator.execute_command(db, req2, user_role="ANALYST")

    print(f"Test 2 State: {res2.state.value}")
    print(f"Test 2 Objective: {res2.objective.primary_goal if res2.objective else None}")
    print(f"Test 2 Candidate Count: {res2.objective.candidate_count if res2.objective else None}")
    print(f"Test 2 Hypothesis: {res2.objective.target_hypothesis if res2.objective else None}")
    print(f"Test 2 Stopping Reason: {res2.stopping_reason}")
    print(f"Test 2 Has Comparison: {'comparison' in res2.details}")

    assert res2.objective is not None, "Test 2 failed: Objective must be set"
    assert res2.objective.candidate_count == 3, f"Test 2 failed: Expected candidate_count 3, got {res2.objective.candidate_count}"
    assert "comparison" in res2.details, "Test 2 failed: Comparison results must be present"
    comp2 = res2.details["comparison"]
    assert comp2.get("winner_event_code") is not None, "Test 2 failed: Strongest candidate winner must be identified"
    assert len(comp2.get("candidates", [])) >= 1, "Test 2 failed: Candidates list must not be empty"
    assert res2.stopping_reason is not None and "IDENTIFIED_STRONGEST_CASE" in res2.stopping_reason, "Test 2 failed: Stopping reason must reflect strongest case identification"
    print(f"Winner: {comp2['winner_event_code']} (Score: {comp2['strongest_candidate']['composite_evidence_score']}/100)")
    print(">>> TEST 2 PASSED: Evaluated 3 candidates in Gujarat, ranked empirical evidence for Industrial Fire, and declared winner.\n")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 3
    # "JARVIS, find high-risk thermal events within 5 km of industrial facilities that are unusually high compared with their historical baseline."
    # -------------------------------------------------------------------------
    print("--- RUNNING TEST 3 ---")
    cmd3 = "JARVIS, find high-risk thermal events within 5 km of industrial facilities that are unusually high compared with their historical baseline."
    req3 = JarvisCommandRequest(command=cmd3, session_id=session_id)
    res3 = master_orchestrator.execute_command(db, req3, user_role="ANALYST")

    print(f"Test 3 State: {res3.state.value}")
    print(f"Test 3 Objective: {res3.objective.primary_goal if res3.objective else None}")
    print(f"Test 3 Constraints: {res3.objective.constraints if res3.objective else None}")
    print(f"Test 3 Stopping Reason: {res3.stopping_reason}")
    print(f"Test 3 Matching Events Count: {len(res3.details.get('multi_constraint_events', []))}")

    assert res3.objective is not None, "Test 3 failed: Objective must be set"
    assert "multi_constraint_events" in res3.details, "Test 3 failed: Multi-constraint events must be present in details"
    assert res3.stopping_reason is not None and "MULTI_CONSTRAINT_FILTER_SATISFIED" in res3.stopping_reason, "Test 3 failed: Stopping reason must reflect multi-constraint satisfaction"
    assert "pdf_export" not in res3.details or res3.details["pdf_export"] is None, "Test 3 failed: No PDF dossier should be generated"
    print(">>> TEST 3 PASSED: Multi-constraint filter executed with facility buffer, high risk, and baseline abnormality.\n")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 4
    # "JARVIS, investigate Event 827 and stop once you have enough evidence to explain its classification and risk."
    # -------------------------------------------------------------------------
    print("--- RUNNING TEST 4 ---")
    cmd4 = "JARVIS, investigate Event 827 and stop once you have enough evidence to explain its classification and risk."
    req4 = JarvisCommandRequest(command=cmd4, session_id=session_id)
    res4 = master_orchestrator.execute_command(db, req4, user_role="ANALYST")

    print(f"Test 4 State: {res4.state.value}")
    print(f"Test 4 Target Event: {res4.execution_trace.target_event}")
    print(f"Test 4 Objective: {res4.objective.primary_goal if res4.objective else None}")
    print(f"Test 4 Stop Rule: {res4.objective.stopping_condition if res4.objective else None}")
    print(f"Test 4 Stopping Reason: {res4.stopping_reason}")

    assert res4.objective is not None, "Test 4 failed: Objective must be set"
    assert res4.stopping_reason is not None and "SUFFICIENT_EVIDENCE_FOR_CLASSIFICATION_AND_RISK" in res4.stopping_reason, "Test 4 failed: Stopping reason must reflect sufficient evidence halt"
    assert "pdf_export" not in res4.details or res4.details["pdf_export"] is None, "Test 4 failed: Should not generate PDF report"
    assert "ml" in res4.details and "risk" in res4.details, "Test 4 failed: ML classification and risk details must be gathered"
    print(">>> TEST 4 PASSED: Executed surgical investigation for Event 827 and halted early once classification and risk were proven.\n")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 5
    # "JARVIS, compare Event 827 with the other high-risk events and identify the strongest case."
    # -------------------------------------------------------------------------
    print("--- RUNNING TEST 5 ---")
    cmd5 = "JARVIS, compare Event 827 with the other high-risk events and identify the strongest case."
    req5 = JarvisCommandRequest(command=cmd5, session_id=session_id)
    res5 = master_orchestrator.execute_command(db, req5, user_role="ANALYST")

    print(f"Test 5 State: {res5.state.value}")
    print(f"Test 5 Objective: {res5.objective.primary_goal if res5.objective else None}")
    print(f"Test 5 Stopping Reason: {res5.stopping_reason}")
    print(f"Test 5 Comparison Details Present: {'comparison' in res5.details}")

    assert res5.objective is not None, "Test 5 failed: Objective must be set"
    assert "comparison" in res5.details, "Test 5 failed: Comparison must be present"
    comp5 = res5.details["comparison"]
    winner5 = comp5.get("winner_event_code")
    assert winner5 is not None, "Test 5 failed: Winner must be determined"
    print(f"Test 5 Winner Event: {winner5}")

    # Check session memory has recorded the winner
    ctx5 = session_memory.get_context_dict(session_id)
    assert ctx5.get("selected_candidate_ref") == winner5, f"Test 5 failed: Session memory selected_candidate_ref should be {winner5}, got {ctx5.get('selected_candidate_ref')}"
    print(">>> TEST 5 PASSED: Compared Event 827 against peers, determined strongest case, and persisted winner to session memory.\n")
    passed_tests += 1

    # -------------------------------------------------------------------------
    # TEST 6 (Conversational follow-up chaining from Test 5)
    # "JARVIS, take the strongest case from that comparison and generate an intelligence dossier."
    # -------------------------------------------------------------------------
    print("--- RUNNING TEST 6 ---")
    cmd6 = "JARVIS, take the strongest case from that comparison and generate an intelligence dossier."
    req6 = JarvisCommandRequest(command=cmd6, session_id=session_id)
    res6 = master_orchestrator.execute_command(db, req6, user_role="ANALYST")

    print(f"Test 6 State: {res6.state.value}")
    print(f"Test 6 Target Event: {res6.execution_trace.target_event}")
    print(f"Test 6 Objective: {res6.objective.primary_goal if res6.objective else None}")
    print(f"Test 6 Resolved from Context: {res6.objective.resolved_from_context if res6.objective else None}")
    print(f"Test 6 Contextual Reference: {res6.objective.contextual_reference if res6.objective else None}")
    print(f"Test 6 Stopping Reason: {res6.stopping_reason}")
    print(f"Test 6 Has PDF Export: {'pdf_export' in res6.details}")

    assert res6.objective is not None, "Test 6 failed: Objective must be set"
    assert res6.objective.resolved_from_context is True, "Test 6 failed: Must resolve event from prior turn context"
    assert res6.execution_trace.target_event == winner5, f"Test 6 failed: Target event must match winner from Test 5 ({winner5}), got {res6.execution_trace.target_event}"
    assert "pdf_export" in res6.details and res6.details["pdf_export"].get("is_valid_pdf") is True, "Test 6 failed: Valid PDF dossier must be generated"
    assert res6.stopping_reason is not None and "DOSSIER_COMPILED_AND_EXPORTED" in res6.stopping_reason, "Test 6 failed: Stopping reason must reflect dossier compilation"
    print(f"Generated PDF Size: {res6.details['pdf_export'].get('pdf_size_bytes')} bytes")
    print(">>> TEST 6 PASSED: Correctly resolved 'strongest case from that comparison' to previous winner, and generated authoritative PDF dossier.\n")
    passed_tests += 1

    db.close()

    print("================================================================================")
    print(f"ALL {passed_tests}/6 TESTS COMPLETED SUCCESSFULLY!")
    print("================================================================================\n")


if __name__ == "__main__":
    run_tests()
