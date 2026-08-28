# AGNI-NETRA — Security & Role-Based Access Control (RBAC)

## 1. Authentication & Token Management

- **Algorithm**: HMAC-SHA256 (HS256) JWT tokens with configurable TTL (default 24 hours).
- **Password Hashing**: Direct Bcrypt salt-hashing (`bcrypt.gensalt()`, `bcrypt.hashpw`).
- **Identity Context**: Injected into FastAPI route dependencies via `OAuth2PasswordBearer`.

---

## 2. Role-Based Access Control (RBAC) Matrix

| Portal / Module | PUBLIC | RESEARCHER | INDUSTRY | ANALYST | AGENCY | ADMIN |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| General Thermal Map & Alerts | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| State-Level Aggregate Statistics | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Exact Facility Coordinates | ❌ | ✅ (Anonymized) | Own Facility | ✅ | ✅ | ✅ |
| SHAP Feature Attribution Chart | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Candidate Facility Discovery Queue | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| HITL Analyst Verification Action | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Download PDF Intelligence Dossier | ❌ | ✅ | Own Facility | ✅ | ✅ | ✅ |
| Ingestion & Model Management | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| User Permissions & Audit Logs | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 3. Enterprise Audit Trail

All critical security and decision actions are immutably logged to `audit_logs`:
- User logins & registrations
- Candidate facility promotions
- Human analyst label corrections and overrides
- Dossier report generations and data exports
