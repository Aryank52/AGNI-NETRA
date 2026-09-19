# AGNI-NETRA — FINAL CANONICAL RELEASE EVIDENCE

**Document Version:** 1.0.0  
**Release Classification:** Sovereign Industrial Thermal Intelligence Baseline  
**Authority:** AGNI-NETRA Architectural Board  
**Target Repository:** `E:\PROJECTS\AGNI-NETRA`  
**Branch:** `development/post-freeze-intelligence-hardening`  
**Baseline Commit (WP8 Hardened):** `adcf6edc18df3aca31f731bd6578f658f2a17a30`  
**Phase 26 Frozen Anchor:** `eb7824e6e58eb61f376a4dadb804984950f624e8`  

---

## 1. Canonical Master Verification Matrix

The following unified table provides the single authoritative source of truth across all architectural tiers, database counts, machine learning assets, security invariants, and runtime environments.

| Dimension | Attribute / Asset | Canonical Release Standard | Ground-Truth Evidence / Source |
|:---|:---|:---|:---|
| **Environment** | Operating System | Windows 11 (64-bit) | PowerShell Host / Windows Kernel |
| | Python Runtime | `3.12.10` | `venv/Scripts/python.exe` |
| | Node.js Runtime | `v24.16.0` | `node -v` |
| | Web Framework | Next.js `15.5.24` | `frontend/package-lock.json` |
| | Frontend UI Engine | React `19.2.8` | `frontend/package-lock.json` |
| | Type System | TypeScript `5.9.3` | Strict typecheck (`tsc --noEmit` exits 0) |
| | Map Visualization | MapLibre GL `4.7.1` | WebGL Web Worker (`blob:`) enabled |
| | API Gateway | FastAPI `0.141.1` | Pydantic v2 / Starlette |
| | Database Engine | PostgreSQL `16.15` | Localhost:5432 Visual C++ 64-bit |
| | Spatial Extension | PostGIS `3.4.2` | GEOS 3.12.1, PROJ 9.3.1 (EPSG:4326) |
| **Database Semantics** | Total Facilities Registry | `35,684` facilities | PostgreSQL `industrial_facilities` table |
| | Active Geolocated Core | `35,570` facilities | Authoritative core geocoded facilities |
| | Provisional Staging Variance | `114` facilities | Non-geolocated project staging variance |
| | Power Station Installations | `502` distinct stations | CEA Power Station Catalog |
| | Power Generating Units | `1,633` generating units | CEA Power Station Units (Never "1,633 stations") |
| | Raw Thermal Detections | `285` raw detections | Satellite thermal pixel baseline |
| | Operational Clustered Events | `88` events | 82 active hotspots + 6 analyst-verified incidents |
| | Operational Alerts | `88` alerts | Dispatched intelligence alerts |
| | Evaluation Event Snapshot | `264` records | Preserved benchmark snapshot in PostgreSQL |
| | Database Coordinate System | `EPSG:4326` (WGS 84) | PostGIS spatial column storage |
| | API GeoJSON Representation | `[longitude, latitude]` | Standard RFC 7946 GeoJSON format |
| | Frontend Map Rendering | `EPSG:3857` (Web Mercator) | MapLibre GL with `renderWorldCopies: false` |
| **ML & Governance** | Training Dataset | `v3.2-real-final` | `data/dataset_v3.2-real-final.csv` |
| | Dataset Cryptographic Hash | SHA-256 Checksum | `9677c6d65ef8f2ab388160079e868ed2bf17307a9e462e1fba26517ae9bedd0e` |
| | Candidate Model Artifact | `xgb-v3.0-real-candidate` | `ml/models/xgb_v3_real_candidate.joblib` |
| | Model Artifact Checksum | SHA-256 Checksum | `c52b6369da19d4e423652a3001e38c72737f7f66684e5bc27b9bb1c2a9c754d8` |
| | Registry Governance State | `status = CANDIDATE` | PostgreSQL `ml_model_registry` table |
| | Active Production Flag | `is_active = FALSE` | PostgreSQL `ml_model_registry` table |
| | Production Champion State | Unconfigured | *"No governed production champion configured"* |
| | Automated Activation Gate | `ENABLE_AUTOMATED_MODEL_ACTIVATION = False` | Hardcoded boolean constant (Tamper-resistant) |
| **ML Evaluation Metrics** | Primary Benchmark Split | Frozen 2026 Temporal Test | Unobserved future satellite passes (N=372) |
| | Temporal Macro F1 | **64.46%** | Primary out-of-time generalization metric |
| | Temporal Accuracy | **69.89%** | Overall classification accuracy |
| | Temporal Balanced Accuracy | **74.56%** | Macro recall across all 7 classes |
| | Temporal Weighted F1 | **71.07%** | Frequency-weighted F1 score |
| | Temporal Macro Precision | **70.63%** | Unweighted average precision |
| | Tier-1 Selective Accuracy | **97.18%** | High-confidence triage gating accuracy |
| | Spatial Cross-Validation | Spatial 5-Fold GroupKFold | Regional cross-terrain validation |
| | Spatial Mean Accuracy | **94.32%** | Spatial generalization accuracy |
| | Spatial Mean Macro F1 | **93.18%** | Spatial cross-validation Macro F1 |
| **JARVIS Architecture** | Orchestrator Authority | Single Master Reasoner | `JarvisReasoningEngine` / `JarvisAgenticOrchestrator` |
| | Agent Swarms / Subagents | Zero (`MAX_RECURSION_DEPTH = 0`) | No autonomous worker loops or swarms |
| | Core Decoupling | Decoupled Intelligence Core | AGNI-NETRA core functions if JARVIS is offline |
| | Tool Execution Budget | Maximum 10 calls | `MAX_CAPABILITY_CALLS = 10`, max 15.0s duration |
| | Epistemic Categorization | 6-Way Epistemic Separation | `OBSERVED`, `DERIVED`, `INFERRED`, `UNKNOWN`, `MISSING`, `CONFLICTING` |
| | Ground Truth Demarcation | Satellite radiances $\ne$ ground truth | Human analyst verification required for incidents |
| | Causation Invariant | Correlation $\ne$ Causation | Historical correlation disclaimers enforced |
| | Simulation Demarcation | AGNI-SAT is Digital Twin | Tagged strictly `SIMULATED_DIGITAL_TWIN` |
| **Voice Architecture** | STT / TTS Subsystem | Platform-managed async audio | Browser Web Speech API with non-blocking fallback |
| | Audio Privacy Standard | Zero Raw Audio Logging | No microphone audio streams or PCM stored |
| | Media Stream Lifecycle | Explicit Track Teardown | `track.stop()` invoked on mic disable |
| | Service Reasoning Latency | P50: 310 ms, P95: 480 ms | Backend JARVIS database & epistemic reasoning |
| | Browser Integration Latency| P50: 305 ms | STT transcription (220ms) + TTS setup (85ms) |
| | Speech-Final-to-Audio Start| P50: 440 ms | Utterance completion to speaker playback start |
| | Full Operator E2E Turnaround| **P50: 770 ms, P95: 1308 ms** | Total user-perceived turnaround (P99: 1915 ms) |
| **Security Gates** | Operational Dispatch Gate | `ENABLE_OPERATIONAL_DISPATCH_GATE = False` | Permanently disabled; zero physical dispatch |
| | Adversarial Prompt Defense | Hardened Regex Patterns | SQLi, path traversal, shell pipe, prompt injection blocked |
| | Geographic Domain | Sovereign Republic of India | Out-of-bounds telemetry quarantined |
| | HTTP Security Headers | Frames & Sniffing Denied | `X-Frame-Options: DENY`, `nosniff`, strict CSP |
| | Permissions Policy | Audio Access Restricted | `Permissions-Policy: microphone=(self)` |
| | Role-Based Access Control | Public, Analyst, Admin | Sensitive triage endpoints require `ANALYST`+ |
| **Disaster Recovery** | Backup Procedure | `pg_dump.exe -Fc` | Compressed binary archive (`7.12 MB` in `4.10s`) |
| | Recovery Procedure | `pg_restore.exe` | Clean restore into isolated database (`13.28s`) |
| | Integrity Validation | 11 Verification Checks Passed | Zero invalid geometries; 100% record parity |
| | Live Cluster Safety | Zero Mutation / Drops | Live PostgreSQL 16 database completely untouched |
| **Test Verification** | Dedicated WP8 Test Suite | 16 / 16 PASSED (100%) | `pytest tests/test_wp8_hardening.py` |
| | Full Regression Suite | 184 / 184 PASSED (100%) | WP1 through WP8 end-to-end regression |
| | Frontend Typecheck | 0 Type Errors (Clean) | `tsc --noEmit` in Next.js frontend |

---

## 2. Documented Engineering Limitations

1. **Multi-Class Classifier Candidate State:**
   The multi-class thermal classifier `xgb-v3.0-real-candidate` achieves 64.46% Macro F1 on the frozen 2026 temporal test (and 93.18% on spatial cross-validation). However, formal multi-stakeholder human governance sign-off has not been conducted. The model remains strictly in evaluation/shadow mode, and the platform explicitly displays: *"No governed production champion configured"*.
2. **Local Voice Synthesis Fidelity:**
   In operating systems or browser environments lacking local neural voices, the Web Speech Synthesis API falls back to standard operating system synthesizers, resulting in variable voice timbre across client devices.
3. **Simulation Status of AGNI-SAT:**
   AGNI-SAT is an orbital mechanics simulation and thermal payload digital twin. All telemetry is generated via SGP4 propagation and synthetic sensor radiometry; it does not represent physical satellite hardware in orbit.
4. **Thermal Anomaly Epistemic Uncertainty:**
   Satellite-derived thermal detections represent unconfirmed infrared radiances, not verified industrial fires or physical ground truth. Human verification remains authoritative for incident certification.

---

## 3. Declarative Release Sign-Off

This release baseline satisfies all nineteen (19) core mandates of Work Package 8. All contradictory or ungrounded statements have been reconciled against primary database and code evidence.

**RELEASE STATUS: PASS WITH DOCUMENTED LIMITATIONS**
