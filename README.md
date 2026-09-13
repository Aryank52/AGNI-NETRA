# AGNI-NETRA (अग्नि-नेत्र)
### Sovereign India AI Thermal Intelligence & Operational Decision Support Platform
**Version**: `1.0.0-RC1` | **Scope**: Sovereign Territory of India | **Classification**: Governed Multi-Source Operational Intelligence

---

> **Operational Mission**:
> Transforming raw spaceborne thermal observations into explainable, legally defensible, and high-fidelity operational decision support for the Sovereign Territory of India.
> 
> *&ldquo;FIRMS indicates where thermal energy is detected. **AGNI-NETRA** determines what sovereign facility or process it is spatially associated with, whether it represents abnormal activity or routine operations, how risky it is under frozen governance formulas, and what verifiable evidence must be evaluated by a human analyst.&rdquo;*

---

## 🏛️ Core Architectural Foundations & Safety Guarantees

1. **Sovereign India Scope Boundary Filtering**:
   - Strictly bounded by official Survey of India / Local Government Directory (LGD) administrative boundaries.
   - Enforces 7,595 PostGIS (SRID 4326) polygons across 36 States/UTs, 735 Districts, and 6,824 Subdistricts (Tehsils).
   - Foreign coordinates (e.g. Sri Lanka, Pakistan, maritime outside EEZ) are automatically quarantined or excluded.

2. **Master Agent JARVIS (Single Master Agent Architecture)**:
   - Single authoritative natural-language command agent (`JARVIS`).
   - Zero independent autonomous subagents, zero background agent swarms.
   - Strictly conversational, read-only analytical reasoning, deterministic state transitions (`IDLE` ➔ `PROCESSING` ➔ `COMPLETED` ➔ `IDLE`).

3. **Governed Operational Dispatch Safety Gate (`BLOCKED`)**:
   - `ENABLE_OPERATIONAL_DISPATCH_GATE = False` (hard invariant).
   - No automated emergency dispatches, siren triggers, or live agency alerts can be emitted without human review.

4. **Automated Model Activation Disabled (`DISABLED`)**:
   - `ENABLE_AUTOMATED_MODEL_ACTIVATION = False` (hard invariant).
   - ML model artifacts, weights, and calibrators are frozen. Automated online retraining and silent activation are forbidden.

5. **Strict Metric Decoupling**:
   - **Risk Score** (0–100 threat magnitude) ≠ **Calibrated Confidence** (0.0–1.0 ML attribution certainty) ≠ **Evidence Strength** (empirical coverage) ≠ **Analyst Confidence** (human judgment) ≠ **Epistemic Uncertainty** (knowledge gaps).

6. **Frozen Mathematical Formulas**:
   - **5-Factor Operational Risk Formula**:
     $$\text{Risk} = 0.30 \times I_{\text{Intensity}} + 0.25 \times A_{\text{Abnormality}} + 0.20 \times E_{\text{Exposure}} + 0.15 \times P_{\text{Persistence}} + 0.10 \times C_{\text{Context}}$$
   - **Governed Priority Formula**:
     $$\text{Priority} = 0.40 \times \text{RiskScore} + 0.20 \times \text{CalibratedConfidence} + 0.30 \times \text{TierWeight} + 0.10 \times \text{RecencyScore}$$

7. **Truthful Provider Disclosure (Zero Synthetic Feeds)**:
   - Live real streams active for NASA FIRMS VIIRS (375m) and PostGIS master cadastral datasets.
   - Unconfigured international feeds (Copernicus CAMS, ECMWF ERA5, NOAA GFS, Sentinel-1/2, Planet) are truthfully reported as `NOT_CONFIGURED`. Zero synthetic data is substituted.

---

## 🚀 Quick Start & Development Setup

### System Prerequisites
- **Operating System**: Windows 11 / Linux (Ubuntu 22.04+)
- **Python**: 3.12+ (Virtual environment in `.venv`)
- **Node.js**: 20+ & npm 10+
- **PostgreSQL**: 16 with PostGIS 3.4+ extension installed

### 1. Database & Services Initial Setup
Ensure PostgreSQL 16 is running on `127.0.0.1:5432` with database `agni_netra_db`.
```powershell
# Set environment
$env:PYTHONPATH="."

# Run database verification & readiness audit
.venv\Scripts\python.exe database\audit_phase_6a_readiness.py
```

### 2. Backend Application (FastAPI)
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Launch FastAPI ASGI daemon on port 8000
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health & Readiness Endpoint**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 3. Frontend Web Application (Next.js 15)
```powershell
cd frontend
npm run dev
```
- **Operational Command Center**: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
- **Analyst Verification Queue**: [http://localhost:3000/dashboard/verification](http://localhost:3000/dashboard/verification)
- **Master Agent JARVIS Terminal**: [http://localhost:3000/jarvis](http://localhost:3000/jarvis)
- **National Intelligence & Analytics**: [http://localhost:3000/dashboard/analytics](http://localhost:3000/dashboard/analytics)

---

## 🧪 Verification & Benchmark Commands

Execute the test suites and performance regression benchmarks directly:

```powershell
# 1. Phase 21 Full Release Readiness Suite (23 Test Groups, 100% Passing)
$env:PYTHONPATH="."; .venv\Scripts\python.exe -m pytest tests/test_phase21_release_readiness.py -v

# 2. Performance Regression Benchmark (P50, P95, P99 across 10 capabilities)
$env:PYTHONPATH="."; .venv\Scripts\python.exe tests/benchmark_phase21_release.py

# 3. 14-Stage End-to-End India Operational Walkthrough
$env:PYTHONPATH="."; .venv\Scripts\python.exe tests/demonstration_phase21_e2e.py

# 4. Full Monorepo Regression Suite (198 Tests across all phases)
$env:PYTHONPATH="."; .venv\Scripts\python.exe -m pytest tests/test_phase*.py -q
```

---

## 👥 Role-Based Access Control (RBAC) Matrix

| Role | Permitted Access | Restricted Actions |
|---|---|---|
| **ANALYST** | Triage queue, case management, ACH hypotheses, dossier, evidence review, report generation | Direct model retraining, dispatch gate modification |
| **AGENCY** | Priority incidents, incident corridor briefings, agency dispatch review | Public dataset modification, raw database access |
| **RESEARCHER** | Longitudinal 6-year thermal baselines, LULC correlation, cross-sensor comparisons | Operational case verification, dispatch gate access |
| **INDUSTRY** | Own-facility baselines, flaring permits, compliance dossiers | Other facilities' telemetry, sovereign queue triage |
| **ADMIN** | System health, audit logs, configuration governance, user management | Autonomous alert emission (dispatch gate remains blocked) |
| **PUBLIC** | Sanitized, aggregated regional advisories (coarse coordinates, zero facility IDs) | All case workspaces, raw sensor telemetry, SHAP attributions |

---

## 📚 Key Reference Documentation

- [Technical Architecture Specification](file:///e:/PROJECTS/AGNI-NETRA/ARCHITECTURE.md)
- [Operations & Runbook Guide](file:///e:/PROJECTS/AGNI-NETRA/OPERATIONS_RUNBOOK.md)
- [Stakeholder Demonstration Script](file:///e:/PROJECTS/AGNI-NETRA/DEMO_GUIDE.md)
- [Phase 21 Comprehensive Release Report](file:///e:/PROJECTS/AGNI-NETRA/PHASE_21_REPORT.md)
