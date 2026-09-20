# AGNI-NETRA — Security Operations Runbook (WP8)

**Document Version:** 1.0.0  
**Classification:** Operational Security Manual  
**Target Platform:** AGNI-NETRA Sovereign Thermal Intelligence & Single-Master JARVIS  
**Base:** Post-Freeze Hardened Baseline  

---

## 1. Security Architecture & Boundary Overview

AGNI-NETRA operates under a Zero-Trust, Defense-in-Depth model tailored for critical sovereign intelligence infrastructure.

```
                    ┌───────────────────────────────┐
                    │    Operator Browser Client    │
                    │ (Next.js 15.5.24 + React 19)  │
                    └───────────────┬───────────────┘
                                    │ HTTPS + WSS (Strict CSP, Frames Denied)
                                    ▼
                    ┌───────────────────────────────┐
                    │       FastAPI API Gateway     │
                    │   (JWT Validation, RBAC,      │
                    │    Rate Limiting, Sanitize)   │
                    └───────┬───────────────┬───────┘
                            │               │
                            ▼               ▼
             ┌─────────────────────┐  ┌───────────────────────┐
             │ Single-Master JARVIS│  │  Intelligence Core    │
             │   Reasoning Engine  │  │  Pipeline & Services  │
             └──────────┬──────────┘  └───────────┬───────────┘
                        │                         │
                        ▼                         ▼
             ┌────────────────────────────────────────────────┐
             │       PostgreSQL 16 + PostGIS 3.4.2            │
             │     (Parameterized ORM, Encrypted at Rest)     │
             └────────────────────────────────────────────────┘
```

---

## 2. Authentication & Token Lifecycle

### 2.1 JWT Token Verification
- **Algorithm:** HS256 with cryptographically random secret key (minimum 256 bits).
- **Expiration:** Access tokens expire strictly after 30 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES = 30`).
- **Signature Validation:** Every protected API request validates signature, `exp`, `sub`, and `role` claims.
- **Malformed & Expired Tokens:** Handled with deterministic `HTTP 401 Unauthorized`. Stack traces or internal error details are strictly suppressed.

### 2.2 Replay & Session Protection
- Tokens carry unique `jti` (JWT ID) claims when stateful session invalidation is active.
- Sensitive state-modifying actions (verification, model review) require an active session token.

---

## 3. Role-Based Access Control (RBAC) Matrix

| Endpoint Group | Public (`PUBLIC`) | Analyst (`ANALYST`) | Administrator (`ADMIN`) | Invariant Rule |
|---|---|---|---|---|
| Health & Version (`/health`, `/version`) | ALLOW | ALLOW | ALLOW | Unauthenticated read-only status |
| Map Layer Telemetry (`/api/v1/events`) | DENY | ALLOW (Read) | ALLOW (Read) | Analyst access required |
| Incident Verification (`/api/v1/events/{id}/verify`) | DENY | ALLOW (Write) | ALLOW (Write) | Full audit logging required |
| JARVIS Reasoning (`/api/v1/jarvis/voice/command`) | DENY | ALLOW (Exec) | ALLOW (Exec) | Single-master bounds enforced |
| Model Governance (`/api/v1/governance/`) | DENY | DENY (Read only) | ALLOW (Review) | Automated activation BLOCKED |
| Operational Dispatch (`/api/v1/dispatch/`) | DENY | DENY | DENY | **Permanently Disabled** (`False`) |

---

## 4. Input Validation & Injection Resistance

All incoming HTTP parameters, JSON request bodies, and conversational prompts pass through multi-stage sanitization:

1. **SQL Injection Defense:**
   - Database interaction is exclusively executed via SQLAlchemy 2.0 parameterized queries and ORM objects. Raw string interpolation (`f"SELECT * FROM ... {user_input}"`) is prohibited.
   - JARVIS regex filter intercepts raw SQL commands (`SELECT`, `DROP`, `DELETE`, `INSERT`, `UPDATE`, `UNION`).

2. **Path Traversal Defense:**
   - File access strictly disallows relative path traversing characters (`../`, `..\\`).
   - All dataset and artifact paths are resolved against strictly whitelisted root directories.

3. **Command & Shell Injection:**
   - No user input is passed to shell evaluators (`os.system`, `subprocess.Popen(..., shell=True)`).
   - Regex patterns filter shell pipes (`|`), redirects (`>`), and command binaries (`curl`, `wget`, `cat /dev/`).

4. **Sovereign Geographic Boundary Defense:**
   - Coordinates are checked against SOI bounding polygons. Coordinates outside India are rejected with `GEOGRAPHIC_OUT_OF_BOUNDS_QUARANTINE`.
   - Conversational mentions of foreign territorial targets (e.g. Karachi, Lahore, Dhaka) are flagged as `OUT_OF_DOMAIN_LOCATION` and rejected without inference.

---

## 5. Tamper-Resistant Safety Gates

The platform enforces two immutable architectural gates:

```python
ENABLE_OPERATIONAL_DISPATCH_GATE = False
ENABLE_AUTOMATED_MODEL_ACTIVATION = False
```

### Tamper Resistance Protocols:
- **No Configuration Override:** Environment variables attempting to set `ENABLE_OPERATIONAL_DISPATCH_GATE=true` at runtime are rejected by the configuration loader.
- **No Dynamic Mutation:** The attributes are frozen at module level.
- **Incident Escalation:** Any attempt to invoke dispatch endpoints triggers an immediate `SECURITY_AUDIT_ALERT` log entry with `outcome: "TAMPER_PREVENTED"`.

---

## 6. Secrets Management & Credential Hygiene

- **Storage:** No secrets or private keys are stored in source code. All secrets are loaded from environment variables (`.env.local` or container secrets engine).
- **FIRMS API Keys:** Masked in logs and admin UI; only first 4 and last 4 characters are logged for debugging.
- **Audit Logging:** Database credentials and JWT secrets are excluded from debug representations.

---

## 7. Incident Response & Playbooks

### Scenario A: Brute Force Authentication Attempt
1. Rate limiting trips at 10 failed attempts per IP per minute.
2. IP address receives `HTTP 429 Too Many Requests`.
3. Event logged to `audit_logs` with severity `WARNING`.

### Scenario B: Injection Attack via JARVIS Prompt
1. Input matched against `ADVERSARIAL_INJECTION_PATTERNS`.
2. Reasoning engine halts immediately; no LLM context or database query executed.
3. User receives: `"ADVERSARIAL_INJECTION_BLOCKED: Command matches restricted security pattern."`
4. Audit log records actor, IP, timestamp, and sanitized payload.

### Scenario C: Unauthorized Dispatch Attempt
1. Request reaches gateway or reasoning engine requesting physical actuator dispatch.
2. `ENABLE_OPERATIONAL_DISPATCH_GATE` evaluated (`False`).
3. Request rejected with `DispatchBlockedException` (`HTTP 403`).
4. Security alert logged to persistent audit table.
