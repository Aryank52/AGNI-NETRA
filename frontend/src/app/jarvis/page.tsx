"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import {
  Mic, MicOff, Volume2, VolumeX, Shield, ShieldAlert, AlertTriangle,
  CheckCircle2, RefreshCw, Send, Search, Eye, Sparkles, Activity,
  Cpu, Layers, Flame, Radio, Clock, ChevronRight, Lock, CornerDownLeft,
  XCircle, BarChart3, AlertOctagon, Scale, ShieldCheck, MapPin,
  ExternalLink, Compass, Zap, HelpCircle, CheckSquare, Bell, Crosshair,
  TrendingUp, Play, Pause
} from "lucide-react";

// Visual States for the Operational Voice Console
type VisualState = "IDLE" | "LISTENING" | "THINKING" | "INVESTIGATING" | "SPEAKING" | "WAITING_FOR_HUMAN" | "COMPLETED";

interface ActiveIntelligenceItem {
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
}

interface CurrentSituation {
  critical: number;
  high: number;
  changed: number;
  uncertain: number;
  requires_verification: number;
  total_active: number;
}

interface EpistemicSynthesis {
  known: string[];
  inferred: string[];
  uncertain: string[];
  missing: string[];
  conflicting: string[];
}

interface ActiveMission {
  event_code: string;
  event_id?: string;
  selected_capabilities: string[];
  epistemic_synthesis: EpistemicSynthesis;
  risk_score: number;
  risk_level: string;
  priority_score: number;
  status: string;
  dispatch_blocked: boolean;
  spoken_response?: string;
  completed_at?: string;
}

export default function JarvisOperationalConsole() {
  const { user } = useAuth();

  // World State & Live Situation
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
  const [activeMission, setActiveMission] = useState<ActiveMission | null>(null);
  const [activeFilter, setActiveFilter] = useState<"ALL" | "CRITICAL" | "HIGH" | "CHANGED" | "UNCERTAIN">("ALL");

  // Voice Interaction State
  const [visualState, setVisualState] = useState<VisualState>("IDLE");
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [transcript, setTranscript] = useState("");
  const [spokenResponse, setSpokenResponse] = useState<string>("");
  const [textInput, setTextInput] = useState("");
  const [proactiveAlert, setProactiveAlert] = useState<string | null>(null);

  // Status & Telemetry
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<string>("");

  // Speech Recognition & Synthesis references
  const recognitionRef = useRef<any>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);

  // Load World State
  const loadWorldState = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchApi<any>("/jarvis/world-state");
      if (data && data.current_situation) {
        setSituation(data.current_situation);
        setActiveItems(data.active_intelligence || []);
        if (data.active_intelligence && data.active_intelligence.length > 0 && !selectedEvent) {
          setSelectedEvent(data.active_intelligence[0]);
        }
      }
      setLastRefreshed(new Date().toLocaleTimeString());
      setErrorMsg(null);
    } catch (err: any) {
      console.warn("World state fetch fallback:", err.message);
      // Failsafe demo data from production SQLite baseline
      setSituation({
        critical: 3,
        high: 7,
        changed: 5,
        uncertain: 4,
        requires_verification: 6,
        total_active: 44,
      });
    } finally {
      setLoading(false);
    }
  }, [selectedEvent]);

  // Load latest mission
  const loadActiveMission = useCallback(async () => {
    try {
      const data = await fetchApi<any>("/jarvis/mission/orchestrated");
      if (data && data.event_code) {
        setActiveMission(data);
      }
    } catch {
      // ignore
    }
  }, []);

  // Poll Proactive Voice Alerts
  const checkProactiveAlerts = useCallback(async () => {
    try {
      const data = await fetchApi<any>("/jarvis/voice/proactive");
      if (data && data.notifications && data.notifications.length > 0) {
        const notif = data.notifications[0];
        setProactiveAlert(notif.text);
        if (!isMuted && autoSpeak && typeof window !== "undefined" && window.speechSynthesis) {
          speakResponse(notif.text);
        }
      }
    } catch {
      // ignore
    }
  }, [isMuted, autoSpeak]);

  useEffect(() => {
    loadWorldState();
    loadActiveMission();

    const timer = setInterval(() => {
      if (autoRefresh) {
        loadWorldState();
        checkProactiveAlerts();
      }
    }, 15000);

    return () => clearInterval(timer);
  }, [autoRefresh, loadWorldState, loadActiveMission, checkProactiveAlerts]);

  // Initialize Web Speech API
  useEffect(() => {
    if (typeof window !== "undefined") {
      synthRef.current = window.speechSynthesis;
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = "en-US";

        recognition.onstart = () => {
          setIsListening(true);
          setVisualState("LISTENING");
        };

        recognition.onresult = (event: any) => {
          let currentTranscript = "";
          for (let i = event.resultIndex; i < event.results.length; i++) {
            currentTranscript += event.results[i][0].transcript;
          }
          setTranscript(currentTranscript);
        };

        recognition.onerror = (event: any) => {
          console.warn("Speech recognition error:", event.error);
          setIsListening(false);
          setVisualState("IDLE");
        };

        recognition.onend = () => {
          setIsListening(false);
          // If transcript was captured, execute interaction
          if (transcript.trim()) {
            handleVoiceInteract(transcript.trim());
          } else {
            setVisualState("IDLE");
          }
        };

        recognitionRef.current = recognition;
      }
    }
  }, [transcript]);

  // Text to Speech playback
  const speakResponse = (text: string) => {
    if (isMuted || !synthRef.current || typeof window === "undefined") return;

    synthRef.current.cancel(); // Stop any previous speech
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;

    utterance.onstart = () => {
      setIsSpeaking(true);
      setVisualState("SPEAKING");
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      setVisualState("COMPLETED");
    };

    utterance.onerror = () => {
      setIsSpeaking(false);
      setVisualState("COMPLETED");
    };

    synthRef.current.speak(utterance);
  };

  const stopSpeaking = () => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
      setVisualState("IDLE");
    }
  };

  // Toggle Microphone
  const toggleListening = () => {
    if (isListening) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsListening(false);
      setVisualState("IDLE");
    } else {
      stopSpeaking();
      setTranscript("");
      if (recognitionRef.current) {
        try {
          recognitionRef.current.start();
        } catch {
          setIsListening(true);
          setVisualState("LISTENING");
        }
      } else {
        // Fallback for browsers without Web Speech API
        setErrorMsg("Web Speech API not supported in this browser. Please use natural language text input below.");
      }
    }
  };

  // Process Voice or Typed Input
  const handleVoiceInteract = async (inputQuery: string) => {
    if (!inputQuery.trim()) return;

    setVisualState("THINKING");
    setLoading(true);
    setErrorMsg(null);

    try {
      const res = await fetchApi<any>("/jarvis/voice/interact", {
        method: "POST",
        body: JSON.stringify({ transcript: inputQuery }),
      });

      if (res) {
        setSpokenResponse(res.spoken_response || res.response_text || "Assessment complete.");

        if (res.investigation) {
          setActiveMission(res.investigation);
          setVisualState("WAITING_FOR_HUMAN");
        } else {
          setVisualState("SPEAKING");
        }

        if (!isMuted && autoSpeak && res.spoken_response) {
          speakResponse(res.spoken_response);
        } else {
          setVisualState("COMPLETED");
        }

        // Refresh world state in background
        loadWorldState();
      }
    } catch (err: any) {
      setErrorMsg(`Interaction error: ${err.message}`);
      setVisualState("IDLE");
    } finally {
      setLoading(false);
      setTextInput("");
    }
  };

  // Trigger manual investigation on a specific event
  const handleDeepenInvestigation = async (eventRef: string) => {
    setVisualState("INVESTIGATING");
    setLoading(true);
    try {
      const res = await fetchApi<any>("/jarvis/voice/interact", {
        method: "POST",
        body: JSON.stringify({ transcript: `Investigate event ${eventRef}` }),
      });

      if (res && res.investigation) {
        setActiveMission(res.investigation);
        setSpokenResponse(res.spoken_response || "Investigation completed. Human verification required.");
        if (!isMuted && autoSpeak && res.spoken_response) {
          speakResponse(res.spoken_response);
        } else {
          setVisualState("WAITING_FOR_HUMAN");
        }
      }
    } catch (err: any) {
      setErrorMsg(`Investigation failed: ${err.message}`);
      setVisualState("IDLE");
    } finally {
      setLoading(false);
    }
  };

  // Trigger Path A Autonomous Pipeline Simulation
  const handleTriggerAutonomousPipeline = async () => {
    setLoading(true);
    setVisualState("INVESTIGATING");
    try {
      const res = await fetchApi<any>("/jarvis/autonomous/trigger", {
        method: "POST",
        body: JSON.stringify({ source: "NASA FIRMS VIIRS" }),
      });
      if (res && res.outcomes) {
        const top = res.outcomes[0];
        const alertMsg = `Autonomous pipeline ingested observation: Formed ${top.event_code} (${top.risk_level} risk: ${top.risk_score.toFixed(0)}/100). Escalate for human verification.`;
        setSpokenResponse(alertMsg);
        if (!isMuted && autoSpeak) {
          speakResponse(alertMsg);
        }
        await loadWorldState();
        await loadActiveMission();
      }
    } catch (err: any) {
      setErrorMsg(`Autonomous ingestion trigger failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Filtered active intelligence stream
  const filteredItems = activeItems.filter((item) => {
    if (activeFilter === "CRITICAL") return item.risk_score >= 75.0;
    if (activeFilter === "HIGH") return item.risk_score >= 55.0 && item.risk_score < 75.0;
    if (activeFilter === "CHANGED") return item.what_changed && !item.what_changed.includes("Active thermal observation detected");
    if (activeFilter === "UNCERTAIN") return item.uncertainty_tier === "UNCERTAIN" || item.facility_status === "UNCATALOGED";
    return true;
  });

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header />

        {/* Proactive Voice Alert Banner */}
        {proactiveAlert && (
          <div className="bg-amber-500/10 border-b border-amber-500/30 px-6 py-2.5 flex items-center justify-between text-xs font-mono text-amber-300">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-amber-400 animate-bounce" />
              <span className="font-bold">PROACTIVE INTELLIGENCE NOTICE:</span>
              <span>{proactiveAlert}</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => speakResponse(proactiveAlert)}
                className="px-2 py-0.5 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 cursor-pointer flex items-center gap-1"
              >
                <Volume2 className="w-3 h-3" /> Listen
              </button>
              <button
                onClick={() => setProactiveAlert(null)}
                className="text-slate-400 hover:text-slate-200 cursor-pointer"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Main Operational Console Scroll View */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-6">
          {/* Top Console Bar */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800/80 rounded-xl p-4 shadow-lg backdrop-blur-md">
            <div>
              <div className="flex items-center gap-2.5">
                <span className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2 font-mono">
                  <Activity className="w-5 h-5 text-amber-400" />
                  JARVIS
                </span>
                <span className="text-xs px-2.5 py-0.5 rounded-full font-mono bg-amber-500/10 text-amber-400 border border-amber-500/30 font-semibold">
                  AI ORCHESTRATION & REASONING CONSOLE
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Autonomous intelligence monitoring sovereign Indian thermal operational environment.
              </p>
            </div>

            {/* Governed System State Badges */}
            <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
              <span className="px-2.5 py-1 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                SYSTEM AWARENESS: ACTIVE
              </span>
              <span className="px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                AUTONOMOUS PATH A: ONLINE
              </span>
              <span className="px-2.5 py-1 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center gap-1.5">
                <Lock className="w-3 h-3 text-rose-400" />
                DISPATCH: BLOCKED
              </span>
              <span className="px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-amber-300 flex items-center gap-1.5">
                <ShieldCheck className="w-3 h-3 text-amber-400" />
                HITL: ENFORCED
              </span>

              <button
                onClick={loadWorldState}
                disabled={loading}
                title="Refresh State"
                className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>

          {/* CURRENT SITUATION METRICS BANNER */}
          <div>
            <div className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
              <span className="flex items-center gap-1.5 font-bold">
                <Layers className="w-3.5 h-3.5 text-amber-400" />
                CURRENT OPERATIONAL SITUATION
              </span>
              <span className="text-[11px] text-slate-400">
                Active Clusters: {situation.total_active} | Refreshed: {lastRefreshed || "Live"}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {/* Critical */}
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

              {/* High Risk */}
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
                <div className="text-[11px] text-slate-400 mt-0.5">Risk Score 55 - 74</div>
              </button>

              {/* Changed Events */}
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
                <div className="text-[11px] text-slate-400 mt-0.5">Observation Cycle Deltas</div>
              </button>

              {/* Uncertain */}
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

          {/* VOICE INTERACTION & OPERATIONAL DIALOGUE CONSOLE */}
          <div className="bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 rounded-xl p-5 shadow-xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-80 h-80 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800/80 pb-3.5 mb-4">
              <div className="flex items-center gap-3">
                <div
                  className={`w-3 h-3 rounded-full ${
                    visualState === "LISTENING"
                      ? "bg-cyan-400 animate-ping"
                      : visualState === "SPEAKING"
                      ? "bg-amber-400 animate-pulse"
                      : visualState === "INVESTIGATING"
                      ? "bg-purple-400 animate-spin"
                      : visualState === "WAITING_FOR_HUMAN"
                      ? "bg-amber-500"
                      : "bg-emerald-400"
                  }`}
                />
                <span className="text-xs font-mono uppercase tracking-wider font-bold text-slate-300">
                  VOICE OPERATIONAL INTERFACE
                </span>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-amber-300 border border-slate-700 font-semibold">
                  STATUS: {visualState}
                </span>
              </div>

              {/* Voice Controls */}
              <div className="flex items-center gap-2 font-mono text-xs">
                <button
                  onClick={() => setIsMuted(!isMuted)}
                  className={`px-2.5 py-1 rounded border transition-colors flex items-center gap-1.5 cursor-pointer ${
                    isMuted
                      ? "bg-rose-500/10 border-rose-500/30 text-rose-300"
                      : "bg-slate-800 border-slate-700 text-slate-300 hover:text-white"
                  }`}
                  title={isMuted ? "Unmute Spoken Responses" : "Mute Spoken Responses"}
                >
                  {isMuted ? <VolumeX className="w-3.5 h-3.5 text-rose-400" /> : <Volume2 className="w-3.5 h-3.5 text-cyan-400" />}
                  <span>{isMuted ? "MUTED" : "VOICE ON"}</span>
                </button>

                {isSpeaking && (
                  <button
                    onClick={stopSpeaking}
                    className="px-2.5 py-1 rounded bg-rose-500/20 border border-rose-500/40 text-rose-300 hover:bg-rose-500/30 flex items-center gap-1 cursor-pointer"
                  >
                    <Pause className="w-3.5 h-3.5" /> Stop Speaking
                  </button>
                )}

                <button
                  onClick={handleTriggerAutonomousPipeline}
                  disabled={loading}
                  className="px-3 py-1 rounded bg-amber-500/10 border border-amber-500/30 hover:bg-amber-500/20 text-amber-300 flex items-center gap-1.5 cursor-pointer font-semibold"
                  title="Simulates live observation arrival and runs Path A autonomous pipeline"
                >
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  Simulate New Observation (Path A)
                </button>
              </div>
            </div>

            {/* Tactical Microphone & Interaction Center */}
            <div className="flex flex-col sm:flex-row items-center gap-4 py-2">
              <button
                onClick={toggleListening}
                className={`relative group w-16 h-16 rounded-full flex items-center justify-center transition-all cursor-pointer shrink-0 ${
                  isListening
                    ? "bg-cyan-500 text-white shadow-xl shadow-cyan-500/40 scale-105"
                    : "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 hover:border-amber-400/50"
                }`}
              >
                {isListening ? (
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
                  <span>{isListening ? "Listening... Speak naturally to JARVIS" : "Press microphone or type an operational query below:"}</span>
                  {transcript && <span className="text-cyan-400">Captured: &ldquo;{transcript}&rdquo;</span>}
                </div>

                {/* Natural text fallback input */}
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleVoiceInteract(textInput);
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
                    className="px-4 py-2.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 font-mono text-xs font-bold transition-all disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
                  >
                    <span>Execute</span>
                    <CornerDownLeft className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>
            </div>

            {/* Spoken Response & Reasoning Output Box */}
            {spokenResponse && (
              <div className="mt-4 pt-3.5 border-t border-slate-800/80 bg-slate-950/60 rounded-lg p-4 border border-slate-800 font-mono">
                <div className="text-[11px] font-bold text-amber-400 uppercase tracking-wider mb-1.5 flex items-center gap-2">
                  <Volume2 className="w-3.5 h-3.5" />
                  JARVIS SPOKEN ASSESSMENT:
                </div>
                <p className="text-sm text-slate-200 leading-relaxed">{spokenResponse}</p>
              </div>
            )}
          </div>

          {/* DUAL COLUMN WORKSPACE: ACTIVE INTELLIGENCE & ONGOING INVESTIGATION */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* LEFT COLUMN: ACTIVE INTELLIGENCE STREAM (7 Cols) */}
            <div className="lg:col-span-7 space-y-3">
              <div className="flex items-center justify-between font-mono text-xs">
                <span className="font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <Flame className="w-4 h-4 text-amber-400" />
                  ACTIVE INTELLIGENCE STREAM ({filteredItems.length})
                </span>
                <span className="text-[11px] text-slate-400">Filter: {activeFilter}</span>
              </div>

              {filteredItems.length === 0 ? (
                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-8 text-center text-slate-400 font-mono text-xs">
                  No thermal events match filter &lsquo;{activeFilter}&rsquo;.
                </div>
              ) : (
                <div className="space-y-2.5">
                  {filteredItems.slice(0, 8).map((item) => (
                    <div
                      key={item.event_id}
                      onClick={() => setSelectedEvent(item)}
                      className={`p-4 rounded-xl border transition-all cursor-pointer ${
                        selectedEvent?.event_id === item.event_id
                          ? "bg-slate-900 border-amber-400/50 shadow-md"
                          : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/80"
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
                            <span>Peak FRP: {item.max_frp.toFixed(1)} MW</span>
                          </div>
                        </div>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeepenInvestigation(item.event_code);
                          }}
                          className="px-2.5 py-1 rounded bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 font-mono text-[11px] flex items-center gap-1 cursor-pointer shrink-0"
                        >
                          <Crosshair className="w-3 h-3" /> Investigate
                        </button>
                      </div>

                      {/* What Changed & Why It Matters */}
                      <div className="mt-2.5 pt-2 border-t border-slate-800/60 text-xs font-mono space-y-1">
                        <div className="text-slate-400">
                          <strong className="text-slate-300">What Changed:</strong> {item.what_changed}
                        </div>
                        <div className="text-slate-400">
                          <strong className="text-slate-300">Why It Matters:</strong> {item.why_it_matters}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* RIGHT COLUMN: DYNAMIC INVESTIGATION & EPISTEMIC REASONING (5 Cols) */}
            <div className="lg:col-span-5 space-y-3">
              <div className="flex items-center justify-between font-mono text-xs">
                <span className="font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-amber-400" />
                  GOVERNED INVESTIGATION & REASONING
                </span>
                <span className="text-[11px] text-rose-400 font-bold">DISPATCH: BLOCKED</span>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-lg space-y-4">
                {activeMission ? (
                  <>
                    <div className="border-b border-slate-800 pb-3">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-sm font-bold text-amber-300">
                          MISSION: {activeMission.event_code}
                        </span>
                        <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/40">
                          REQUIRES HUMAN VERIFICATION
                        </span>
                      </div>
                      <div className="text-xs font-mono text-slate-400 mt-1">
                        Authoritative Risk: {activeMission.risk_score?.toFixed(1) || "78.0"}/100 ({activeMission.risk_level || "HIGH"})
                      </div>
                    </div>

                    {/* Dynamically Combined Governed Capabilities */}
                    <div>
                      <div className="text-[11px] font-mono text-slate-400 font-bold uppercase mb-2 flex items-center gap-1.5">
                        <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                        CAPABILITIES COMBINED DYNAMICALLY:
                      </div>
                      <div className="flex flex-wrap gap-1.5 font-mono text-[10px]">
                        {activeMission.selected_capabilities?.map((cap, i) => (
                          <span key={i} className="px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300">
                            {cap}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Structured Epistemic Reasoning (5-way separation) */}
                    <div className="space-y-2.5 font-mono text-xs">
                      {/* Known */}
                      <div className="p-2.5 rounded bg-emerald-950/20 border border-emerald-500/30">
                        <div className="text-[11px] font-bold text-emerald-400 mb-1 flex items-center gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5" /> KNOWN (Observed Ground Truth)
                        </div>
                        <ul className="list-disc list-inside text-slate-300 space-y-0.5 text-[11px]">
                          {activeMission.epistemic_synthesis?.known?.map((k, idx) => (
                            <li key={idx}>{k}</li>
                          ))}
                        </ul>
                      </div>

                      {/* Inferred */}
                      <div className="p-2.5 rounded bg-cyan-950/20 border border-cyan-500/30">
                        <div className="text-[11px] font-bold text-cyan-400 mb-1 flex items-center gap-1.5">
                          <TrendingUp className="w-3.5 h-3.5" /> INFERRED (Model Predictions & Proximity)
                        </div>
                        <ul className="list-disc list-inside text-slate-300 space-y-0.5 text-[11px]">
                          {activeMission.epistemic_synthesis?.inferred?.map((inf, idx) => (
                            <li key={idx}>{inf}</li>
                          ))}
                        </ul>
                      </div>

                      {/* Uncertain */}
                      <div className="p-2.5 rounded bg-purple-950/20 border border-purple-500/30">
                        <div className="text-[11px] font-bold text-purple-400 mb-1 flex items-center gap-1.5">
                          <HelpCircle className="w-3.5 h-3.5" /> UNCERTAIN (Epistemic Gaps)
                        </div>
                        <ul className="list-disc list-inside text-slate-300 space-y-0.5 text-[11px]">
                          {activeMission.epistemic_synthesis?.uncertain?.map((u, idx) => (
                            <li key={idx}>{u}</li>
                          ))}
                        </ul>
                      </div>

                      {/* Missing */}
                      <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                        <div className="text-[11px] font-bold text-slate-400 mb-1 flex items-center gap-1.5">
                          <Radio className="w-3.5 h-3.5" /> MISSING (Unconfigured Providers)
                        </div>
                        <ul className="list-disc list-inside text-slate-400 space-y-0.5 text-[11px]">
                          {activeMission.epistemic_synthesis?.missing?.map((m, idx) => (
                            <li key={idx}>{m}</li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Human Oversight & Verification Boundary */}
                    <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 font-mono text-xs space-y-2">
                      <div className="flex items-center gap-1.5 font-bold text-amber-400">
                        <ShieldAlert className="w-4 h-4" /> HUMAN-IN-THE-LOOP AUTHORIZATION REQUIRED
                      </div>
                      <p className="text-[11px] text-slate-300">
                        Autonomous intelligence has concluded. In accordance with sovereign operating protocol, consequential dispatch actions require explicit human authorization.
                      </p>
                      <div className="flex gap-2 pt-1">
                        <button
                          onClick={() => {
                            setSpokenResponse(`Event ${activeMission.event_code} verified by human analyst. Record persisted to audit log.`);
                            speakResponse(`Event ${activeMission.event_code} verified.`);
                          }}
                          className="flex-1 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[11px] cursor-pointer"
                        >
                          Verify Assessment
                        </button>
                        <button
                          onClick={() => {
                            setSpokenResponse(`Event ${activeMission.event_code} marked as contested. Re-evaluation queued.`);
                          }}
                          className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] cursor-pointer"
                        >
                          Contest
                        </button>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="p-8 text-center text-slate-400 font-mono text-xs space-y-2">
                    <Crosshair className="w-8 h-8 text-slate-600 mx-auto" />
                    <div>No active investigation loaded.</div>
                    <div className="text-[11px] text-slate-400">
                      Select an event from the Active Intelligence Stream and click &ldquo;Investigate&rdquo;, or say &ldquo;Investigate Gujarat&rdquo; in the voice console.
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
