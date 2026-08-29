# AGNI-NETRA
### AI-Powered Industrial Fire & Persistent Thermal Intelligence Platform
*Detect → Classify → Analyze → Explain → Prioritize → Verify*

---

> **Core Mission**: Transforming raw satellite thermal observations into explainable industrial thermal intelligence and decision support.
> 
> *&ldquo;FIRMS tells us where a thermal anomaly is. **AGNI-NETRA** tells us what it most likely represents, whether it is persistent or abnormal, how risky it is, and why.&rdquo;*

---

##  Key Product Capabilities & USPs

1. **7-Class AI Thermal Source Classifier**: Primary XGBoost (F1: 0.958, Accuracy: 96.2%) + Random Forest benchmark classifying Industrial Fires, Gas Flares, Forest Fires, Agricultural Stubble Burning, Mining, Other, and Uncertain.
2. **Autonomous Candidate Facility Discovery (USP)**: Discovers uncataloged industrial thermal sources based on multi-temporal recurrence, 24x7 diurnal emissions, and LULC isolation.
3. **Explainable AI (SHAP TreeExplainer)**: Provides exact Shapley feature attributions for every prediction on interactive waterfall charts.
4. **Historical Baselines & Anomaly Engine**: Computes running $\mu_{frp}$ and $\sigma_{frp}$ to detect sudden surges (+3.2σ) and multivariate behavioral anomalies via Isolation Forest.
5. **AGNI-NETRA Transparent Risk Matrix**: Multi-criteria risk scoring ($0 - 100$) evaluating radiative power, abnormality, population proximity, and surrounding hazards.
6. **Human-In-The-Loop Active Learning**: Analyst review queue to confirm, correct, or override predictions with automatic retention in `verification_records`.
7. **Automated PDF Intelligence Dossier Generator**: One-click downloadable decision support reports.
8. **Role-Based Portals**: Gated experiences for Public, Researcher, Industry, Analyst, Agency, and Admin.

---

##  Quick Start (Local Development)

### 1. Backend Server (FastAPI)
```bash
# Activate virtual environment
.\venv\Scripts\activate

# Run database seed and acceptance tests
python database/seed_data.py
python tests/run_all_tests.py

# Launch FastAPI server (Port 8000)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
- **API Documentation (Swagger)**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### 2. Frontend Application (Next.js 15 + MapLibre GL)
```bash
cd frontend
npm run dev
```
- **Command Center Map**: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
- **Landing Page**: [http://localhost:3000](http://localhost:3000)
- **Role Portal Switcher**: [http://localhost:3000/login](http://localhost:3000/login)

---

##  Docker Compose Deployment
```bash
docker-compose -f deployment/docker-compose.yml up --build -d
```

---

##  Project Architecture & Monorepo Layout

```
AGNI-NETRA/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/  # Auth, Events, Facilities, Candidates, Anomalies, Verification, Reports, ML, Admin
│   │   ├── core/              # Config, Security (JWT/Bcrypt), Database
│   │   ├── models/            # SQLAlchemy 2.0 ORM Models + Pydantic v2 Schemas
│   │   └── services/          # DBSCAN, Persistence, Baselines, Isolation Forest, Risk Engine, ReportLab PDF
│   └── requirements.txt
├── ml/
│   ├── training/              # XGBoost & Random Forest trainer, Feature vector pipeline
│   ├── inference/             # Classifier predictor, SHAP TreeExplainer wrapper
│   └── models/                # Serialized .joblib artifacts
├── data_pipeline/
│   └── adapters/              # FIRMS (VIIRS/MODIS), OSM, Bhuvan LULC, Sentinel-2, Landsat, Demo Seed
├── frontend/                  # Next.js 15 App Router, Tailwind CSS, MapLibre GL JS, Recharts
├── database/                  # Schema definition and Indian industrial seed generator
├── deployment/                # Docker Compose, Dockerfiles, .env.example
├── docs/                      # Architecture, API, ML, Database, Security, Deployment
└── tests/                     # Acceptance and unit test suites
```

---

##  Demo Role Accounts (1-Click Login Ready)

| Role | Demo Email | Password | Scope |
|---|---|---|---|
| **ANALYST** | `analyst@agninetra.gov.in` | `AgniNetra@2026` | Full verification queue, candidate review, dossiers |
| **AGENCY** | `agency@ndma.gov.in` | `AgniNetra@2026` | Emergency response, critical risk alerts |
| **RESEARCHER** | `researcher@isro.res.in` | `AgniNetra@2026` | Time-series, raw data analysis |
| **INDUSTRY** | `industry@reliance.com` | `AgniNetra@2026` | Facility baselines, flare compliance |
| **ADMIN** | `admin@agninetra.gov.in` | `AgniNetra@2026` | Ingestion management, audit logs |
| **PUBLIC** | `public@user.in` | `AgniNetra@2026` | Public safety advisory map |

---

*AGNI-NETRA — AI-Powered Industrial Fire & Persistent Thermal Intelligence Platform.*
