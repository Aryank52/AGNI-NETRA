# AGNI-NETRA — VOICE OPERATIONS RUNBOOK (WP7)
## Standard Operating Procedures for Operational Voice Interface to Single-Master JARVIS

**Document Version:** 1.0.0  
**Effective Date:** September 19, 2026  
**Audience:** Operational Analysts, Duty Officers, Command Center Operators  
**System Classification:** Sovereign Republic of India Operational Thermal Monitoring  

---

## 1. Overview & Operating Philosophy

The AGNI-NETRA Voice Interface provides a hands-free, low-latency conversational interface to the Single-Master JARVIS Reasoning Engine. 

### Core Operating Rules:
1. **Voice is an Interface, Not Intelligence**: Spoken audio is transcribed into text, validated against sovereign geographic and prompt-injection security gates, and routed directly to the Single-Master JARVIS Orchestrator. Voice cannot alter system semantics or bypass authorization.
2. **Hardened Safety Gates**:
   - `ENABLE_OPERATIONAL_DISPATCH_GATE = False` (Permanently Locked)
   - `ENABLE_AUTOMATED_MODEL_ACTIVATION = False` (Permanently Locked)
   - Voice commands can never trigger external emergency services dispatch or activate candidate machine learning models.
3. **No Synthetic Fabrication**: The voice interface never fabricates transcripts, telemetry, or answers. If data is unavailable or uncataloged, JARVIS explicitly returns `UNKNOWN` or `MISSING`.

---

## 2. Operator Interface & Visual States

The console top bar and voice pill visibly communicate the real-time operational status:

| Visual State Badge | Operating Condition | Operator Action |
|:---|:---|:---|
| `MIC OFF` | Microphone is inactive and audio capture stream is closed. | Click the tactical mic button to begin speaking. |
| `REQUESTING PERMISSION` | Browser is requesting microphone access authorization. | Click "Allow" in the browser security prompt. |
| `LISTENING` | Microphone is open; speech recognition is actively capturing audio. | Speak the operational query clearly in English. |
| `TRANSCRIBING` | Interim speech tokens are being converted to text. | Continue speaking or pause when complete. |
| `THINKING` | Audio capture stopped; JARVIS is evaluating database state. | Await grounded structured assessment. |
| `SPEAKING` | JARVIS TTS is audibly articulating the structured finding. | Listen to response or press mic to barge in. |
| `ERROR` / `DEGRADED` | Hardware issue or permission denied. | Use the typed natural language prompt bar. |

---

## 3. Supported Operational Voice Intents

Operators may use conversational natural language commands:

### 3.1 Situational Awareness
- *"What is happening right now?"*
- *"Give me a situational report."*
- *"Which events changed in the latest observation cycle?"*
- *"How many critical fires are active?"*

### 3.2 Targeted Investigation
- *"Investigate event EVT-GJ-2025-001."*
- *"Investigate the highest priority fire."*
- *"Analyze thermal event in Gujarat."*
- *"Examine uncataloged thermal anomaly."*

### 3.3 Asset & Model Provenance Inquiries
- *"What is the current model status?"*
- *"Check candidate model lineage."*
- *"What is our total facility count?"*

---

## 4. Barge-In & Interruption Procedures

JARVIS supports instantaneous barge-in interruption to maintain operator control:
1. When JARVIS is speaking (`SPEAKING`), click the microphone button or type a new query.
2. The browser immediately halts speech synthesis (`synth.cancel()`), silences audio output, and transitions to `LISTENING`.
3. If an emergency briefing requires immediate silence, click the `Stop Speaking` button or toggle `MUTED`.

---

## 5. Failure Modes & Graceful Degradation SOP

| Incident / Symptom | Root Cause | Operator Response / Recovery SOP |
|:---|:---|:---|
| **Microphone Permission Denied** | Browser blocked mic permission. | 1. Look for red camera/mic icon in browser URL bar.<br>2. Select "Always allow https://..." and reload.<br>3. In the interim, use the typed prompt bar below the mic. |
| **No Microphone Detected** | Hardware device unplugged or disconnected. | Check USB/3.5mm headset connection. The typed prompt bar remains 100% operational. |
| **Speech Recognition Network Error** | Transient network interruption to browser STT service. | Switch to typing in the prompt bar. Intelligence analysis is unaffected. |
| **TTS Speech Audio Inaudible** | Browser autoplay policy or OS audio muted. | 1. Check speaker volume.<br>2. The complete text response is simultaneously rendered on screen in the Reasoning Assessment box. |
| **Security Rejection Notice** | Query requested out-of-domain foreign location or restricted command. | Re-submit query ensuring geographic targets remain within the sovereign boundaries of the Republic of India. |

---

## 6. Security, Privacy & Audio Data Retention Policy

- **No Raw Audio Persistence**: Raw microphone PCM audio streams are processed strictly in volatile browser memory and are **never** persisted to disk or sent to external unauthorized cloud providers.
- **Audited Transcripts**: Only the final text transcript, correlation ID, and JARVIS execution trace are logged to the PostgreSQL audit log for analytical review.
- **Sensitive Credentials Protected**: Operators must never dictate passwords, JWT tokens, or encryption keys. The voice input parser automatically strips credential-like tokens.

---

## 7. Operational Escalation Contacts

For persistent hardware failure or software degradation:
- **Lead GIS / System Administrator**: `ops@agni-netra.gov.in`
- **Command Center Duty Desk**: Extension `7100` / Secure Tactical VoIP `AGNI-OPS-1`
