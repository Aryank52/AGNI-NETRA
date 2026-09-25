# AGNI-NETRA

India-first geospatial thermal intelligence and decision-support platform.

---

## 1. Overview

**AGNI-NETRA** is an industrial-grade geospatial thermal intelligence and operational decision-support platform purpose-built for the Sovereign Territory of India. The platform ingests spaceborne multi-sensor radiometric observations, filters and validates telemetry against official sovereign administrative boundaries, performs spatiotemporal clustering and contextual fusion with cadastral infrastructure registries, and executes explainable machine learning inference to deliver defensible incident intelligence.

Rather than treating thermal hotspots merely as raw coordinate dots on a generic map, AGNI-NETRA contextualizes thermal phenomena against India's industrial plants, power infrastructure, mineral concessions, and forest boundaries—providing human analysts with transparent, reproducible, and legally defensible intelligence dossiers.

---

## 2. Problem

Thermal monitoring in industrial and environmental sectors across India presents critical operational challenges:

1. **Information Overload Without Context**: Satellite fire feeds (e.g., NASA FIRMS) detect thousands of thermal anomalies daily across the subcontinent, but cannot distinguish between routine industrial flaring, uncontrolled refinery fires, crop residue burning, or forest wildfires.
2. **Lack of Cadastral & Sovereign Grounding**: Standard global satellite pipelines lack alignment with official Survey of India / Local Government Directory (LGD) administrative boundaries and industrial registers.
3. **Black-Box Decision Making**: Machine learning models often produce opaque risk scores without local attribution, making automated alarms legally indefensible and operationally untrustworthy.
4. **Autonomous Dispatch Hazards**: Unregulated autonomous alert dispatching risks false alarms and uncoordinated municipal or industrial emergency responses.

---

## 3. Solution

AGNI-NETRA solves these challenges through an end-to-end governed intelligence architecture:

- **Sovereign Boundary Enforcement**: Real-time spatial gating against 7,595 PostGIS boundary polygons ensuring sovereign territorial filtering and automatic hierarchy resolution (State, District, Subdistrict/Tehsil).
- **Multi-Source Cadastral Fusion**: Deterministic spatial association with verified infrastructure databases, including 35,684 OpenStreetMap industrial facilities, 1,633 Central Electricity Authority (CEA) power units, and Indian Bureau of Mines (IBM) concessions.
- **Explainable Thermal Attribution**: TreeSHAP Shapley feature attribution explaining every classification decision alongside calibrated posterior probabilities.
- **Strict Human-in-the-Loop Governance**: Hardcoded safety gates prohibiting automated emergency dispatch and unverified model promotion.

---

## 4. Core Intelligence Pipeline

The AGNI-NETRA intelligence pipeline transforms raw spaceborne radiometric telemetry into actionable operational incident intelligence:

```
Satellite-Derived Thermal Observations / Telemetry
  │
  ▼
Validation (Coordinate bounds, radiometric range, duplicate hash)
  │
  ▼
Deduplication / Spatiotemporal Clustering (Spherical DBSCAN, Haversine metric)
  │
  ▼
Context Fusion (Survey of India LGD boundaries, 35,684 Industrial facilities, CEA, IBM)
  │
  ▼
Classification (Frozen 7-class thermal source classification)
  │
  ▼
Anomaly Analysis (Z-score historical baseline deviation + Isolation Forest)
  │
  ▼
Historical Correlation (Diurnal patterns, multi-year recurrence, FRP variance)
  │
  ▼
Risk Assessment (Frozen 5-factor mathematical risk engine)
  │
  ▼
Priority (Governed 4-tier operational routing and triage ranking)
  │
  ▼
Evidence (Evidence graph, epistemic uncertainty, Analysis of Competing Hypotheses)
  │
  ▼
Incident Intelligence (17-section certified dossier with cryptographic SHA-256 seal)
```

---

## 5. Features

- **Multi-Sensor Telemetry Normalization**: Normalized ingestion for NASA FIRMS VIIRS (375m) active fire detections across Suomi-NPP, NOAA-20, and NOAA-21.
- **Cadastral Infrastructure Association**: Real-time distance and buffer matching against 35,684 verified industrial facilities across India.
- **Dual Anomaly Detection**: Combination of statistical running baseline deviation ($z\text{-score}$) and unsupervised multivariate Isolation Forest (`iso-v1.0-anomaly`).
- **Explainable AI (XAI)**: Exact local Shapley feature attributions computed via SHAP TreeExplainer for every evaluated thermal cluster.
- **Master Agent JARVIS**: Governed natural-language conversational reasoning terminal with 21 intelligence domains and speech synthesis.
- **Cryptographic Dossier Export**: Server-side ReportLab generation of 17-section certified forensic PDF incident dossiers with SHA-256 integrity verification.
- **Role-Based Portals**: Dedicated operational workspaces tailored for Analysts, Public Agencies, Industrial Operators, and Academic Researchers.

---

## 6. Architecture

AGNI-NETRA employs a modern decoupled service architecture separating data ingestion, spatial calculation, machine learning inference, and interactive visualization:

```
┌─────────────────────────────────────────────────────────────┐
│                      Next.js 15 Frontend                    │
│   (Command Center, MapLibre GL, Analyst Queue, JARVIS)      │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / JSON API
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend Engine                   │
│   (Auth, Intelligence Routers, Risk Engine, Dossiers)       │
└──────┬───────────────────────┬───────────────────────┬──────┘
       │                       │                       │
┌──────▼──────┐         ┌──────▼──────┐         ┌──────▼──────┐
│ PostgreSQL  │         │   Redis 7   │         │ ML Model    │
│  + PostGIS  │         │  (Upstash)  │         │ Registry    │
│  (Supabase) │         │             │         │ (Frozen)    │
└─────────────┘         └─────────────┘         └─────────────┘
```

Detailed architectural specifications, system diagrams, and data flows are documented in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 7. Technology Stack

- **Frontend**: Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, MapLibre GL JS, Recharts, Lucide React.
- **Backend API**: FastAPI 0.115+, Python 3.11+, Pydantic v2, SQLAlchemy 2.0, ReportLab PDF Engine, Passlib/Bcrypt.
- **Spatial & GIS**: PostGIS 3.4+, Shapely 2.0, GeoPandas, PyProj.
- **Machine Learning**: Scikit-Learn, XGBoost, SHAP (TreeExplainer), Joblib.
- **Persistence & Caching**: PostgreSQL 16 (Supabase PostGIS), Redis 7 (Upstash).
- **Object Storage**: Cloudflare R2 / S3-compatible API for generated intelligence dossiers.

---

## 8. GIS Conventions

- **Coordinate Reference System (CRS)**: WGS 84 (`EPSG:4326`) used universally across storage, API contracts, and spatial computations.
- **Coordinate Tuple Ordering**: `[longitude, latitude]` for GeoJSON standard compliance; explicit named keys (`latitude`, `longitude`) in REST request/response schemas.
- **Distance Calculation**: Exact great-circle Haversine metric for cluster formation; PostGIS spheroidal `ST_Distance` for cadastral boundary evaluation.
- **Administrative Hierarchy**: Sovereign containment enforced against official Survey of India and Local Government Directory (LGD) codes (State $\rightarrow$ District $\rightarrow$ Subdistrict/Tehsil).

---

## 9. Intelligence Governance

To ensure legal defensibility, ethical compliance, and operational reliability, AGNI-NETRA enforces strict, frozen governance invariants:

### Frozen Operational Safety Invariants
```python
ENABLE_OPERATIONAL_DISPATCH_GATE = False
ENABLE_AUTOMATED_MODEL_ACTIVATION = False
```

- **Operational Dispatch Gate**: Master Agent JARVIS and backend background jobs cannot autonomously trigger siren networks, external webhooks, or public dispatch systems. All escalations require human analyst authorization.
- **Model Activation Gate**: Machine learning models cannot be retrained online or promoted automatically. Production model weights remain locked.

### Active & Candidate Models
- **Active Anomaly Detection Model**: `iso-v1.0-anomaly` (Unsupervised multivariate Isolation Forest).
- **Evaluation Candidate Classifier**: `xgb-v3.0-real-candidate` (`is_active = False`, candidate evaluation mode only).

### Frozen 5-Factor Operational Risk Formula
$$\text{RiskScore} = 0.30 \times \text{Intensity} + 0.25 \times \text{Abnormality} + 0.20 \times \text{Exposure} + 0.15 \times \text{Persistence} + 0.10 \times \text{Context}$$

- **Intensity (0.30)**: Scaled maximum Fire Radiative Power (MW) and brightness temperature.
- **Abnormality (0.25)**: Standardized deviation ($z\text{-score}$) from 6-year multi-sensor baseline.
- **Exposure (0.20)**: Proximity to dense population settlements and critical infrastructure.
- **Persistence (0.15)**: Multi-day temporal continuity and day/night diurnal activity ratio.
- **Context (0.10)**: Cadastral zoning, chemical hazard registry presence, and forest reserve buffer.

### Risk Thresholds
| Risk Tier | Score Range | Operational Protocol |
|---|---|---|
| **CRITICAL** | $\ge 75$ | Immediate escalation to Analyst Triage Queue with priority flag |
| **HIGH** | $\ge 55$ | Analyst review queue within operational shift window |
| **MODERATE** | $\ge 35$ | Routine monitoring watchlist and baseline logging |
| **LOW** | $< 35$ | Standard telemetry log and historical aggregation |

---

## 10. Human-in-the-Loop (HITL)

AGNI-NETRA implements a strict Human-in-the-Loop operational workflow:

- **Analyst Adjudication**: Authenticated human analysts review automated clusters, inspect local SHAP factor contributions, and evaluate the Analysis of Competing Hypotheses (ACH) matrix.
- **Promotion & Verification**: No candidate model or classified incident can receive authoritative verified status without an authenticated analyst signature.
- **Immutable Audit Logging**: Every adjudication, state transition, and hypothesis validation is logged with immutable UTC timestamps and user attribution.

---

## 11. JARVIS

**JARVIS** serves as the platform's Single Master Reasoning and Natural-Language Orchestration Layer:

- **Single Master Pattern**: Centralized deterministic reasoning engine without autonomous subagents or recursive worker swarms (`MAX_RECURSION_DEPTH = 0`).
- **21 Governed Intelligence Domains**: Synthesizes factual data across spatial, telemetry, infrastructure, historical, and risk domains (Domains A through U).
- **Epistemic Qualification**: Enforces explicit 6-way epistemic certainty tags: `OBSERVED`, `DERIVED`, `INFERRED`, `UNKNOWN`, `MISSING`, and `CONFLICTING`.
- **Integrated Voice Interface**: Built-in Web Speech API / TTS provider enabling hands-free situational awareness for tactical operations centers.

---

## 12. AGNI-SAT

> [!IMPORTANT]
> **SIMULATION / DIGITAL TWIN NOTICE**:
> **AGNI-SAT** is an integrated software simulation and orbital digital twin engine. It models sensor constellations, orbit propagation, radiometric revisit schedules, and swath geometry for mission planning and operational training. AGNI-SAT does NOT represent live sovereign orbital hardware acquisition.

For complete technical specifications of the simulation engine, consult [docs/SATELLITE_DIGITAL_TWIN.md](docs/SATELLITE_DIGITAL_TWIN.md).

---

## 13. Security

- **Authentication & RBAC**: Stateless JSON Web Tokens (JWT) signed with SHA-256 HMAC, Bcrypt password hashing, and granular role permissions (`ANALYST`, `AGENCY`, `RESEARCHER`, `INDUSTRY`, `ADMIN`, `PUBLIC`).
- **Public Safety Sanitization**: Public portal responses automatically strip industrial facility names, candidate IDs, SHAP values, and truncate spatial coordinates to 2 decimal places (~1.1 km) to safeguard critical infrastructure.
- **Repository Secret Guard**: Automated pre-commit guard (`scripts/pre_commit_secret_guard.py`) preventing accidental staging of `.env` files, private keys, service credentials, or production tokens.

---

## 14. Project Structure

```
E:\PROJECTS\AGNI-NETRA\
├── .github/workflows/         # Production CI/CD pipelines (acceptance & build validation)
├── alembic/                   # Database schema migration environment
├── backend/                   # FastAPI application source
│   ├── app/
│   │   ├── api/v1/            # API route controllers
│   │   ├── core/              # Security, database connection, configuration
│   │   ├── models/            # SQLAlchemy 2.0 domain entities
│   │   ├── schemas/           # Pydantic v2 validation contracts
│   │   └── services/          # Intelligence, spatial, risk, JARVIS, and PDF services
│   └── main.py                # ASGI application entrypoint
├── data_pipeline/             # Telemetry adapters & sovereign ingestion engines
├── database/                  # PostGIS initialization and spatial verification scripts
├── deployment/                # Docker compose, Dockerfiles, and deployment templates
├── docs/                      # Authoritative public documentation & API specifications
├── frontend/                  # Next.js 15 App Router web application
│   ├── src/app/               # Application routes & dashboard pages
│   ├── src/components/        # Design system & MapLibre GL viewers
│   └── src/lib/               # API clients, auth context, formatters, voice
├── ml/                        # ML feature pipelines, model artifacts, inference services
├── scripts/                   # Administrative utilities and pre-commit secret guard
└── tests/                     # Comprehensive acceptance, regression, and benchmark test suites
```

---

## 15. Local Development

### Prerequisites
- Python 3.11+ / 3.12+ (virtual environment)
- Node.js 20+ and npm 10+
- PostgreSQL 16 with PostGIS 3.4+

### Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Aryank52/AGNI-NETRA.git
   cd AGNI-NETRA
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   ```

3. **Backend setup**:
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

   # Install dependencies
   pip install -r backend/requirements.txt

   # Start backend API server
   uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Frontend setup**:
   ```bash
   cd frontend
   npm install --legacy-peer-deps
   npm run dev
   ```

5. **Run test suite**:
   ```bash
   python tests/run_all_tests.py
   ```

---

## 16. Deployment Architecture

The production deployment architecture separates public edge delivery, application compute, and managed database services:

| Component | Target Platform | Role | Configuration |
|---|---|---|---|
| **Frontend** | Vercel | Next.js 15 SSR & Edge Assets | `vercel.json` |
| **Backend API** | Render | FastAPI ASGI Web Service | `render.yaml` |
| **Ingestion Worker** | Render | Background FIRMS Telemetry Daemon | `render.yaml` |
| **Database** | Supabase | Managed PostgreSQL 16 + PostGIS 3.4 | Configured via `DATABASE_URL` |
| **Cache & Broker** | Upstash | Managed Redis 7 | Configured via `REDIS_URL` |
| **Dossier Storage** | Cloudflare R2 | S3-compatible Intelligence PDF store | Configured via `S3_*` |

> [!NOTE]
> Component deployment configurations are maintained and verified within repository manifests. Operational cloud services are activated independently following security staging review.

---

## 17. Current Project Status

- **System Version**: `1.0.0-final-freeze`
- **Core Intelligence Pipeline**: Fully integrated and verified.
- **Verified Cadastral Facilities**: 35,684 active industrial facilities indexed in spatial engine.
- **Acceptance Test Suite**: 100% pass rate (`tests/run_all_tests.py`: 7/7 suites passing).
- **Frontend Build**: Verified production compilation across all 33 Next.js routes.
- **Governance Invariants**: Enforced (`ENABLE_OPERATIONAL_DISPATCH_GATE = False`, `ENABLE_AUTOMATED_MODEL_ACTIVATION = False`).

---

## 📚 Technical Documentation Index

For detailed technical specifications, consult the authoritative documentation:

- [System Architecture Specification](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Database Architecture & ERD](docs/DATABASE.md)
- [Dataset Specification](docs/DATASET_SPECIFICATION.md)
- [JARVIS Intelligence Integration](docs/JARVIS_INTELLIGENCE_INTEGRATION.md)
- [Machine Learning Architecture](docs/ML.md)
- [Model Registry & Lineage](docs/MODEL_REGISTRY.md)
- [Security Governance](docs/SECURITY.md)
- [AGNI-SAT Simulation Specification](docs/SATELLITE_DIGITAL_TWIN.md)
