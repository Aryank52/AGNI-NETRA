# AGNI-NETRA — Production Release Runbook

> **Target Baseline**: Final Release Freeze Baseline  
> **Audience**: Platform Operations, Site Reliability Engineers, Lead System Architects  
> **Status**: Verified Operational Runbook

---

## 1. Pre-Deployment Verification Checklist

Before deploying any production release artifact, the release engineer must verify that the local working tree satisfies all invariants:

- [ ] **Git Working Tree**: Verified clean branch `stabilization/final-release-freeze`.
- [ ] **TypeScript Compilation**: `npm run typecheck` passes with **0 errors**.
- [ ] **Next.js Production Build**: `npm run build` succeeds (all 33 routes generate cleanly).
- [ ] **Backend Acceptance Tests**: `pytest tests/test_e2e_acceptance_flow.py tests/test_dossier_assessment_contract.py -v` passes (100% pass rate).
- [ ] **Safety Gate**: `ENABLE_OPERATIONAL_DISPATCH_GATE = False` verified in `backend/app/core/config.py`.
- [ ] **Model Activation Gate**: `ENABLE_AUTOMATED_MODEL_ACTIVATION = False` verified.
- [ ] **Model Candidate Status**: `xgb-v3.0-real-candidate` status verified as `CANDIDATE` (`is_active = FALSE`).
- [ ] **Active Champion**: Verified as `NONE CONFIGURED`.

---

## 2. Release Deployment Sequence

### Step 1: Database Migration & Health Check
1. Ensure PostgreSQL 16 + PostGIS 3.4 is operational:
   ```bash
   psql -U postgres -d agni_netra -c "SELECT PostGIS_Full_Version();"
   ```
2. Execute schema upgrades:
   ```bash
   alembic upgrade head
   ```

### Step 2: Backend Container Rollout
1. Build and tag the backend container image:
   ```bash
   docker build -t agni-netra-backend:1.0.0 -f backend/Dockerfile .
   ```
2. Deploy backend service and verify health endpoint:
   ```bash
   curl -fsS http://127.0.0.1:8000/health
   # Expected: {"status": "ok"}
   ```

### Step 3: Frontend Container / Edge Rollout
1. Build frontend artifact with production `NEXT_PUBLIC_API_URL`:
   ```bash
   cd frontend
   npm ci
   npm run build
   ```
2. Deploy frontend application and verify accessibility on Port 3000 / Port 443.

---

## 3. Post-Deployment Smoke Test (Primary Analyst Journey)

Perform this verification immediately following deployment:

1. **Authentication**:
   - Access `/login`.
   - Authenticate with analyst credentials.
   - Confirm redirect to `/dashboard`.
2. **Command Center & Map**:
   - Verify KPI strip displays 88 Clustered Events, 82 Hotspots, 6 Verified Incidents, and 88 Alerts.
   - Confirm MapLibre renders India bounds and vector layers.
3. **Event Dossier**:
   - Click on the target event from the stream.
   - Verify 9 canonical sections (Overview, Thermal, Context, History, ML, Risk, Verification, JARVIS, Prevention) load without error.
4. **JARVIS Intelligence**:
   - Open `/jarvis?event_id=1`.
   - Confirm 8 structured intelligence domains render; verify the 18-question grid is hidden.
5. **HITL Verification**:
   - In `/dashboard/verification`, record a verification determination (`CONFIRMED_ANOMALY`).
   - Confirm determination commits to audit trail.
6. **Reporting & PDF Binary Stream**:
   - Navigate to `/dashboard/reports`.
   - Click `GENERATE PDF` on an event dossier.
   - Verify file downloads with valid `%PDF-1.4` binary header.

---

## 4. Common Failure Modes & Emergency Mitigations

### 4.1 CORS Error on Frontend API Requests
- **Symptom**: Browser console shows `CORS policy: No 'Access-Control-Allow-Origin' header is present`.
- **Mitigation**: Update `BACKEND_CORS_ORIGINS` in backend environment to include the exact frontend protocol, domain, and port (e.g. `https://console.agninetra.gov.in`). Restart backend service.

### 4.2 MapLibre External Raster Tile Timeout
- **Symptom**: Console logs tile fetch timeouts from third-party OSM/Carto servers.
- **Mitigation**: Normal degraded operation. The application automatically falls back to `MINIMAL_DARK_STYLE` (#060913 sovereign dark canvas) while rendering all PostGIS vector geometries and thermal events.

### 4.3 Web Speech API Microphone Permission Denied
- **Symptom**: User clicks microphone icon; console registers `not-allowed`.
- **Mitigation**: Built-in graceful degradation. Prompt displays `"Microphone permission denied. Voice input is unavailable. Please type your query in the prompt bar."` Text queries continue to function normally.

### 4.4 Database Connection Pool Exhaustion
- **Symptom**: Backend logs `TimeoutError: QueuePool limit of size 25 overflow 50 reached`.
- **Mitigation**: Ensure `pool_pre_ping: True` is active; verify PostgreSQL `max_connections >= 200`; recycle connections via `DB_POOL_RECYCLE=1800`.

---

## 5. Rollback Protocol

If a critical severity P0 issue occurs during deployment:

1. **Immediate Action**:
   - Route traffic back to the prior stable release container/commit.
   - Do NOT execute automated down-migrations against active PostgreSQL tables.
2. **Audit Verification**:
   - Verify `/health` on rollback version.
   - Review PostgreSQL transaction error logs.
3. **Incident Debrief**:
   - Log timestamp, commit SHA, and observed failure trace in platform audit register.
