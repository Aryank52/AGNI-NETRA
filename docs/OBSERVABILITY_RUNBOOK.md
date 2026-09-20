# AGNI-NETRA — Observability & Telemetry Runbook (WP8)

**Document Version:** 1.0.0  
**Classification:** Operational Runbook  
**Target Systems:** Data Ingestion, Intelligence Core Pipeline, Single-Master JARVIS, Voice & Audio Subsystems  
**Target Environment:** Sovereign Republic of India Boundary & Core Services  

---

## 1. Overview & Core Principles

The AGNI-NETRA platform enforces strict structured logging and correlation tracing across all microservices and cognitive layers. 

### Mandatory Redaction & Privacy Invariants:
- **Zero Raw Audio Logging:** Under NO circumstances may raw audio buffers, PCM streams, or audio blobs be captured, logged, or saved to disk.
- **Zero Secret Exposure:** Credentials, JWT secret keys, database passwords, FIRMS map keys, or Authorization bearer tokens must be stripped or redacted as `[REDACTED]`.
- **Zero Personal Data Exposure:** Analyst identities are recorded solely by system UUID or assigned callsign; personal email or contact info is excluded from event payloads.
- **Distributed Correlation ID Preservation:** Every request traversing from frontend UI, through REST API, into single-master JARVIS, or across event pipeline stages MUST preserve the `X-Correlation-ID` header and log correlation attribute.

---

## 2. Telemetry Schemas Across Architectural Tiers

### 2.1 Ingestion Subsystem (`agni_netra.ingestion`)
Every ingestion cycle (NASA FIRMS, sentinel feeds, or local sensors) records structured events:

```json
{
  "timestamp": "2026-09-19T11:15:00.123Z",
  "subsystem": "ingestion",
  "provider": "FIRMS_VIIRS_SNPP",
  "correlation_id": "ingest-viirs-20260919-001",
  "batch_size": 285,
  "checkpoint_id": "chk_20260919_0600",
  "quarantine_count": 0,
  "replayed": false,
  "retry_count": 0,
  "status": "SUCCESS",
  "duration_ms": 1420
}
```

**Quarantine Logging:**
When telemetry fails spatial SOI boundary checks, coordinate bounds, or schema validation:
```json
{
  "timestamp": "2026-09-19T11:15:00.456Z",
  "subsystem": "ingestion_quarantine",
  "provider": "FIRMS_MODIS",
  "quarantine_reason": "GEOGRAPHIC_OUT_OF_BOUNDS_QUARANTINE",
  "attempted_coordinates": [67.01, 24.86],
  "action": "QUARANTINED_AND_DISCARDED"
}
```

---

### 2.2 AGNI-NETRA Intelligence Core (`agni_netra.pipeline`)
All clustering, priority scoring, infrastructure correlation, and ML evaluation emit deterministic pipeline telemetry:

```json
{
  "timestamp": "2026-09-19T11:15:02.789Z",
  "subsystem": "intelligence_core",
  "event_id": "evt_20260919_mum_088",
  "pipeline_stage": "SPATIAL_CLUSTERING",
  "correlation_id": "corr-pipe-884920",
  "model_version": "xgb-v3.0-real-candidate",
  "artifact_sha256": "c52b6369da19d4e423652a3001e38c72737f7f66684e5bc27b9bb1c2a9c754d8",
  "dataset_sha256": "9677c6d65ef8f2ab388160079e868ed2bf17307a9e462e1fba26517ae9bedd0e",
  "risk_tier": "HIGH",
  "priority_score": 87.5,
  "lifecycle_transition": "NEW -> EVALUATED",
  "processing_time_ms": 185
}
```

---

### 2.3 Single-Master JARVIS Reasoning Engine (`agni_netra.jarvis_reasoning`)
Every cognitive query, whether voice-initiated or UI-initiated, is traced through the single-master orchestrator:

```json
{
  "timestamp": "2026-09-19T11:15:10.012Z",
  "subsystem": "jarvis_single_master",
  "request_id": "req-jarvis-9921",
  "correlation_id": "corr-op-session-77",
  "actor_role": "ANALYST",
  "selected_capabilities": ["resolve_event", "query_nearby_infrastructure", "evaluate_evidence_graph"],
  "capability_latency_ms": {
    "resolve_event": 14.2,
    "query_nearby_infrastructure": 28.1,
    "evaluate_evidence_graph": 45.0
  },
  "total_evidence_count": 12,
  "epistemic_distribution": {
    "OBSERVED": 4,
    "CORRELATED": 6,
    "HYPOTHESIZED": 2
  },
  "reasoning_stop_reason": "EVIDENCE_SUFFICIENT",
  "errors": null,
  "total_duration_ms": 87.3
}
```

---

### 2.4 Voice & Audio Telemetry (`agni_netra.jarvis_voice`)
Voice interactions use implementation-neutral telemetry that measures actual pipeline segments:

```json
{
  "timestamp": "2026-09-19T11:15:12.345Z",
  "subsystem": "voice_pipeline",
  "session_id": "sess-voice-8812",
  "correlation_id": "corr-op-session-77",
  "platform_mode": "browser_managed_speech_recognition",
  "timing_breakdown": {
    "capture_duration_ms": 1820,
    "stt_latency_ms": 110,
    "jarvis_reasoning_ms": 87,
    "tts_synthesis_ms": 140,
    "total_roundtrip_ms": 337
  },
  "fallback_invoked": false,
  "fallback_reason": null,
  "barge_in_occurred": false
}
```

---

## 3. Failure & Degradation Monitoring

When subsystem failures occur, structured alarms are emitted:

| Alarm Code | Trigger Condition | Severity | Automated Action |
|---|---|---|---|
| `INGEST_PROVIDER_DOWN` | FIRMS or provider API HTTP 5xx or timeout | WARNING | Exponential backoff retry; checkpoint retained |
| `DB_RECONNECT_REQUIRED` | SQLAlchemy pool disconnect or socket drop | CRITICAL | Retry with exponential backoff (up to 3 attempts); fail-safe rollback |
| `GEO_OUT_OF_BOUNDS_BURST` | >10 out-of-bounds telemetry records in single batch | WARNING | Batch quarantined; SOI containment logged |
| `TAMPER_GATE_BREACH_ATTEMPT` | Attempt to modify `ENABLE_OPERATIONAL_DISPATCH_GATE` or `ENABLE_AUTOMATED_MODEL_ACTIVATION` | CRITICAL | Request blocked (HTTP 403); Security incident logged |
| `VOICE_STT_UNAVAILABLE` | Browser Web Speech API unsupported or denied | INFO | Graceful fallback to typed tactical input |

---

## 4. Runbook Operational Procedures

### Checking Active Log Streams
```bash
# Backend core service logs
Get-Content -Path logs/agni_netra.log -Tail 100 -Wait

# Grep for security rejections or injection attempts
Select-String -Path logs/agni_netra.log -Pattern "ADVERSARIAL_INJECTION_BLOCKED"
```

### Trace Request by Correlation ID
```bash
Select-String -Path logs/agni_netra.log -Pattern "corr-op-session-77"
```
