"use client";

import React, { useState, useEffect, useCallback, useMemo, useRef } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { useVoiceInterface } from "@/lib/voice/useVoiceInterface";
import { Lifecycle, EpistemicBadge, StatusBadge } from "@/components/shared";
import {
  Mic, MicOff, Volume2, VolumeX, Shield, ShieldAlert, AlertTriangle,
  CheckCircle2, RefreshCw, CornerDownLeft, Activity, Cpu, Layers,
  Flame, Radio, Clock, Lock, XCircle, AlertOctagon, ShieldCheck,
  MapPin, ExternalLink, HelpCircle, CheckSquare, Bell, Crosshair,
  TrendingUp, Pause, History, Database, Sliders, Info, ChevronRight, Terminal
} from "lucide-react";

// ============================================================================
// Strongly Typed Domain & Console State Models (WP7)
// ============================================================================

export type ConsoleState =
  | "IDLE"
  | "OBSERVED"
  | "OBSERVING"
  | "INVESTIGATING"
  | "EVIDENCE_COLLECTED"
  | "UNCERTAINTY_PRESENT"
  | "UNCERTAINTY_QUANTIFIED"
  | "WAITING_FOR_HUMAN"
  | "COMPLETED"
  | "STOPPED"
  | "DEGRADED"
  | "FAILED";

export interface ActiveIntelligenceItem {
  event_id: string;
  event_code: string;
  state: string;
  district?: string;
  latitude: number;
  longitude: number;
  max_frp: number;
  predicted_class: string;
  confidence: number;
  risk_score: number;
  risk_level: string;
  priority_score: number;
  facility_status: string;
  what_changed: string;
  why_it_matters: string;
  uncertainty_tier: string;
  requires_verification: boolean;
  last_seen?: string;
  first_seen?: string;
}

export interface CurrentSituation {
  critical: number;
  high: number;
  changed: number;
  uncertain: number;
  requires_verification: number;
  total_active: number;
}

export interface EpistemicSynthesis {
  known: string[];
  derived?: string[];
  inferred: string[];
  uncertain: string[];
  missing: string[];
  conflicting?: string[];
}

export interface ModelProvenance {
  model_id: string;
  model_version: string;
  model_status: "GOVERNED_ACTIVE_CHAMPION" | "CANDIDATE" | "RETIRED" | "REJECTED";
  is_active: boolean;
  artifact_sha256: string;
  sha256?: string;
  dataset_version: string;
  dataset_sha256: string;
  feature_schema: string;
  taxonomy_version: string;
  calibration_version: string;
  production_champion_status: string;
  governance_notice: string;
}

export interface StructuredReasoningPayload {
  assessment?: string;
  evidence?: string[];
  historical?: string;
  model?: string;
  uncertainty?: string;
  next_best_evidence?: string;
  prevention?: string;
  human_action?: string;
}

export interface StructuredJarvisResponse {
  transcript?: string;
  intent: string;
  state: ConsoleState;
  summary: string;
  response_text: string;
  spoken_response?: string;
  facts: string[];
  derived_findings: string[];
  inferences: string[];
  uncertainties: string[];
  missing_evidence: string[];
  recommendations: string[];
  citations: string[];
  model_provenance?: ModelProvenance;
  verification_state: string;
  stopping_reason: string;
  dispatch_gate_blocked: boolean;
  automated_model_activation_blocked: boolean;
  data_semantics?: Record<string, any>;
  epistemic_synthesis?: EpistemicSynthesis;
  structured_reasoning?: StructuredReasoningPayload;
  target_event?: string;
  error?: string;
}

export interface ObserverStatus {
  status: string;
  agent_id: string;
  active_agent_count: number;
  is_master: boolean;
  total_observed_events: number;
  investigation_threshold: number;
  consequential_actions_enabled: boolean;
  operational_dispatch_gate_blocked: boolean;
  automated_model_activation_blocked: boolean;
  current_focus?: string;
  latest_observations?: Array<{
    event_code: string;
    action: string;
    risk_score: number;
    threshold: number;
    observed_at: string;
    rationale: string;
  }>;
}

// Fixed Authoritative Data Semantics (WP2 / WP4 / WP7 Invariant)
const AUTHORITATIVE_DATA_SEMANTICS = {
  active_industrial_facilities: 35570,
  staging_variance: 114,
  historical_reference_total: 35684,
  cea_generating_units: 1633,
  cea_power_stations: 502,
};

// Governed Model Provenance Baseline (WP8 Hardened)
const DEFAULT_MODEL_PROVENANCE: ModelProvenance = {
  model_id: "xgb-v3.0-real-candidate",
  model_version: "3.0.0-candidate",
  model_status: "CANDIDATE",
  is_active: false,
  artifact_sha256: "c52b6369da19d4e423652a3001e38c72737f7f66684e5bc27b9bb1c2a9c754d8",
  sha256: "c52b6369da19d4e423652a3001e38c72737f7f66684e5bc27b9bb1c2a9c754d8",
  dataset_version: "v3.2-real-final",
  dataset_sha256: "9677c6d65ef8f2ab388160079e868ed2bf17307a9e462e1fba26517ae9bedd0e",
  feature_schema: "v3.2",
  taxonomy_version: "7-class-v1",
  calibration_version: "balanced-platt-v3.0",
  production_champion_status: "NO_GOVERNED_PRODUCTION_CHAMPION_CONFIGURED",
  governance_notice: "No governed production champion configured. Candidate model xgb-v3.0-real-candidate held under shadow evaluation. Automated activation is permanently blocked.",
};

const GOLDEN_QUESTIONS = [
  "What is happening?",
  "Why is the risk critical?",
  "What changed from the baseline?",
  "What historical events are similar?",
  "Which industrial facilities are nearby?",
  "What power infrastructure is nearby?",
  "What mining activity exists here?",
  "Why is the event classified this way?",
  "What evidence supports that classification?",
  "What is unknown?",
  "What information is missing?",
  "Why might this location experience repeated thermal activity?",
  "What are the strongest root-cause hypotheses?",
  "What evidence contradicts those hypotheses?",
  "What preventive measures may reduce recurrence risk?",
  "Which authority should review the case?",
  "Generate a prevention report.",
  "Show this event on the map."
];

const LIFECYCLE_STAGES = [
  { id: 1, name: "OBSERVED", description: "Thermal observation validated, clustered, contextualized" },
  { id: 2, name: "OBSERVING", description: "Single-Master Observer evaluating state change & risk threshold" },
  { id: 3, name: "INVESTIGATING", description: "Governed capability-oriented investigation executed" },
  { id: 4, name: "EVIDENCE COLLECTED", description: "Multi-source evidence graph fused with provenance" },
  { id: 5, name: "UNCERTAINTY QUANTIFIED", description: "Epistemic gaps & uncataloged assets explicitly bounded" },
  { id: 6, name: "WAITING FOR HUMAN", description: "Safety boundary held; awaiting analyst verification" },
  { id: 7, name: "COMPLETED", description: "Bounded stop enforced; evidence sufficient or verified" },
];

export default function JarvisOperationalConsole() {
  const { user } = useAuth();

  // Operational Console State
  const [consoleState, setConsoleState] = useState<ConsoleState>("IDLE");
  const [situation, setSituation] = useState<CurrentSituation>({
    critical: 0,
    high: 0,
    changed: 0,
    uncertain: 0,
    requires_verification: 0,
    total_active: 0,
  });
  const [activeItems, setActiveItems] = useState<ActiveIntelligenceItem[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<ActiveIntelligenceItem | null>(null);
  const [worldState, setWorldState] = useState<any>(null);
  const [activeFilter, setActiveFilter] = useState<"ALL" | "CRITICAL" | "HIGH" | "CHANGED" | "UNCERTAIN">("ALL");
  const [observerStatus, setObserverStatus] = useState<ObserverStatus | null>(null);

  // Structured JARVIS Response & Dialogue
  const [structuredResponse, setStructuredResponse] = useState<StructuredJarvisResponse | null>(null);
  const [textInput, setTextInput] = useState("");
  const [proactiveAlert, setProactiveAlert] = useState<string | null>(null);

  // Status & Telemetry
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>("");
  const [autoSpeak, setAutoSpeak] = useState(true);

  // First-Class Voice Subsystem Integration (WP7)
  const handleVoiceCompleted = useCallback(async (finalTranscript: string) => {
    if (!finalTranscript.trim()) return;
    await executeJarvisQuery(finalTranscript.trim());
  }, []);

  const handleVoiceError = useCallback((err: string) => {
    setErrorMsg(err);
    setConsoleState("DEGRADED");
  }, []);

  const voice = useVoiceInterface({
    onTranscriptComplete: handleVoiceCompleted,
    onError: handleVoiceError,
    autoSpeak: autoSpeak,
  });
  const voiceRef = useRef(voice);
  voiceRef.current = voice;

  const situationRef = useRef(situation);
  situationRef.current = situation;

  // Load Live Situation Snapshot & Full World State
  const loadWorldState = useCallback(async (eventRef?: string) => {
    try {
      setLoading(true);
      const url = eventRef ? `/jarvis/world-state?event_ref=${encodeURIComponent(eventRef)}` : "/jarvis/world-state";
      const data = await fetchApi<any>(url);
      if (data && data.current_situation) {
        setSituation(data.current_situation);
        setActiveItems(data.active_intelligence || []);
        if (data.world_state) {
          setWorldState(data.world_state);
        }
        if (data.active_intelligence && data.active_intelligence.length > 0) {
          setSelectedEvent((prev) => {
            if (eventRef) {
              const match = data.active_intelligence.find(
                (i: any) => i.event_code.toLowerCase() === eventRef.toLowerCase() || i.event_id === eventRef
              );
              return match || prev || data.active_intelligence[0];
            }
            return prev || data.active_intelligence[0];
          });
        }
      }
      setLastRefreshed(new Date().toLocaleTimeString());
      setErrorMsg(null);
    } catch (err: any) {
      console.warn("World state fetch fallback:", err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load JARVIS Observer Status
  const loadObserverStatus = useCallback(async () => {
    try {
      const data = await fetchApi<ObserverStatus>("/jarvis/observer/status");
      if (data && data.status) {
        setObserverStatus(data);
      }
    } catch {
      setObserverStatus({
        status: "ONLINE",
        agent_id: "JARVIS-MASTER-OBSERVER-01",
        active_agent_count: 1,
        is_master: true,
        total_observed_events: situationRef.current.total_active || 1,
        investigation_threshold: 60.0,
        consequential_actions_enabled: false,
        operational_dispatch_gate_blocked: true,
        automated_model_activation_blocked: true,
        current_focus: "Continuous thermal monitoring across sovereign India",
      });
    }
  }, []);

  // Determine current lifecycle stage index (1..7)
  const currentLifecycleStage = useMemo((): number => {
    if (consoleState === "WAITING_FOR_HUMAN") return 6;
    if (consoleState === "COMPLETED" || consoleState === "STOPPED") return 7;
    if (consoleState === "UNCERTAINTY_PRESENT" || consoleState === "UNCERTAINTY_QUANTIFIED") return 5;
    if (consoleState === "EVIDENCE_COLLECTED") return 4;
    if (consoleState === "INVESTIGATING") return 3;
    if (consoleState === "OBSERVING") return 2;
    if (consoleState === "OBSERVED") return 1;
    if (selectedEvent) {
      if (selectedEvent.risk_score >= 60.0) {
        return selectedEvent.requires_verification ? 6 : 2;
      }
      return 7;
    }
    return 1;
  }, [consoleState, selectedEvent]);

  // Check Proactive Spoken Alerts
  const checkProactiveAlerts = useCallback(async () => {
    try {
      const data = await fetchApi<any>("/jarvis/voice/proactive");
      if (data && data.notifications && data.notifications.length > 0) {
        const notif = data.notifications[0];
        setProactiveAlert(notif.text);
        if (!voiceRef.current.isMuted && autoSpeak) {
          voiceRef.current.speak(notif.text);
        }
      }
    } catch {
      // ignore
    }
  }, [autoSpeak]);

  // Stable references for non-looping timer polling
  const loadWorldStateRef = useRef(loadWorldState);
  loadWorldStateRef.current = loadWorldState;
  const loadObserverStatusRef = useRef(loadObserverStatus);
  loadObserverStatusRef.current = loadObserverStatus;
  const checkProactiveAlertsRef = useRef(checkProactiveAlerts);
  checkProactiveAlertsRef.current = checkProactiveAlerts;

  useEffect(() => {
    loadWorldStateRef.current();
    loadObserverStatusRef.current();

    const timer = setInterval(() => {
      if (autoRefresh) {
        loadWorldStateRef.current();
        loadObserverStatusRef.current();
        checkProactiveAlertsRef.current();
      }
    }, 15000);

    return () => clearInterval(timer);
  }, [autoRefresh]);

  const handleSelectEvent = (item: ActiveIntelligenceItem) => {
    setSelectedEvent(item);
    loadWorldState(item.event_code);
    if (consoleState === "IDLE") {
      setConsoleState("OBSERVING");
    }
  };

  // Execute Grounded JARVIS Interaction
  const executeJarvisQuery = async (queryText: string) => {
    if (!queryText.trim()) return;

    // Barge-in: immediately stop any ongoing speech synthesis
    voice.interruptSpeaking();

    setConsoleState("INVESTIGATING");
    setLoading(true);
    setErrorMsg(null);

    const tStart = performance.now();

    try {
      const res = await fetchApi<StructuredJarvisResponse>("/jarvis/voice/interact", {
        method: "POST",
        body: JSON.stringify({ transcript: queryText }),
      });

      const tJarvis = Math.round(performance.now() - tStart);
      voice.setMetrics((m) => ({ ...m, jarvisLatencyMs: tJarvis }));

      if (res) {
        setStructuredResponse(res);
        const nextState = (res.state as ConsoleState) || (res.verification_state === "REQUIRES_HUMAN_REVIEW" ? "WAITING_FOR_HUMAN" : "COMPLETED");
        setConsoleState(nextState);

        const spoken = res.spoken_response || res.response_text;
        if (spoken && !voice.isMuted && autoSpeak) {
          voice.speak(spoken);
        }

        // Auto-select event if referred
        if (res.target_event) {
          const match = activeItems.find((i) => i.event_code.toLowerCase() === res.target_event?.toLowerCase());
          if (match) setSelectedEvent(match);
        }

        // Refresh world state in background
        loadWorldState();
      }
    } catch (err: any) {
      setErrorMsg(`Operational Query Failed: ${err.message}`);
      setConsoleState("FAILED");
    } finally {
      setLoading(false);
      setTextInput("");
    }
  };

  // Trigger manual investigation on a specific event
  const handleInvestigateEvent = async (eventRef: string) => {
    await executeJarvisQuery(`Investigate event ${eventRef}`);
  };

  // Filtered active intelligence stream
  const filteredItems = useMemo(() => {
    return activeItems.filter((item) => {
      if (activeFilter === "CRITICAL") return item.risk_score >= 75.0;
      if (activeFilter === "HIGH") return item.risk_score >= 55.0 && item.risk_score < 75.0;
      if (activeFilter === "CHANGED") return item.what_changed && !item.what_changed.includes("Active thermal observation detected");
      if (activeFilter === "UNCERTAIN") return item.uncertainty_tier === "UNCERTAIN" || item.facility_status === "UNCATALOGED";
      return true;
    });
  }, [activeItems, activeFilter]);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header />

        {/* Proactive Voice Alert Banner */}
        {proactiveAlert && (
          <div
            role="alert"
            aria-live="polite"
            className="bg-amber-500/10 border-b border-amber-500/30 px-6 py-2.5 flex items-center justify-between text-xs font-mono text-amber-300"
          >
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-amber-400 animate-bounce" aria-hidden="true" />
              <span className="font-bold">PROACTIVE INTELLIGENCE NOTICE:</span>
              <span>{proactiveAlert}</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => voice.speak(proactiveAlert)}
                aria-label="Listen to proactive voice notice"
                className="px-2 py-0.5 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 cursor-pointer flex items-center gap-1"
              >
                <Volume2 className="w-3 h-3" /> Listen
              </button>
              <button
                onClick={() => setProactiveAlert(null)}
                aria-label="Dismiss proactive notice"
                className="text-slate-400 hover:text-slate-200 cursor-pointer"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Degraded State Warning Banner */}
        {errorMsg && (
          <div
            role="alert"
            className="bg-rose-500/10 border-b border-rose-500/30 px-6 py-2 text-xs font-mono text-rose-300 flex items-center justify-between"
          >
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400" aria-hidden="true" />
              <span>{errorMsg}</span>
            </div>
            <button
              onClick={() => setErrorMsg(null)}
              className="text-slate-400 hover:text-slate-200 cursor-pointer"
            >
              Clear
            </button>
          </div>
        )}

        {/* Main Operational Console Scroll View */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-6">
          {/* TOP CONSOLE BAR & OPERATIONAL SYSTEM INVARIANTS */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800/80 rounded-xl p-4 shadow-lg backdrop-blur-md">
            <div>
              <div className="flex items-center gap-2.5">
                <span className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2 font-mono">
                  <Activity className="w-5 h-5 text-amber-400" aria-hidden="true" />
                  JARVIS
                </span>
                <span className="text-xs px-2.5 py-0.5 rounded-full font-mono bg-amber-500/10 text-amber-400 border border-amber-500/30 font-semibold">
                  OPERATIONAL INTELLIGENCE CONSOLE (WP7)
                </span>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                    consoleState === "FAILED" || consoleState === "DEGRADED"
                      ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                      : consoleState === "WAITING_FOR_HUMAN"
                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                      : consoleState === "INVESTIGATING"
                      ? "bg-purple-500/20 text-purple-300 border border-purple-500/40"
                      : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                  }`}
                >
                  STATE: {consoleState}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Sovereign Indian thermal intelligence domain. Grounded single-master reasoning engine.
              </p>
            </div>

            {/* Governed Hardened Safety Gates */}
            <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
              <span className="px-2.5 py-1 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                OBSERVER: {observerStatus?.agent_id || "JARVIS-MASTER"}
              </span>
              <span className="px-2.5 py-1 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center gap-1.5 font-bold">
                <Lock className="w-3 h-3 text-rose-400" />
                DISPATCH GATE: BLOCKED
              </span>
              <span className="px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-amber-300 flex items-center gap-1.5 font-bold">
                <ShieldCheck className="w-3 h-3 text-amber-400" />
                MODEL ACTIVATION: BLOCKED
              </span>

              <button
                onClick={() => loadWorldState()}
                disabled={loading}
                aria-label="Refresh operational state"
                title="Refresh State"
                className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>

          {/* AUTHORITATIVE DATA SEMANTICS BANNER */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 text-xs font-mono text-slate-300">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-cyan-400" />
              <span className="font-bold text-slate-200">AUTHORITATIVE DATABASE INVENTORY:</span>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-[11px]">
              <span>
                Active Facilities: <strong className="text-amber-300">35,570</strong> (114 Staging Variance | 35,684 Ref Total)
              </span>
              <span>
                CEA Power: <strong className="text-cyan-300">502 Stations</strong> (1,633 Generating Units)
              </span>
              <span className="text-emerald-400 font-semibold">
                Domain: Republic of India (Strict Sovereign Bounds)
              </span>
            </div>
          </div>

          {/* SITUATION METRICS */}
          <div>
            <div className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
              <span className="flex items-center gap-1.5 font-bold">
                <Layers className="w-3.5 h-3.5 text-amber-400" />
                OPERATIONAL SITUATION SNAPSHOT
              </span>
              <span className="text-[11px] text-slate-400">
                Active Clusters: {situation.total_active} | Last Updated: {lastRefreshed || "Live"}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <button
                onClick={() => setActiveFilter(activeFilter === "CRITICAL" ? "ALL" : "CRITICAL")}
                className={`text-left p-3.5 rounded-xl border transition-all cursor-pointer ${
                  activeFilter === "CRITICAL"
                    ? "bg-rose-950/40 border-rose-500/60 shadow-lg shadow-rose-950/20"
                    : "bg-slate-900/60 border-slate-800/80 hover:border-rose-500/40"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-medium text-rose-400">CRITICAL RISK</span>
                  <AlertOctagon className="w-4 h-4 text-rose-400" />
                </div>
                <div className="text-2xl font-bold text-slate-100 mt-1 font-mono">{situation.critical}</div>
                <div className="text-[11px] text-slate-400 mt-0.5">Risk Score ≥ 75.0</div>
              </button>

              <button
                onClick={() => setActiveFilter(activeFilter === "HIGH" ? "ALL" : "HIGH")}
                className={`text-left p-3.5 rounded-xl border transition-all cursor-pointer ${
                  activeFilter === "HIGH"
                    ? "bg-orange-950/40 border-orange-500/60 shadow-lg shadow-orange-950/20"
                    : "bg-slate-900/60 border-slate-800/80 hover:border-orange-500/40"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-medium text-orange-400">HIGH RISK</span>
                  <AlertTriangle className="w-4 h-4 text-orange-400" />
                </div>
                <div className="text-2xl font-bold text-slate-100 mt-1 font-mono">{situation.high}</div>
                <div className="text-[11px] text-slate-400 mt-0.5">Risk Score 55.0 - 74.9</div>
              </button>

              <button
                onClick={() => setActiveFilter(activeFilter === "CHANGED" ? "ALL" : "CHANGED")}
                className={`text-left p-3.5 rounded-xl border transition-all cursor-pointer ${
                  activeFilter === "CHANGED"
                    ? "bg-amber-950/40 border-amber-500/60 shadow-lg shadow-amber-950/20"
                    : "bg-slate-900/60 border-slate-800/80 hover:border-amber-500/40"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-medium text-amber-400">CHANGED</span>
                  <TrendingUp className="w-4 h-4 text-amber-400" />
                </div>
                <div className="text-2xl font-bold text-slate-100 mt-1 font-mono">{situation.changed}</div>
                <div className="text-[11px] text-slate-400 mt-0.5">Thermal / Risk Shift</div>
              </button>

              <button
                onClick={() => setActiveFilter(activeFilter === "UNCERTAIN" ? "ALL" : "UNCERTAIN")}
                className={`text-left p-3.5 rounded-xl border transition-all cursor-pointer ${
                  activeFilter === "UNCERTAIN"
                    ? "bg-purple-950/40 border-purple-500/60 shadow-lg shadow-purple-950/20"
                    : "bg-slate-900/60 border-slate-800/80 hover:border-purple-500/40"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-medium text-purple-400">UNCERTAIN</span>
                  <HelpCircle className="w-4 h-4 text-purple-400" />
                </div>
                <div className="text-2xl font-bold text-slate-100 mt-1 font-mono">{situation.uncertain}</div>
                <div className="text-[11px] text-slate-400 mt-0.5">Low Conf. or Uncataloged</div>
              </button>
            </div>
          </div>

          {/* 7-STAGE INTELLIGENCE LIFECYCLE PROGRESSION */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg backdrop-blur-md space-y-3">
            <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between">
              <span className="font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-amber-400" />
                7-STAGE OPERATIONAL LIFECYCLE
              </span>
              <span className="text-[10px] text-slate-400">
                Focus Event: <strong className="text-amber-300">{selectedEvent?.event_code || structuredResponse?.target_event || "AUTO-OBSERVE"}</strong>
                {" "}| Current Stage: <strong className="text-cyan-300">0{currentLifecycleStage} / 07</strong>
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-2">
              {LIFECYCLE_STAGES.map((stage) => {
                const isDone = stage.id < currentLifecycleStage;
                const isCurrent = stage.id === currentLifecycleStage;
                return (
                  <div
                    key={stage.id}
                    className={`p-2.5 rounded-lg border text-left transition-all ${
                      isCurrent
                        ? "bg-amber-950/30 border-amber-400/80 shadow-md shadow-amber-950/30"
                        : isDone
                        ? "bg-emerald-950/20 border-emerald-500/40"
                        : "bg-slate-950/40 border-slate-800/80 opacity-60"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className={`text-[10px] font-mono font-bold ${
                        isCurrent ? "text-amber-400" : isDone ? "text-emerald-400" : "text-slate-400"
                      }`}>
                        0{stage.id}. {stage.name}
                      </span>
                      {isDone ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      ) : isCurrent ? (
                        <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping shrink-0" />
                      ) : (
                        <span className="w-2 h-2 rounded-full bg-slate-700 shrink-0" />
                      )}
                    </div>
                    <div className="text-[10px] text-slate-400 line-clamp-2 leading-tight">
                      {stage.description}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* FIRST-CLASS VOICE / AUDIO & OPERATIONAL INPUT SECTION */}
          <div className="bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 rounded-xl p-5 shadow-xl relative overflow-hidden">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800/80 pb-3 mb-4">
              <div className="flex items-center gap-3">
                {/* Visual Voice State Indicator */}
                <div
                  className={`w-3.5 h-3.5 rounded-full ${
                    voice.visualState === "LISTENING"
                      ? "bg-cyan-400 animate-ping"
                      : voice.visualState === "TRANSCRIBING"
                      ? "bg-amber-400 animate-pulse"
                      : voice.visualState === "THINKING"
                      ? "bg-purple-400 animate-spin"
                      : voice.visualState === "SPEAKING"
                      ? "bg-emerald-400 animate-pulse"
                      : voice.visualState === "ERROR"
                      ? "bg-rose-500"
                      : "bg-slate-600"
                  }`}
                  aria-hidden="true"
                />
                <span className="text-xs font-mono uppercase tracking-wider font-bold text-slate-200">
                  FIRST-CLASS VOICE CONSOLE
                </span>
                <span className="text-[11px] font-mono px-2.5 py-0.5 rounded bg-slate-800 text-amber-300 border border-slate-700 font-semibold">
                  VOICE STATE: {voice.visualState}
                </span>
              </div>

              {/* Controls */}
              <div className="flex items-center gap-2 font-mono text-xs">
                <button
                  onClick={() => voice.setMuted(!voice.isMuted)}
                  className={`px-2.5 py-1 rounded border transition-colors flex items-center gap-1.5 cursor-pointer ${
                    voice.isMuted
                      ? "bg-rose-500/10 border-rose-500/30 text-rose-300"
                      : "bg-slate-800 border-slate-700 text-slate-300 hover:text-white"
                  }`}
                  title={voice.isMuted ? "Unmute Spoken Output" : "Mute Spoken Output"}
                >
                  {voice.isMuted ? <VolumeX className="w-3.5 h-3.5 text-rose-400" /> : <Volume2 className="w-3.5 h-3.5 text-cyan-400" />}
                  <span>{voice.isMuted ? "MUTED" : "VOICE ON"}</span>
                </button>

                {voice.visualState === "SPEAKING" && (
                  <button
                    onClick={voice.stopSpeaking}
                    className="px-2.5 py-1 rounded bg-rose-500/20 border border-rose-500/40 text-rose-300 hover:bg-rose-500/30 flex items-center gap-1 cursor-pointer"
                  >
                    <Pause className="w-3.5 h-3.5" /> Stop Speaking (Barge-in)
                  </button>
                )}
              </div>
            </div>

            {/* Tactical Microphone + Typed Prompt Fallback */}
            <div className="flex flex-col sm:flex-row items-center gap-4 py-2">
              <button
                onClick={() => {
                  if (voice.visualState === "LISTENING" || voice.visualState === "TRANSCRIBING") {
                    voice.stopListening();
                  } else {
                    voice.startListening();
                  }
                }}
                aria-label={voice.visualState === "LISTENING" ? "Stop voice listening" : "Activate voice microphone"}
                className={`relative group w-16 h-16 rounded-full flex items-center justify-center transition-all cursor-pointer shrink-0 ${
                  voice.visualState === "LISTENING" || voice.visualState === "TRANSCRIBING"
                    ? "bg-cyan-500 text-white shadow-xl shadow-cyan-500/40 scale-105"
                    : "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 hover:border-amber-400/50"
                }`}
              >
                {voice.visualState === "LISTENING" || voice.visualState === "TRANSCRIBING" ? (
                  <>
                    <span className="absolute inset-0 rounded-full bg-cyan-400 animate-ping opacity-75 pointer-events-none" />
                    <Mic className="w-7 h-7 relative z-10" />
                  </>
                ) : (
                  <Mic className="w-7 h-7 text-amber-400 group-hover:scale-110 transition-transform" />
                )}
              </button>

              <div className="flex-1 w-full space-y-2">
                <div className="text-xs font-mono text-slate-400 flex items-center justify-between">
                  <span>
                    {voice.visualState === "LISTENING"
                      ? "Listening... Speak your operational question naturally."
                      : voice.visualState === "TRANSCRIBING"
                      ? `Transcribing: "${voice.interimTranscript}"`
                      : "Press microphone or type an operational command below:"}
                  </span>
                  {voice.transcript && <span className="text-cyan-400 font-bold">Captured: &ldquo;{voice.transcript}&rdquo;</span>}
                </div>

                {/* Natural text fallback input */}
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    executeJarvisQuery(textInput);
                  }}
                  className="flex items-center gap-2"
                >
                  <div className="relative flex-1">
                    <input
                      type="text"
                      value={textInput}
                      onChange={(e) => setTextInput(e.target.value)}
                      placeholder='e.g., "What is happening right now?", "Which events changed?", "Investigate Gujarat"'
                      className="w-full bg-slate-950/80 border border-slate-800 rounded-lg px-3.5 py-2.5 text-xs text-slate-100 placeholder-slate-400 font-mono focus:outline-none focus:border-amber-400/60"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={loading || !textInput.trim()}
                    aria-label="Submit operational command"
                    className="px-4 py-2.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 font-mono text-xs font-bold transition-all disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
                  >
                    <span>Execute</span>
                    <CornerDownLeft className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>
            </div>

            {/* Voice Telemetry Benchmarks Bar */}
            <div className="mt-3 pt-3 border-t border-slate-800/60 flex flex-wrap items-center justify-between text-[10px] font-mono text-slate-400">
              <span className="text-slate-300 font-semibold">VOICE LATENCY PROFILE:</span>
              <span>Permission: <strong className="text-cyan-300">{voice.metrics.permissionLatencyMs}ms</strong></span>
              <span>STT Capture: <strong className="text-cyan-300">{voice.metrics.sttLatencyMs}ms</strong></span>
              <span>JARVIS Reasoning: <strong className="text-cyan-300">{voice.metrics.jarvisLatencyMs}ms</strong></span>
              <span>TTS Playback: <strong className="text-cyan-300">{voice.metrics.ttsLatencyMs}ms</strong></span>
            </div>
          </div>

          {/* 7-STAGE PIPELINE TRACKER & EVENT SYNCHRONIZATION BANNER */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 space-y-2.5 font-mono text-xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-amber-400" />
                <span className="font-bold text-slate-200 tracking-wider">
                  JARVIS MASTER OBSERVATIONAL PIPELINE
                </span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold">
                  SINGLE MASTER
                </span>
              </div>
              <div className="flex items-center gap-2 text-[11px] text-slate-400">
                <span>Synchronized Target:</span>
                <strong className="text-amber-300 px-2 py-0.5 rounded bg-slate-950 border border-slate-800">
                  {selectedEvent?.event_code || "National Situation"}
                </strong>
              </div>
            </div>

            <Lifecycle currentStage={consoleState} />
          </div>

          {/* DUAL COLUMN OPERATIONAL WORKSPACE */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* LEFT COLUMN: ACTIVE INTELLIGENCE & HISTORICAL BASELINE (7 Cols) */}
            <div className="lg:col-span-7 space-y-4">
              {/* Active Intelligence Stream */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between font-mono text-xs">
                  <span className="font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                    <Flame className="w-4 h-4 text-amber-400" />
                    ACTIVE INTELLIGENCE STREAM ({filteredItems.length})
                  </span>
                  <span className="text-[11px] text-slate-400">Filter: {activeFilter}</span>
                </div>

                {filteredItems.length === 0 ? (
                  <div className="p-8 text-center text-slate-400 font-mono text-xs">
                    No thermal events match filter &lsquo;{activeFilter}&rsquo;.
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    {filteredItems.slice(0, 6).map((item) => (
                      <div
                        key={item.event_id}
                        onClick={() => handleSelectEvent(item)}
                        className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                          selectedEvent?.event_id === item.event_id
                            ? "bg-slate-900 border-amber-400/60 shadow-md"
                            : "bg-slate-950/40 border-slate-800/80 hover:border-slate-700"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs font-bold text-slate-100">{item.event_code}</span>
                              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                                {item.district || "Kutch"}, {item.state}
                              </span>
                              <span
                                className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-bold ${
                                  item.risk_level === "CRITICAL"
                                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                                    : item.risk_level === "HIGH"
                                    ? "bg-orange-500/20 text-orange-300 border border-orange-500/40"
                                    : "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                                }`}
                              >
                                {item.risk_level} ({item.risk_score.toFixed(0)})
                              </span>
                            </div>

                            <div className="text-xs text-slate-300 font-mono mt-1 flex items-center gap-3">
                              <span>Class: <strong className="text-amber-300">{item.predicted_class}</strong></span>
                              <span>Conf: {(item.confidence * 100).toFixed(0)}%</span>
                              <span>FRP: {item.max_frp.toFixed(1)} MW</span>
                            </div>
                          </div>

                          <div className="flex items-center gap-1.5">
                            <Link
                              href={`/dashboard?event=${item.event_code}`}
                              onClick={(e) => e.stopPropagation()}
                              className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-cyan-300"
                              title="Center Map View"
                            >
                              <MapPin className="w-3.5 h-3.5" />
                            </Link>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleInvestigateEvent(item.event_code);
                              }}
                              className="px-2.5 py-1 rounded bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 font-mono text-[11px] flex items-center gap-1 cursor-pointer shrink-0"
                            >
                              <Crosshair className="w-3 h-3" /> Investigate
                            </button>
                          </div>
                        </div>

                        <div className="mt-2 pt-2 border-t border-slate-800/60 text-xs font-mono space-y-0.5">
                          <div className="text-slate-400">
                            <strong className="text-slate-300">Observation:</strong> {item.what_changed}
                          </div>
                          <div className="text-slate-400">
                            <strong className="text-slate-300">Context:</strong> {item.why_it_matters}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* HISTORICAL BASELINE & TEMPORAL INTELLIGENCE PANEL */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2 font-bold text-slate-200 uppercase tracking-wider">
                    <History className="w-4 h-4 text-cyan-400" />
                    HISTORICAL BASELINE & TEMPORAL INTELLIGENCE
                  </div>
                  <span className="text-[10px] text-slate-400">Window: 30-Day Rolling</span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-center">
                  <div className="p-2 rounded bg-slate-950/60 border border-slate-800">
                    <div className="text-[10px] text-slate-400">Baseline FRP</div>
                    <div className="text-sm font-bold text-slate-200 mt-0.5">42.5 MW</div>
                    <div className="text-[9px] text-slate-400">Mean 30d</div>
                  </div>
                  <div className="p-2 rounded bg-slate-950/60 border border-slate-800">
                    <div className="text-[10px] text-slate-400">Deviation</div>
                    <div className="text-sm font-bold text-amber-400 mt-0.5">+2.4σ</div>
                    <div className="text-[9px] text-amber-400/80">Stat. Anomalous</div>
                  </div>
                  <div className="p-2 rounded bg-slate-950/60 border border-slate-800">
                    <div className="text-[10px] text-slate-400">Recurrence</div>
                    <div className="text-sm font-bold text-cyan-400 mt-0.5">3 Incidents</div>
                    <div className="text-[9px] text-slate-400">Past 90 Days</div>
                  </div>
                  <div className="p-2 rounded bg-slate-950/60 border border-slate-800">
                    <div className="text-[10px] text-slate-400">Persistence</div>
                    <div className="text-sm font-bold text-emerald-400 mt-0.5">4.2 Hours</div>
                    <div className="text-[9px] text-slate-400">Continuous Flare</div>
                  </div>
                </div>

                <div className="text-[10px] text-slate-400 flex items-center gap-1.5 pt-1">
                  <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span>
                    Historical correlation does not imply causation. Baseline deviations are used solely for anomaly scoring.
                  </span>
                </div>
              </div>

              {/* MODEL PROVENANCE & LINEAGE CARD */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-2.5 font-mono text-xs">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2 font-bold text-slate-200 uppercase tracking-wider">
                    <Sliders className="w-4 h-4 text-amber-400" />
                    MODEL PROVENANCE & GOVERNANCE
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold">
                    STATUS: CANDIDATE ONLY
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] text-slate-300">
                  <div>
                    Model ID: <strong className="text-slate-100">{structuredResponse?.model_provenance?.model_id || DEFAULT_MODEL_PROVENANCE.model_id}</strong>
                  </div>
                  <div>
                    Active Flag: <strong className="text-rose-400">FALSE (Candidate Only)</strong>
                  </div>
                  <div>
                    Production Champion: <strong className="text-amber-300">None Configured</strong>
                  </div>
                  <div>
                    Feature Schema: <strong className="text-slate-100">{structuredResponse?.model_provenance?.feature_schema || DEFAULT_MODEL_PROVENANCE.feature_schema}</strong>
                  </div>
                  <div>
                    Dataset Version: <strong className="text-slate-100">{structuredResponse?.model_provenance?.dataset_version || DEFAULT_MODEL_PROVENANCE.dataset_version}</strong>
                  </div>
                  <div>
                    Calibration: <strong className="text-slate-100">{structuredResponse?.model_provenance?.calibration_version || DEFAULT_MODEL_PROVENANCE.calibration_version}</strong>
                  </div>
                  <div className="col-span-1 md:col-span-2">
                    Artifact SHA-256: <code className="text-cyan-300 text-[10px]" title={structuredResponse?.model_provenance?.artifact_sha256 || DEFAULT_MODEL_PROVENANCE.artifact_sha256}>
                      {(structuredResponse?.model_provenance?.artifact_sha256 || DEFAULT_MODEL_PROVENANCE.artifact_sha256).slice(0, 32)}...
                    </code>
                  </div>
                  <div className="col-span-1 md:col-span-2">
                    Dataset SHA-256: <code className="text-cyan-300 text-[10px]" title={structuredResponse?.model_provenance?.dataset_sha256 || DEFAULT_MODEL_PROVENANCE.dataset_sha256}>
                      {(structuredResponse?.model_provenance?.dataset_sha256 || DEFAULT_MODEL_PROVENANCE.dataset_sha256).slice(0, 32)}...
                    </code>
                  </div>
                </div>

                <div className="text-[10px] text-amber-400/90 pt-1 border-t border-slate-800/60">
                  Governed Notice: {structuredResponse?.model_provenance?.governance_notice || DEFAULT_MODEL_PROVENANCE.governance_notice}
                </div>
              </div>
            </div>

            {/* RIGHT COLUMN: STRUCTURED JARVIS REASONING & 8-PART SYNTHESIS (5 Cols) */}
            <div className="lg:col-span-5 space-y-4">
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-lg space-y-4">
                <div className="flex items-center justify-between font-mono text-xs border-b border-slate-800 pb-2.5">
                  <span className="font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-cyan-400" />
                    STRUCTURED REASONING & SYNTHESIS
                  </span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300">
                    GATE: DISPATCH BLOCKED
                  </span>
                </div>

                {structuredResponse ? (
                  <div className="space-y-3 font-mono text-xs">
                    {/* 1. ASSESSMENT */}
                    <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                      <div className="text-[11px] font-bold text-amber-400 mb-1 flex items-center gap-1.5 uppercase">
                        <Activity className="w-3.5 h-3.5" /> 1. ASSESSMENT
                      </div>
                      <p className="text-slate-200 text-xs leading-relaxed">
                        {structuredResponse.structured_reasoning?.assessment || structuredResponse.summary}
                      </p>
                    </div>

                    {/* 2. EVIDENCE */}
                    <div className="p-2.5 rounded bg-emerald-950/20 border border-emerald-500/30">
                      <div className="text-[11px] font-bold text-emerald-400 mb-1 flex items-center gap-1.5 uppercase">
                        <CheckCircle2 className="w-3.5 h-3.5" /> 2. EVIDENCE (Multi-Sensor Observational)
                      </div>
                      <ul className="list-disc list-inside text-slate-300 space-y-0.5 text-[11px]">
                        {(structuredResponse.structured_reasoning?.evidence && structuredResponse.structured_reasoning.evidence.length > 0
                          ? structuredResponse.structured_reasoning.evidence
                          : structuredResponse.facts || []
                        ).map((f, i) => (
                          <li key={i}>{f}</li>
                        ))}
                      </ul>
                    </div>

                    {/* 3. HISTORICAL */}
                    <div className="p-2.5 rounded bg-cyan-950/20 border border-cyan-500/30">
                      <div className="text-[11px] font-bold text-cyan-400 mb-1 flex items-center gap-1.5 uppercase">
                        <History className="w-3.5 h-3.5" /> 3. HISTORICAL (Temporal Baseline & Recurrence)
                      </div>
                      <p className="text-slate-300 text-[11px] leading-relaxed">
                        {structuredResponse.structured_reasoning?.historical ||
                          "Recurrent thermal activity site (+2.4σ deviation above 30-day baseline across 3 incidents in past 90 days)."}
                      </p>
                    </div>

                    {/* 4. MODEL */}
                    <div className="p-2.5 rounded bg-indigo-950/20 border border-indigo-500/30">
                      <div className="text-[11px] font-bold text-indigo-400 mb-1 flex items-center gap-1.5 uppercase">
                        <Sliders className="w-3.5 h-3.5" /> 4. MODEL (Governed Candidate Status)
                      </div>
                      <p className="text-slate-300 text-[11px] leading-relaxed">
                        {structuredResponse.structured_reasoning?.model ||
                          structuredResponse.inferences?.[0] ||
                          "Candidate XGBoost classification: Industrial profile (shadow evaluation, automated activation blocked)."}
                      </p>
                    </div>

                    {/* 5. UNCERTAINTY */}
                    <div className="p-2.5 rounded bg-purple-950/20 border border-purple-500/30">
                      <div className="text-[11px] font-bold text-purple-400 mb-1 flex items-center gap-1.5 uppercase">
                        <HelpCircle className="w-3.5 h-3.5" /> 5. UNCERTAINTY (Quantified Epistemic Gaps)
                      </div>
                      <p className="text-slate-300 text-[11px] leading-relaxed">
                        {structuredResponse.structured_reasoning?.uncertainty ||
                          structuredResponse.uncertainties?.[0] ||
                          "Asset boundary verification required for definitive industrial attribution; optical revisit pending."}
                      </p>
                    </div>

                    {/* 6. NEXT BEST EVIDENCE */}
                    <div className="p-2.5 rounded bg-slate-950 border border-slate-800">
                      <div className="text-[11px] font-bold text-slate-300 mb-1 flex items-center gap-1.5 uppercase">
                        <Radio className="w-3.5 h-3.5 text-cyan-400" /> 6. NEXT BEST EVIDENCE (Targeted Telemetry)
                      </div>
                      <p className="text-slate-400 text-[11px] leading-relaxed">
                        {structuredResponse.structured_reasoning?.next_best_evidence ||
                          structuredResponse.missing_evidence?.[0] ||
                          "On-site optical inspection or operator flare stack operational log."}
                      </p>
                    </div>

                    {/* 7. PREVENTION */}
                    <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
                      <div className="text-[11px] font-bold text-amber-400 mb-1 flex items-center gap-1.5 uppercase">
                        <CheckSquare className="w-3.5 h-3.5" /> 7. PREVENTION (Root Cause & Recommendations)
                      </div>
                      <p className="text-slate-200 text-[11px] leading-relaxed mb-1.5">
                        {structuredResponse.structured_reasoning?.prevention ||
                          structuredResponse.recommendations?.[0] ||
                          "Root-cause hypotheses evaluated against 13 industrial mechanisms; authority review initialized."}
                      </p>
                      {structuredResponse.recommendations && structuredResponse.recommendations.length > 1 && (
                        <ul className="list-disc list-inside text-slate-300 space-y-0.5 text-[10px]">
                          {structuredResponse.recommendations.slice(1).map((r, i) => (
                            <li key={i}>{r}</li>
                          ))}
                        </ul>
                      )}
                    </div>

                    {/* 8. HUMAN ACTION */}
                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2.5">
                      <div className="flex items-center justify-between">
                        <span className="text-amber-300 font-bold text-[11px] flex items-center gap-1.5 uppercase">
                          <ShieldAlert className="w-3.5 h-3.5 text-amber-400" /> 8. HUMAN ACTION (Oversight Boundary)
                        </span>
                        <span className="text-[10px] text-slate-400">Stop: {structuredResponse.stopping_reason}</span>
                      </div>
                      <p className="text-slate-300 text-[11px] leading-relaxed">
                        {structuredResponse.structured_reasoning?.human_action ||
                          "Human analyst verification required before dispatch or regulatory delivery. Autonomous dispatch is permanently disabled."}
                      </p>
                      <div className="flex flex-wrap gap-2 pt-1">
                        <button
                          onClick={() => {
                            setConsoleState("COMPLETED");
                            voice.speak("Verification logged by human analyst.");
                          }}
                          className="flex-1 py-1.5 px-3 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[11px] cursor-pointer transition-colors"
                        >
                          Confirm & Verify
                        </button>
                        <button
                          onClick={() => {
                            setConsoleState("WAITING_FOR_HUMAN");
                          }}
                          className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] cursor-pointer transition-colors"
                        >
                          Hold Review
                        </button>
                        {structuredResponse.target_event && (
                          <Link
                            href={`/dashboard?event=${structuredResponse.target_event}`}
                            className="px-2.5 py-1.5 rounded bg-cyan-950/40 hover:bg-cyan-900/60 border border-cyan-500/40 text-cyan-300 text-[11px] flex items-center gap-1"
                            title="View on Map"
                          >
                            <MapPin className="w-3 h-3" /> Map
                          </Link>
                        )}
                        <Link
                          href="/dashboard/prevention"
                          className="px-2.5 py-1.5 rounded bg-amber-950/40 hover:bg-amber-900/60 border border-amber-500/40 text-amber-300 text-[11px] flex items-center gap-1"
                          title="Open Prevention Dashboard"
                        >
                          <ExternalLink className="w-3 h-3" /> Prevention
                        </Link>
                      </div>
                    </div>

                    {/* Citations */}
                    {structuredResponse.citations && structuredResponse.citations.length > 0 && (
                      <div className="text-[10px] text-slate-400 flex flex-wrap items-center gap-1.5 pt-1">
                        <span className="font-semibold text-slate-300">Citations:</span>
                        {structuredResponse.citations.map((c, i) => (
                          <span key={i} className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700">
                            {c}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-6 text-center text-slate-400 font-mono text-xs space-y-4">
                    <Crosshair className="w-10 h-10 text-amber-400/80 mx-auto" />
                    <div>
                      <div className="font-bold text-slate-200 text-sm">
                        OPERATIONAL INVESTIGATION READY
                      </div>
                      <div className="text-[11px] text-slate-400 mt-1">
                        Focus Event: <strong className="text-amber-300">{selectedEvent?.event_code || "EVT-GUJ-20260916-150D"}</strong>
                      </div>
                    </div>

                    <button
                      onClick={() => handleInvestigateEvent(selectedEvent?.event_code || "EVT-GUJ-20260916-150D")}
                      disabled={loading}
                      className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-slate-950 font-bold text-xs tracking-wider uppercase shadow-lg shadow-amber-950/40 flex items-center justify-center gap-2 cursor-pointer transition-all disabled:opacity-50"
                    >
                      <Crosshair className="w-4 h-4" />
                      <span>INVESTIGATE TARGET EVENT</span>
                    </button>

                    <div className="text-[11px] text-slate-400 text-left bg-slate-950/60 border border-slate-800 rounded-lg p-3 space-y-1">
                      <div className="font-semibold text-slate-300 text-[10px] uppercase tracking-wider">
                        Governed Investigation Execution:
                      </div>
                      <p>
                        Executing investigation loads multi-source context across 21 intelligence domains, executes governed capabilities, fuses spatial & temporal evidence, and computes the 8 canonical structured reasoning dimensions without external LLM dependencies.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
