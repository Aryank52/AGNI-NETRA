# AGNI-NETRA — JARVIS Operations & Governance Runbook

**Operational Scope:** Master Intelligence Reasoning, Governed Capability Orchestration & Voice Interface  
**Classification:** Operational Security Level 3 — Ministry / Agency Command Center

---

## 1. Operating Principles & Roles

### 1.1 Separation of Intelligence vs Reasoning
- **AGNI-NETRA Core Engine:** Sole authority for computed physical truth (satellite thermal detections, PostGIS spatial containment, 5-factor risk scores, historical baselines, and ML inferences).
- **JARVIS Master Orchestrator:** Reasoning, evidence orchestration, Analysis of Competing Hypotheses (ACH), next-best-evidence determination, explanation, and voice interface.
- **Human Analyst:** Sole authority for operational confirmation and physical field dispatch.

### 1.2 Permanent Platform Invariants
```python
ENABLE_OPERATIONAL_DISPATCH_GATE = False   # Physical dispatch is blocked
ENABLE_AUTOMATED_MODEL_ACTIVATION = False  # Model activation requires human Admin
MAX_CAPABILITY_CALLS = 10                  # Budget ceiling per investigation
MAX_RECURSION_DEPTH = 0                    # Single master orchestrator (no subagents)
```

---

## 2. Analyst Interaction Workflows

### 2.1 Web Intelligence Console (`/jarvis`)
1. **Situational Awareness Dashboard:** Monitor live attention items, risk queues, and state-wise thermal activity across India.
2. **Event Deep-Dive:** Click any active event or type:
   ```
   JARVIS, investigate Event EVT-2026-08-0001
   ```
3. **Epistemic Evidence Review:** Review findings categorized strictly by epistemic status:
   - `OBSERVED`: Raw satellite telemetry (FRP, brightness, coordinates).
   - `DERIVED`: Distance to nearest industrial assets, 5-factor risk score.
   - `INFERRED`: Candidate model prediction, calibrated probability, top SHAP drivers.
   - `UNKNOWN` / `MISSING`: Uncataloged assets, missing radar or optical passes.
   - `CONFLICTING`: Contradictory evidence requiring human resolution.

### 2.2 Voice Interface
- **Microphone Button:** Tap once to initiate speech capture.
- **Voice Commands Supported:**
  - *"JARVIS, what is the situation in Gujarat?"*
  - *"Investigate the highest priority event."*
  - *"Explain the evidence for event EVT-GJ-2025-001."*
  - *"What changed from historical baseline?"*
- **Voice Security Boundary:** Voice commands cannot bypass RBAC, cannot execute raw SQL or shell commands, cannot alter database records, and cannot query foreign territories.

---

## 3. Human-in-the-Loop (HITL) Verification Protocol

When an event is categorized as `REQUIRES_HUMAN_REVIEW` or risk score $\ge 65.0$:

```
THERMAL EVENT (Risk >= 65.0)
          ↓
[JARVIS INVESTIGATION] (Synthesizes Evidence, ACH Matrix, Next-Best-Evidence)
          ↓
[ATTENTION QUEUE] (Event marked: REQUIRES_HUMAN_REVIEW)
          ↓
[ANALYST INSPECTION] (Analyst reviews ground photography / optical / on-site log)
          ↓
[VERIFICATION VERDICT]
  ├── CONFIRM  -> Confirmed industrial incident; case note appended
  ├── CORRECT  -> Misclassification corrected; feedback logged to retraining pool
  └── DISMISS  -> False alarm / benign emission recorded
          ↓
[AUDIT TRAIL] (SHA-256 verified audit log created in database)
```

> [!CAUTION]
> **No Automated Dispatch:** Even if calibrated probability is $99\%$, JARVIS will NEVER dispatch emergency units. Operational dispatch must be handled externally through authorized departmental channels.

---

## 4. Troubleshooting & Graceful Degradation Runbooks

### 4.1 PostGIS Cadastral Proximity Service Unavailable
- **Symptom:** Logs show `[CAPABILITY ERROR] Failed executing GET_SPATIAL_CONTEXT`.
- **System Behavior:** Spatial context is marked `DEGRADED`; nearest facility distance defaults to `99999.0m`; investigation continues.
- **Analyst Action:**
  1. Check PostgreSQL daemon status on port 5432 (`SELECT PostGIS_Full_Version();`).
  2. Verify GiST spatial indices:
     ```sql
     REINDEX INDEX idx_industrial_facilities_geom_gist;
     ```

### 4.2 Machine Learning Model Inference Degradation
- **Symptom:** `GET_MODEL_PREDICTION` returns `UNCLASSIFIED` or latency exceeds threshold.
- **System Behavior:** Epistemic uncertainty tier transitions to `MISSING_DATA`; explanation marked `MISSING`; baseline and risk scoring continue without crashing.
- **Admin Action:**
  1. Check `ml/models/candidates/` artifact integrity:
     ```powershell
     certutil -hashfile ml/models/candidates/xgb_v3.0_candidate.joblib SHA256
     ```
  2. Verify hash matches PostgreSQL `ml_model_registry` entry: `c52b6369da19d4e423652a3001e38c72737f7f66684e5bc27b9bb1c2a9c754d8`.

### 4.3 Voice Interface Failure (STT or TTS Unavailable)
- **Symptom:** Voice input does not transcribe or audio does not play.
- **System Behavior:** Voice failures are isolated to the peripheral UI. The core intelligence engine, databases, and REST APIs remain completely unaffected.
- **Analyst Action:**
  1. Switch to text input in the `/jarvis` console.
  2. Verify browser microphone permissions in settings.

---

## 5. Security Incident Response

### 5.1 Prompt / Instruction Injection Attempt
- **Detection:** Security filter logs `[SECURITY] Adversarial injection detected: <query>`.
- **System Behavior:** Request rejected with `ADVERSARIAL_INJECTION_BLOCKED`; audit record created with client IP and user ID.
- **Admin Action:**
  Review `audit_logs` table for repeated injection patterns from the same user session:
  ```sql
  SELECT * FROM audit_logs WHERE action = 'SECURITY_VIOLATION' ORDER BY timestamp DESC LIMIT 20;
  ```

### 5.2 Out-of-Domain Foreign Queries
- **Detection:** Query contains foreign city name (e.g. Lahore, Karachi, Colombo, Yangon).
- **System Behavior:** Query blocked with `OUT_OF_DOMAIN_LOCATION`; no queries executed against Indian cadastral databases.
- **Resolution:** Inform operator that AGNI-NETRA is sovereign to the territory of India.
