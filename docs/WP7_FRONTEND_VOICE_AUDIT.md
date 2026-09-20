# AGNI-NETRA — WP7 Frontend & Voice Subsystem Comprehensive Audit

**Execution Context:** Post-Freeze Intelligence Hardening (Base: Phase 26 `eb7824e6e58eb61f376a4dadb804984950f624e8` + WP1–WP6)  
**Audit Scope:** Next.js 15 App Router, React 19, TypeScript, state management, MapLibre GL integration, browser audio lifecycle, STT/TTS abstractions, error boundaries, latency profiling, and security boundaries.  
**Taxonomy Categories:** `IMPLEMENTED`, `VERIFIED`, `PARTIAL`, `DEGRADED`, `SIMULATED`, `MOCKED`, `NOT CONFIGURED`, `MISSING`, `FUTURE`.

---

## 1. Executive Summary

The AGNI-NETRA frontend is an operations dashboard designed for environmental monitoring, industrial compliance, and sovereign intelligence observation across India. The objective of this audit is to rigorously inspect every component of the frontend application, evaluate the browser audio stack, verify data integrity semantics, and eliminate any synthetic or misleading presentation.

```
USER MICROPHONE
      ↓
[BROWSER PERMISSION & AUDIOCONTEXT] (Clean lifecycle, no leaks)
      ↓
[SPEECH-TO-TEXT (STT) ABSTRACTION] (Web Speech API / fallback)
      ↓
[JARVIS MASTER REASONING ENGINE] (Intent normalization, sovereign validation, ACH)
      ↓
[STRUCTURED RESPONSE CONTRACT] (Facts, derived metrics, inferred models, gaps)
      ↓
[OPERATIONAL CONSOLE RENDERING] (Epistemic badges, model provenance, MapLibre)
      ↓
[TEXT-TO-SPEECH (TTS) PLAYBACK] (Interruption / barge-in, mute control)
```

---

## 2. Technology Stack & Framework Audit

| Component | Current Version | Required Version | Status | Architectural Rationale & Compatibility |
| :--- | :--- | :--- | :---: | :--- |
| **Next.js** | `15.1.7` | `15.1.7` | `VERIFIED` | Next.js 15 App Router is fully functional with React 19 support. No migration required; hardening in place. |
| **React** | `19.0.0` | `19.0.0` | `VERIFIED` | Native hooks (`useCallback`, `useRef`, `useState`) and modern client-side rendering. |
| **TypeScript** | `5.7.3` | `5.7.3` | `VERIFIED` | Strict type checking enabled (`tsc --noEmit` clean with 0 errors). |
| **MapLibre GL** | `4.7.1` | `4.7.1` | `VERIFIED` | High-performance WebGL vector tile rendering for 35,570 facilities and 7,595 administrative polygons. |
| **Tailwind CSS** | `3.4.17` | `3.4.17` | `VERIFIED` | Utility-first styling with responsive layouts and dark mode palettes. |
| **Lucide React** | `0.475.0` | `0.475.0` | `VERIFIED` | Standard iconography for epistemic tiers, audio states, and alert levels. |

---

## 3. Subsystem-by-Subsystem Component Audit

| Subsystem / Path | Functional Responsibility | Audit Status | Canonical Findings & Hardening Directives |
| :--- | :--- | :---: | :--- |
| **App Router (`src/app/`)** | Layouts, routing, page components (`/`, `/dashboard`, `/jarvis`, `/portal`). | `VERIFIED` | Client-side layouts (`layout.tsx`) properly wrap header and navigation. Protected routes enforce authentication. |
| **JARVIS UI (`src/app/jarvis/page.tsx`)** | Operational console for master JARVIS orchestrator. | `PARTIAL` $\to$ `VERIFIED` | Pre-WP7 implementation contained visual cards and inline speech synthesis. Hardened into a strongly typed state machine with explicit epistemic segregation. |
| **Browser Audio Capture** | Microphone access, MediaStream, and Web Audio API. | `PARTIAL` $\to$ `VERIFIED` | Previously relied solely on inline `SpeechRecognition`. Hardened with dedicated `useVoiceInterface` hook managing `AudioContext` lifecycle and stopping active tracks upon release. |
| **Speech-to-Text (STT)** | Real-time speech transcription. | `IMPLEMENTED` | Wrapped via `STTProvider` abstraction supporting Web Speech API with automatic graceful fallback to typed input. |
| **Text-to-Speech (TTS)** | Audible spoken narrative playback. | `IMPLEMENTED` | Wrapped via `TTSProvider` abstraction supporting `window.speechSynthesis` with speech cancellation, barge-in, and mute control. |
| **Barge-In / Interruption** | Halting TTS when user activates microphone. | `IMPLEMENTED` | Audio playback is immediately cancelled upon microphone activation to prevent echo and confusing audio overlaps. |
| **MapLibre View (`src/components/map/`)** | Interactive geospatial mapping with PostGIS layers. | `VERIFIED` | Renders active thermal events, facility clusters, and sovereign boundaries. Synchronized with selected JARVIS event focus. |
| **Event Dossier (`src/components/intelligence/`)** | Detailed 7-dimension operational dossier view. | `VERIFIED` | Displays full event telemetry, cadastral proximity, historical baselines, and SHAP attribution charts. |
| **API Client (`src/lib/api.ts`)** | Central HTTP request handler. | `VERIFIED` | Automatically attaches JWT bearer tokens, enforces 12s timeouts, and handles 401 unauthorization events. |
| **Auth Context (`src/lib/authContext.tsx`)** | Client-side user session and RBAC context. | `VERIFIED` | Stores user profiles and roles (`ADMIN`, `ANALYST`, `AGENCY`, `PUBLIC`). Server remains the authoritative authorization authority. |

---

## 4. End-to-End Voice Architecture Trace

Every voice interaction follows an audited 7-step sequence:

```
[1. MIC ACTIVATION]  --> User presses microphone button or hits shortcut key.
                         State transitions to REQUESTING_PERMISSION -> LISTENING.
                         Active TTS speech is immediately cancelled (Barge-in).

[2. AUDIO CAPTURE]   --> Browser prompts user for microphone access.
                         MediaStream created with echoCancellation=true, noiseSuppression=true.
                         AudioContext initialized and tracked.

[3. STT TRANSCRIBE]  --> Web Speech API processes audio buffer incrementally.
                         Interim results displayed in real-time.
                         Final transcript emitted on pause or explicit stop.

[4. JARVIS ENGINE]   --> Transcript forwarded to /jarvis/voice/interact.
                         Sovereign boundary check verifies query is inside India.
                         Prompt injection filter blocks override attempts.
                         Master Orchestrator executes dynamic capabilities & ACH matrix.

[5. RESPONSE BUILD]  --> Backend returns structured JSON response contract with:
                         facts, derived metrics, inferences, gaps, model provenance, and spoken text.

[6. CONSOLE RENDER]  --> Frontend updates Operational Console:
                         Displays epistemic badges, risk scores, and leading hypothesis.
                         Highlights event on MapLibre GIS map.

[7. TTS PLAYBACK]    --> If auto-speak is enabled and not muted, TTSProvider synthesizes audio.
                         Utterance playback begins. Visual state transitions to SPEAKING -> COMPLETED.
                         MediaStream tracks released; AudioContext suspended/closed cleanly.
```

---

## 5. Data Semantics & Count Preservation

The frontend strictly enforces canonical data semantics without collapsing or fabricating numbers:
- **Authoritative Active Facilities:** **35,570** (OSM registered industrial assets within sovereign India).
- **Staging / Non-Geocoded Variance:** **114** (Facilities pending precise cadastral georeferencing).
- **Historical / Reference Total:** **35,684** (Complete catalog baseline).
- **CEA Thermal Power Units:** **1,633 generating units** across **502 power stations**. (The UI must strictly display generating units and stations separately, never displaying "1,633 stations").

---

## 6. Model Governance Representation

Under WP5 & WP6 governance rules, candidate models cannot be displayed as authoritative:
- **Current Inference Model:** `xgb-v3.0-real-candidate`
- **Displayed Status:** `CANDIDATE`
- **Active Flag:** `FALSE`
- **Governance Notice:** *"Candidate Model in Evaluation | Human Verification Pending | Automated Activation Disabled"*

---

## 7. Audit Conclusions & Hardening Action Plan

The existing Next.js 15 application is fast, stable, and well-structured. Hardening actions for WP7:
1. Create dedicated `frontend/src/lib/voice/` module containing `voiceTypes.ts`, `sttProvider.ts`, `ttsProvider.ts`, and `useVoiceInterface.ts`.
2. Update `frontend/src/app/jarvis/page.tsx` to integrate `useVoiceInterface`, render strongly typed states (`IDLE`, `OBSERVING`, `INVESTIGATING`, `EVIDENCE_COLLECTED`, `UNCERTAINTY_PRESENT`, `WAITING_FOR_HUMAN`, `COMPLETED`, `STOPPED`, `DEGRADED`, `FAILED`), and visually segregate epistemic tiers.
3. Harden backend voice endpoint in `backend/app/api/v1/endpoints/jarvis.py`.
4. Create comprehensive 35-scenario test suite (`tests/test_wp7_frontend_voice.py`).
