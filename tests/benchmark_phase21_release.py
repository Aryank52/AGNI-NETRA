"""
AGNI-NETRA — Phase 21 Product Release & Performance Regression Benchmark
Measures P50, P95, P99, Mean, and Max latencies across all 10 core operational capabilities:
1. API Health & Diagnostics
2. Operational Event Retrieval
3. Analyst Triage Queue Retrieval
4. Governed Priority Explanation Breakdown
5. Standardized 7-Dimension Event Dossier
6. Competing Hypotheses Evaluation (ACH)
7. Evidence Review Workspace
8. Investigation Workspace Loading
9. Operational Intelligence Report Generation
10. JARVIS Master Agent Command Execution
"""

import time
import statistics
import os
import sys
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.models.domain import ThermalEvent, InvestigationWorkspace
from backend.app.services.analyst.analyst_workflow_service import analyst_workflow_service
from backend.app.services.jarvis.jarvis_orchestrator import jarvis_orchestrator
from backend.app.services.intelligence.india_intelligence_service import india_intelligence_service
from backend.app.models.jarvis_schemas import JarvisCommandRequest


def percentile(data: List[float], p: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    idx = int(len(sorted_data) * p)
    return sorted_data[min(idx, len(sorted_data) - 1)]


def run_benchmark():
    db = SessionLocal()
    print("=" * 80)
    print("AGNI-NETRA PHASE 21 RELEASE HARDENING PERFORMANCE BENCHMARK")
    print("Sovereign Territory of India Scope")
    print("=" * 80)

    # Pick representative event
    ev = db.query(ThermalEvent).filter(ThermalEvent.country == "India").first()
    if not ev:
        ev = db.query(ThermalEvent).first()
    assert ev is not None, "Thermal event required for benchmark."
    event_id = ev.id

    ws = db.query(InvestigationWorkspace).first()
    case_id = ws.investigation_id if ws else "INV-BENCHMARK-01"

    benchmarks = {}

    def measure(name: str, fn, iterations: int = 10):
        latencies = []
        # Warmup
        try:
            fn()
        except Exception as e:
            print(f"Warmup error for {name}: {e}")

        for _ in range(iterations):
            t0 = time.perf_counter()
            fn()
            latencies.append((time.perf_counter() - t0) * 1000.0)

        mean_val = statistics.mean(latencies)
        p50 = statistics.median(latencies)
        p95 = percentile(latencies, 0.95)
        p99 = percentile(latencies, 0.99)
        max_val = max(latencies)

        benchmarks[name] = {
            "mean": round(mean_val, 2),
            "p50": round(p50, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2),
            "max": round(max_val, 2),
            "iterations": iterations,
        }
        print(f"[{name:<40}] P50: {p50:6.2f}ms | P95: {p95:6.2f}ms | P99: {p99:6.2f}ms | Mean: {mean_val:6.2f}ms")

    # 1. API Health / DB Connection
    measure("1. Database Connection & Health", lambda: db.execute(text("SELECT 1")).scalar(), 15)

    # 2. Event Retrieval
    measure("2. Operational Event Retrieval", lambda: db.query(ThermalEvent).filter(ThermalEvent.country == "India").limit(25).all(), 15)

    # 3. Analyst Triage Queue
    measure("3. Triage Queue Retrieval", lambda: analyst_workflow_service.get_triage_queue(db, limit=25), 10)

    # 4. Priority Explanation
    measure("4. Priority Explanation Breakdown", lambda: analyst_workflow_service.explain_triage_priority(db, event_id), 10)

    # 5. Event Dossier Loading
    measure("5. Standardized Event Dossier", lambda: analyst_workflow_service.get_standardized_event_dossier(db, event_id), 10)

    # 6. Competing Hypotheses (ACH)
    measure("6. Competing Hypotheses (ACH)", lambda: analyst_workflow_service.get_competing_hypotheses_review(db, event_id), 10)

    # Resolve or create benchmark investigation workspace
    ws = db.query(InvestigationWorkspace).filter(InvestigationWorkspace.target_event_id == event_id).first()
    if not ws:
        ws = db.query(InvestigationWorkspace).first()
    if not ws:
        ws = InvestigationWorkspace(
            investigation_id=f"INV-BENCH-{int(time.time())}",
            session_id="bench-session",
            target_event_id=event_id,
            user_role="ANALYST",
            status="ACTIVE",
            verification_status="REQUIRES_HUMAN_REVIEW",
            created_by="BENCHMARK",
            structured_evidence=[
                {"evidence_id": "EV-1", "title": "Satellite Telemetry", "source": "NASA_FIRMS", "type": "SATELLITE_TELEMETRY"}
            ]
        )
        db.add(ws)
        db.commit()
        db.refresh(ws)
    ws_id = ws.investigation_id

    # 7. Evidence Review Workspace
    measure("7. Evidence Review Workspace", lambda: analyst_workflow_service.get_evidence_review_workspace(db, ws_id), 10)

    # 8. Investigation Workspace Loading
    measure("8. Investigation Workspace State", lambda: analyst_workflow_service.get_investigation_workflow_state(db, ws_id), 10)

    # 9. Operational Report Generation
    measure("9. 17-Section Report Generation", lambda: analyst_workflow_service.generate_operational_analyst_report(db, event_id, analyst_id="BENCHMARK"), 5)

    # 10. JARVIS Command Execution
    req = JarvisCommandRequest(command="JARVIS, why was this event prioritized?")
    measure("10. JARVIS Command Execution", lambda: jarvis_orchestrator.execute_command(req, db=db), 5)

    print("=" * 80)
    print("BENCHMARK SUMMARY RESULTS TABLE")
    print("=" * 80)
    print(f"{'Capability':<38} | {'P50 (ms)':<9} | {'P95 (ms)':<9} | {'P99 (ms)':<9} | {'Mean (ms)':<9} | {'Max (ms)':<9}")
    print("-" * 95)
    for k, v in benchmarks.items():
        print(f"{k:<38} | {v['p50']:<9.2f} | {v['p95']:<9.2f} | {v['p99']:<9.9} | {v['mean']:<9.2f} | {v['max']:<9.2f}")
    print("=" * 80)

    db.close()
    return benchmarks


if __name__ == "__main__":
    from sqlalchemy import text
    run_benchmark()
