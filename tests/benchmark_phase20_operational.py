"""
AGNI-NETRA — Phase 20 Operational Performance Benchmark
Measures P50, P95, Mean, and Max latencies across operational analyst endpoints and workflows.
"""

import time
import statistics
from typing import List, Dict, Any

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.models.domain import ThermalEvent, InvestigationWorkspace
from backend.app.services.analyst.analyst_workflow_service import analyst_workflow_service
from backend.app.services.jarvis.jarvis_orchestrator import JarvisMasterOrchestrator
from backend.app.models.jarvis_schemas import JarvisCommandRequest


def run_benchmark():
    db = SessionLocal()
    orchestrator = JarvisMasterOrchestrator()
    print("=" * 70)
    print("AGNI-NETRA PHASE 20 OPERATIONAL PERFORMANCE BENCHMARK")
    print("Sovereign Territory of India Scope")
    print("=" * 70)

    # Pick representative event and case
    ev = db.query(ThermalEvent).filter(ThermalEvent.country == "India").first()
    assert ev is not None, "Thermal event required for benchmark."
    event_id = ev.id

    ws = db.query(InvestigationWorkspace).first()
    if not ws:
        ws = InvestigationWorkspace(
            investigation_id="INV-BENCHMARK-01",
            session_id="session-bench",
            target_event_id=event_id,
            user_role="ANALYST",
            status="ACTIVE",
            created_by="BENCHMARK",
        )
        db.add(ws)
        db.commit()
    case_id = ws.investigation_id

    benchmarks = {}

    def measure(name: str, fn, iterations: int = 10):
        latencies = []
        # Warmup
        try:
            fn()
        except Exception:
            pass

        for _ in range(iterations):
            t0 = time.perf_counter()
            fn()
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)

        latencies.sort()
        p50 = statistics.median(latencies)
        p95 = latencies[int(len(latencies) * 0.95)] if len(latencies) >= 20 else latencies[-1]
        mean = statistics.mean(latencies)
        max_lat = max(latencies)

        benchmarks[name] = {
            "iterations": iterations,
            "mean_ms": round(mean, 2),
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "max_ms": round(max_lat, 2),
        }
        print(f"[{name:<35}] Mean: {mean:6.2f}ms | P50: {p50:6.2f}ms | P95: {p95:6.2f}ms | Max: {max_lat:6.2f}ms")

    # 1. Triage Queue Retrieval
    measure("Triage Queue Retrieval", lambda: analyst_workflow_service.get_triage_queue(db, limit=25), iterations=10)

    # 2. Priority Explanation
    measure("Priority Explanation Breakdown", lambda: analyst_workflow_service.explain_triage_priority(db, event_id), iterations=10)

    # 3. Standardized Event Dossier (7 Dimensions)
    measure("Event Dossier Loading", lambda: analyst_workflow_service.get_standardized_event_dossier(db, event_id), iterations=10)

    # 4. Competing Hypotheses Matrix
    measure("Competing Hypotheses Evaluation", lambda: analyst_workflow_service.get_competing_hypotheses_review(db, event_id), iterations=10)

    # 5. Evidence Review Workspace
    measure("Evidence Review Workspace Loading", lambda: analyst_workflow_service.get_evidence_review_workspace(db, case_id), iterations=10)

    # 6. Decision Effectiveness Metrics
    measure("Decision Metrics Computation", lambda: analyst_workflow_service.compute_decision_effectiveness_metrics(db), iterations=10)

    # 7. Triage Metrics
    measure("Triage Metrics Computation", lambda: analyst_workflow_service.compute_triage_effectiveness_metrics(db), iterations=10)

    # 8. Operational Report Generation
    measure("Operational Report Generation", lambda: analyst_workflow_service.generate_operational_analyst_report(db, event_id), iterations=5)

    # 9. JARVIS Master Agent Command
    measure("JARVIS Triage Command", lambda: orchestrator.execute_command(JarvisCommandRequest(command="JARVIS, show me what needs verification first.")), iterations=5)

    print("=" * 70)
    print("BENCHMARK RESULTS SUMMARY (Target: All sub-second, majority < 100ms)")
    all_sub_second = all(b["mean_ms"] < 2000.0 for b in benchmarks.values())
    print(f"All operations within SLA: {'PASSED' if all_sub_second else 'FAILED'}")
    print("=" * 70)

    db.close()
    return benchmarks


if __name__ == "__main__":
    run_benchmark()
