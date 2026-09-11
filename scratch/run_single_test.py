import sys
import traceback
sys.path.insert(0, r"E:\PROJECTS\AGNI-NETRA")
from backend.app.core.database import SessionLocal
from tests.test_jarvis_operational_intelligence import TestJarvisPhase5OperationalIntelligence

db = SessionLocal()
suite = TestJarvisPhase5OperationalIntelligence()

test_methods = [
    "test_section_20_complex_operational_acceptance_workflow",
    "test_analyst_prioritization_ranking",
    "test_priority_explanation",
    "test_multi_constraint_queries",
    "test_evidence_conflict_detection",
    "test_evidence_strength_distinct_from_risk",
    "test_epistemic_uncertainty_and_what_could_change",
    "test_operator_summary_on_demand",
    "test_safety_dispatch_gate_invariant"
]

for m_name in test_methods:
    print(f"\n========================================\nRUNNING {m_name}")
    try:
        getattr(suite, m_name)(db)
        print(f"PASSED: {m_name}")
    except Exception as e:
        print(f"FAILED: {m_name} -> {e}")
        traceback.print_exc()

db.close()
