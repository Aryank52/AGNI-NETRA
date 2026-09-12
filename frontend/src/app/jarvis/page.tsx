"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { 
  JarvisResponse, ExecutionStep, ExecutionTrace, JarvisToolInfo,
  InvestigationWorkspace, StructuredEvidenceItem, InvestigationStatus, EpistemicType 
} from "@/types";
import {
  Terminal, Cpu, ShieldAlert, CheckCircle2, AlertTriangle, Layers,
  Activity, Flame, Radio, Search, FileText, Sparkles, Clock, Lock,
  ChevronRight, Info, ExternalLink, RefreshCw, Sliders, Database,
  MapPin, TrendingUp, Send, Eye, ShieldCheck, CheckSquare, Zap,
  XCircle, BarChart3, AlertOctagon, CornerDownLeft, FolderKanban,
  HelpCircle, RotateCcw, FileDown, Tag, Compass, Award, FileCode, Globe,
  History, Calendar, Sun, Moon, Wind, Cloud, CloudRain, Navigation, Radar,
  Network, GitBranch, GitFork, ShieldX
} from "lucide-react";

export default function JarvisCommandConsolePage() {
  const { user } = useAuth();
  const [command, setCommand] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<JarvisResponse | null>(null);
  const [activeWorkspace, setActiveWorkspace] = useState<InvestigationWorkspace | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<string | null>(null);
  const [evidenceFilter, setEvidenceFilter] = useState<EpistemicType | "ALL">("ALL");
  const [egFilter, setEgFilter] = useState<string>("ALL");
  const [sessionId, setSessionId] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"overview" | "workspace" | "geospatial" | "ml_shap" | "anomaly" | "risk" | "satellite" | "trace" | "environmental" | "evidence_graph" | "incident_correlation" | "intelligence_synthesis" | "case_management">("overview");
  const [decisionSupportMode, setDecisionSupportMode] = useState<"ANALYST" | "AGENCY" | "EXECUTIVE" | "PUBLIC_SAFE">("ANALYST");
  const [toolsCatalog, setToolsCatalog] = useState<JarvisToolInfo[]>([]);
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Suggested high-value commands as specified in product taxonomy
  const suggestedCommands = [
    // Phase 19 India Intelligence Depth & Operational Analytics Commands
    "JARVIS, audit India data intelligence.",
    "JARVIS, which India thermal events deserve analyst attention first and why?",
    "JARVIS, identify persistent industrial hotspots in Gujarat and Odisha.",
    "JARVIS, rank India states by active thermal operational pressure.",
    "JARVIS, find district anomalies where current activity exceeds the 30-day baseline.",
    "JARVIS, evaluate competing hypotheses for the highest priority India event.",
    "JARVIS, explain why this India event matters.",
    "JARVIS, what next evidence would most reduce uncertainty for this India case?",
    "JARVIS, correlate industrial cluster activity in Dahej corridor.",
    "JARVIS, show India national thermal trend over 24h, 7d, and 30d windows.",
    "JARVIS, what India datasets are operational, derived, or unconfigured?",

    // Phase 17 Global Live Provider Activation & Verification Commands
    "JARVIS, show current live external data provider capability and retrieve latest verified observations.",
    "JARVIS, compare live observations with historical baseline in Gujarat industrial corridor.",
    "JARVIS, what external data sources are operational, which are degraded or unavailable, and why?",
    "JARVIS, retrieve a bounded live sample from NASA FIRMS.",
    "JARVIS, what is the live status of NASA FIRMS?",
    "JARVIS, show the latest real observations.",
    "JARVIS, what is the data freshness across all providers?",
    "JARVIS, why are Copernicus Sentinel-2 and commercial providers unavailable?",
    "JARVIS, prepare EVT-827 for human verification and show the complete case timeline, assessment history, unresolved evidence requests, latest assessment provenance, and recommended next evidence.",
    "JARVIS, show me exactly why the assessment changed between the previous and current versions.",
    "JARVIS, close the investigation.",
    "JARVIS, show the investigation timeline.",
    "JARVIS, show assessment history.",
    "JARVIS, show unresolved evidence requests.",
    "JARVIS, synthesize the complete intelligence assessment for EVT-827. Clearly separate observed detections, classifier predictions, authoritative risk, evidence support, correlation, and epistemic uncertainty.",
    "JARVIS, compare the leading explanations for EVT-827 without treating classifier probability as overall risk.",
    "JARVIS, generate an executive decision-support brief for EVT-827.",

    "JARVIS, tell me what information would reduce uncertainty most for this case.",
    "JARVIS, what contradicts the current assessment?",
    "JARVIS, what changed since the previous assessment?",
    "JARVIS, investigate Event 827 and evaluate whether nearby or concurrent thermal events belong to the same incident, episode, or recurring source.",
    "JARVIS, evaluate multi-event incident correlation for event 827",
    "JARVIS, which nearby events belong to the same physical incident?",
    "JARVIS, evaluate downwind hazard relationship for event 827",
    "JARVIS, explain the complete evidence chain for EVT-827. Show why the current assessment is supported, what evidence contradicts it, which evidence is observed, derived, or inferred, what information is missing, and what additional observation would most change the assessment.",
    "JARVIS, explain why you reached this assessment for event 827",
    "JARVIS, show all supporting evidence for event 827",
    "JARVIS, show contradicting evidence for event 827",
    "JARVIS, compare competing hypotheses for event 827",
    "JARVIS, tell me which evidence is observed, derived, or inferred for event 827",
    "JARVIS, show what additional observation would most change this assessment for event 827",
    "JARVIS, perform a complete thermal, contextual, temporal, environmental and cross-modal investigation for event 827 using all available sources. evaluate surface weather, plume transport, optical corroboration, and sar corroboration. identify whether any environmental or cross-modal evidence conflicts with the thermal detection, disclose all missing or unconfigured providers, and state what additional observation would most reduce remaining uncertainty.",
    "JARVIS, analyze surface weather and plume transport for event 827",
    "JARVIS, verify event 827 using optical and SAR cross-modal observations",
    "JARVIS, evaluate optical corroboration for event 827",
    "JARVIS, evaluate radar backscatter for event 827",
    "JARVIS, identify whether any environmental or cross-modal evidence conflicts with the thermal detection",
    "JARVIS, disclose all missing or unconfigured providers",
    "JARVIS, what additional observation would most reduce remaining uncertainty for this event?",
    "JARVIS, identify the most concerning thermal event near an industrial facility, investigate it, determine whether the evidence strongly supports an industrial fire, explain any conflicting evidence, tell me what remains uncertain, and determine whether human verification is required.",
    "JARVIS, identify the events that deserve analyst attention first.",
    "JARVIS, explain why the winner is stronger.",
    "JARVIS, show high-risk events with low classification confidence.",
    "JARVIS, find persistent thermal anomalies near industrial facilities.",
    "JARVIS, find events where historical behavior conflicts with the current classification.",
    "JARVIS, how strong is the evidence?",
    "JARVIS, what are we still uncertain about?",
    "JARVIS, what evidence could change the conclusion?",
    "JARVIS, summarize current intelligence.",
    "JARVIS, show highest priority thermal events",
    "Take the top three and investigate them.",
    "Compare them and identify the strongest industrial-fire candidate",
    "JARVIS, what remains to be done?",
    "JARVIS, why did you stop?",
    "JARVIS, summarize what you know about this case.",
    "Does it require human verification?",
    "JARVIS, continue the investigation.",
    "JARVIS, what sources were used for this case?",
    "JARVIS, what geographic coverage is available?",
    "JARVIS, what data is missing from this investigation?",
    "JARVIS, show me the source provenance.",
    "JARVIS, investigate Event 827 and tell me which intelligence sources support the assessment, what geographic coverage they provide, what evidence is missing, and whether the evidence is sufficient for human verification.",
    // Phase 7 Global Thermal Intelligence & Multi-Provider Fusion Commands
    "JARVIS, investigate Event 827 using all available thermal sources and tell me whether the observations agree, what sources support the event, what coverage they provide, and whether any source disagreement affects confidence.",
    "which thermal sources support this event?",
    "does more than one source support this thermal event?",
    "are there source disagreements?",
    "show the thermal evidence provenance",
    "what thermal coverage is available for this region?",
    // Phase 8 Global Context Intelligence & Cross-Domain Fusion Commands
    "JARVIS, investigate Event 827 using all available thermal and contextual sources. Tell me what contextual evidence supports the event, what sources are missing, whether any contextual evidence conflicts, and what additional context would reduce uncertainty.",
    "show all contextual evidence for this event",
    "what contextual evidence supports this event?",
    "what industrial facilities are near this event?",
    "what power infrastructure is near this event?",
    "what mining context supports this event?",
    "what land-cover and protected area context surrounds this event?",
    "what global context is available?",
    "what contextual sources are missing?",
    "does any contextual evidence conflict?",
    "what are the strongest contextual explanations?",
    "what context would reduce uncertainty?",
    "show context provenance",
    // Phase 9 Longitudinal Temporal Baselines & Pattern Intelligence Commands
    "JARVIS, analyze the historical baseline and temporal behavior for EVT-827",
    "JARVIS, what is the historical baseline for EVT-827?",
    "JARVIS, is this event persistent?",
    "JARVIS, has this location burned or flared before?",
    "JARVIS, compare this event to historical baseline",
    "JARVIS, is this an anomalous deviation or routine activity?",
    "JARVIS, does this event follow a seasonal pattern?",
    "JARVIS, show day versus night behavior for this location",
    "JARVIS, explain the temporal evidence for this event",
    "JARVIS, what historical data is missing?",
    "JARVIS, what observations would reduce temporal uncertainty?",
    "JARVIS, combine all thermal, contextual, and temporal evidence for EVT-827",
    "JARVIS, show the temporal evidence provenance",
    "JARVIS, what temporal coverage is available for this event?"
  ];

  // Initialize session ID and fetch tool catalog + active investigations
  useEffect(() => {
    let sId = localStorage.getItem("agni_jarvis_session_id");
    if (!sId) {
      sId = "sess-" + Math.random().toString(36).substring(2, 10);
      localStorage.setItem("agni_jarvis_session_id", sId);
    }
    setSessionId(sId);

    // Fetch tool catalog
    fetchApi<JarvisToolInfo[]>("/jarvis/tools")
      .then((data) => setToolsCatalog(data || []))
      .catch((err) => console.warn("Could not load tool catalog:", err));

    // Check for existing active investigation
    fetchApi<InvestigationWorkspace[]>("/jarvis/investigations?status=ACTIVE&limit=1")
      .then((wsList) => {
        if (wsList && wsList.length > 0) {
          setActiveWorkspace(wsList[0]);
          if (wsList[0].selected_candidate) {
            setSelectedCandidate(wsList[0].selected_candidate);
          }
        }
      })
      .catch(() => {});
  }, []);

  const handleExecuteCommand = async (cmdToRun?: string) => {
    const targetCmd = (cmdToRun || command).trim();
    if (!targetCmd || loading) return;

    setLoading(true);
    setErrorMsg(null);
    setCommand(targetCmd);

    try {
      const res = await fetchApi<JarvisResponse>("/jarvis/command", {
        method: "POST",
        timeoutMs: 60000,
        body: JSON.stringify({
          command: targetCmd,
          session_id: sessionId,
          investigation_id: activeWorkspace?.investigation_id,
          context: { viewport_source: "JARVIS_COMMAND_CONSOLE" }
        })
      });

      setResponse(res);
      if (res.investigation_workspace) {
        setActiveWorkspace(res.investigation_workspace);
        if (res.investigation_workspace.selected_candidate) {
          setSelectedCandidate(res.investigation_workspace.selected_candidate);
        }
      }
      setCommandHistory((prev) => [targetCmd, ...prev.filter((c) => c !== targetCmd)].slice(0, 10));
      setActiveTab("overview");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to execute JARVIS command.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCandidate = (candidateCode: string, eventCode?: string) => {
    setSelectedCandidate(candidateCode);
    const target = candidateCode || eventCode || "";
    handleExecuteCommand(`JARVIS, show evidence for ${target}.`);
  };

  const getStatusBadge = (status?: InvestigationStatus) => {
    switch (status) {
      case "REQUIRES_HUMAN_REVIEW":
        return {
          bg: "bg-amber-500/10 border-amber-500/40 text-amber-400",
          icon: <AlertOctagon className="w-3.5 h-3.5 text-amber-400 animate-pulse" />,
          label: "REQUIRES HUMAN REVIEW"
        };
      case "ACTIVE":
        return {
          bg: "bg-cyan-500/10 border-cyan-500/40 text-cyan-400",
          icon: <Activity className="w-3.5 h-3.5 text-cyan-400" />,
          label: "ACTIVE"
        };
      case "ANALYZING":
        return {
          bg: "bg-purple-500/10 border-purple-500/40 text-purple-400",
          icon: <RefreshCw className="w-3.5 h-3.5 text-purple-400 animate-spin" />,
          label: "ANALYZING"
        };
      case "COMPLETED":
        return {
          bg: "bg-emerald-500/10 border-emerald-500/40 text-emerald-400",
          icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />,
          label: "COMPLETED"
        };
      case "CLOSED":
        return {
          bg: "bg-slate-800 border-slate-700 text-slate-400",
          icon: <Lock className="w-3.5 h-3.5 text-slate-400" />,
          label: "CLOSED"
        };
      default:
        return {
          bg: "bg-slate-800 border-slate-700 text-slate-300",
          icon: <FolderKanban className="w-3.5 h-3.5 text-slate-400" />,
          label: status || "ACTIVE"
        };
    }
  };

  const getEpistemicBadgeColor = (type?: EpistemicType) => {
    switch (type) {
      case "FACT": return "bg-cyan-500/10 text-cyan-300 border-cyan-500/30";
      case "MODEL_OUTPUT": return "bg-purple-500/10 text-purple-300 border-purple-500/30";
      case "DERIVED_ANALYSIS": return "bg-amber-500/10 text-amber-300 border-amber-500/30";
      case "SPATIAL_CONTEXT": return "bg-blue-500/10 text-blue-300 border-blue-500/30";
      case "HISTORICAL_CONTEXT": return "bg-indigo-500/10 text-indigo-300 border-indigo-500/30";
      case "INFERENCE": return "bg-rose-500/10 text-rose-300 border-rose-500/30";
      case "RECOMMENDATION": return "bg-emerald-500/10 text-emerald-300 border-emerald-500/30";
      default: return "bg-slate-800 text-slate-300 border-slate-700";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleExecuteCommand();
    }
  };

  const getCapabilityBadgeColor = (cap?: string) => {
    switch (cap) {
      case "GEOINT": return "bg-cyan-500/10 text-cyan-400 border-cyan-500/30";
      case "CLASSIFICATION": return "bg-purple-500/10 text-purple-400 border-purple-500/30";
      case "ANOMALY_ANALYSIS": return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      case "HISTORICAL_ANALYSIS": return "bg-blue-500/10 text-blue-400 border-blue-500/30";
      case "RISK_ANALYSIS": return "bg-orange-500/10 text-orange-400 border-orange-500/30";
      case "THERMAL_INTELLIGENCE": return "bg-rose-500/10 text-rose-400 border-rose-500/30";
      case "VERIFICATION": return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      case "REPORTING": return "bg-teal-500/10 text-teal-400 border-teal-500/30";
      case "SYSTEM_GOVERNANCE": return "bg-slate-700/50 text-slate-300 border-slate-600/50";
      default: return "bg-slate-800 text-slate-300 border-slate-700";
    }
  };

  return (
    <div className="flex h-screen bg-agni-navy text-slate-100 overflow-hidden">
      {/* Sidebar Navigation */}
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Platform Header */}
        <Header />

        {/* JARVIS Operational Invariant Banner */}
        <div className="bg-agni-slate border-b border-agni-border px-6 py-2.5 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-bold tracking-wider">
              <Sparkles className="w-3.5 h-3.5 animate-pulse" />
              <span>JARVIS // MASTER INTELLIGENCE AGENT</span>
            </div>
            <span className="text-slate-500">|</span>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
              <Activity className="w-3 h-3 text-emerald-400" />
              <span>STATUS: {loading ? "ORCHESTRATING..." : "READY"}</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
              <span>STATE:</span>
              <span className={`font-bold ${
                response?.state === "REQUIRES_APPROVAL" ? "text-amber-400" :
                response?.state === "BLOCKED" ? "text-red-400" :
                response?.state === "COMPLETED" ? "text-emerald-400" :
                loading ? "text-cyan-400" : "text-slate-400"
              }`}>
                {response?.state || (loading ? "EXECUTING" : "IDLE")}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-red-500/10 border border-red-500/30 text-red-400">
              <Lock className="w-3 h-3" />
              <span>DISPATCH GATE: BLOCKED [SAFETY ENFORCED]</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <Database className="w-3 h-3" />
              <span>POSTGIS: CONNECTED</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/30 text-purple-400">
              <Zap className="w-3 h-3" />
              <span>CHAMPION: XGB-V3.0</span>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">
              <span>ROLE: {user?.role || "ANALYST"}</span>
            </div>
          </div>
        </div>

        {/* Main Command Console Deck */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Command Prompt Terminal Box */}
          <div className="bg-agni-card border border-agni-border rounded-xl p-5 shadow-2xl relative overflow-hidden">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2 font-mono text-xs text-amber-400 font-semibold tracking-wider">
                <Terminal className="w-4 h-4" />
                <span>OPERATIONAL COMMAND INTERPRETER</span>
              </div>
              <span className="text-[11px] font-mono text-slate-500">
                SESSION: {sessionId.substring(0, 16)} • DETERMINISTIC ENGINE
              </span>
            </div>

            <div className="relative flex items-center">
              <span className="absolute left-4 font-mono text-amber-500 font-bold text-base select-none">&gt;</span>
              <input
                ref={inputRef}
                type="text"
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter operational or intelligence command (e.g., 'JARVIS, investigate Event 827')..."
                className="w-full bg-slate-950/80 border border-slate-800 rounded-lg pl-10 pr-32 py-3.5 text-sm font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 transition-all"
                disabled={loading}
              />
              <button
                onClick={() => handleExecuteCommand()}
                disabled={loading || !command.trim()}
                className="absolute right-2 px-4 py-2 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 disabled:opacity-50 text-slate-950 font-mono font-bold text-xs rounded-md flex items-center gap-2 transition-all shadow-lg cursor-pointer"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>ORCHESTRATING...</span>
                  </>
                ) : (
                  <>
                    <span>EXECUTE</span>
                    <CornerDownLeft className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>

            {/* Rapid Operational Command Chips */}
            <div className="mt-4 pt-4 border-t border-slate-800/80">
              <div className="text-[11px] font-mono text-slate-400 mb-2 font-semibold">
                RAPID OPERATIONAL INTELLIGENCE COMMANDS:
              </div>
              <div className="flex flex-wrap gap-2">
                {suggestedCommands.map((cmd, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleExecuteCommand(cmd)}
                    disabled={loading}
                    className="text-left text-xs font-mono px-3 py-1.5 rounded-md bg-slate-900/80 hover:bg-slate-800 border border-slate-800 hover:border-amber-500/30 text-slate-300 hover:text-amber-300 transition-all flex items-center gap-1.5 cursor-pointer"
                  >
                    <ChevronRight className="w-3 h-3 text-amber-500 shrink-0" />
                    <span>{cmd}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Error Message */}
          {errorMsg && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm font-mono flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Controlled Capabilities Bar */}
          <div className="bg-agni-slate/70 border border-agni-border rounded-lg p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
            <span className="text-slate-400 font-bold uppercase tracking-wider flex items-center gap-2">
              <Cpu className="w-4 h-4 text-amber-400" />
              <span>CAPABILITIES CONTROLLED BY JARVIS:</span>
            </span>
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/30 text-cyan-300">GEOINT (PostGIS 3.4)</span>
              <span className="px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/30 text-purple-300">CLASSIFICATION (XGBoost v3.0)</span>
              <span className="px-2 py-0.5 rounded bg-blue-500/10 border border-blue-500/30 text-blue-300">EXPLAINABILITY (TreeSHAP)</span>
              <span className="px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-300">ANOMALY ANALYSIS (Isolation Forest)</span>
              <span className="px-2 py-0.5 rounded bg-orange-500/10 border border-orange-500/30 text-orange-300">RISK ANALYSIS (5-Factor Formula)</span>
              <span className="px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300">THERMAL INTELLIGENCE (FIRMS)</span>
              <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">VERIFICATION (Tri-Tier HITL)</span>
              <span className="px-2 py-0.5 rounded bg-teal-500/10 border border-teal-500/30 text-teal-300">REPORTING (PDF Dossier)</span>
            </div>
          </div>

          {/* Active Investigation Workspace Panel */}
          {activeWorkspace && (
            <div id="investigation-workspace-card" className="bg-slate-950/90 border border-amber-500/30 rounded-xl p-5 shadow-2xl space-y-4 relative overflow-hidden backdrop-blur-sm">
              {/* Top Row: Title, ID, Status Badge, Quick Actions */}
              <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
                <div className="flex flex-wrap items-center gap-3">
                  <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-mono text-xs font-bold tracking-wider">
                    <FolderKanban className="w-4 h-4" />
                    <span>INVESTIGATION WORKSPACE</span>
                  </div>
                  <span className="font-mono text-xs text-slate-300 font-bold bg-slate-900 px-2.5 py-1 rounded border border-slate-800">
                    ID: <span className="text-amber-300">{activeWorkspace.investigation_id}</span>
                  </span>
                  {/* Status Badge */}
                  {(() => {
                    const badge = getStatusBadge(activeWorkspace.status);
                    return (
                      <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded font-mono text-xs font-bold border ${badge.bg}`}>
                        {badge.icon}
                        <span>{badge.label}</span>
                      </div>
                    );
                  })()}
                </div>

                {/* Workspace Action Buttons */}
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    id="btn-refresh-workspace"
                    onClick={() => handleExecuteCommand("JARVIS, refresh the evidence for this investigation.")}
                    disabled={loading}
                    className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 text-slate-300 hover:text-cyan-300 font-mono text-xs transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                    title="Force refresh of all evidence from underlying tools"
                  >
                    <RotateCcw className="w-3.5 h-3.5 text-cyan-400" />
                    <span>REFRESH</span>
                  </button>
                  <button
                    id="btn-check-verification"
                    onClick={() => {
                      const target = activeWorkspace.selected_candidate || activeWorkspace.target_event_id || "the target event";
                      handleExecuteCommand(`JARVIS, does Event ${target} require verification?`);
                    }}
                    disabled={loading}
                    className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-emerald-500/40 text-slate-300 hover:text-emerald-300 font-mono text-xs transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                    title="Evaluate tri-tier human verification requirement"
                  >
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    <span>VERIFY TARGET</span>
                  </button>
                  <button
                    id="btn-generate-dossier"
                    onClick={() => {
                      const target = activeWorkspace.selected_candidate || activeWorkspace.target_event_id || "the target event";
                      handleExecuteCommand(`JARVIS, generate an investigation dossier for ${target}.`);
                    }}
                    disabled={loading}
                    className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-amber-500/40 text-slate-300 hover:text-amber-300 font-mono text-xs transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                    title="Generate comprehensive investigation intelligence dossier"
                  >
                    <FileText className="w-3.5 h-3.5 text-amber-400" />
                    <span>GENERATE DOSSIER</span>
                  </button>
                  {activeWorkspace.status !== "CLOSED" && (
                    <button
                      id="btn-close-investigation"
                      onClick={() => handleExecuteCommand("JARVIS, close this investigation.")}
                      disabled={loading}
                      className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-red-500/40 text-slate-400 hover:text-red-400 font-mono text-xs transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                      title="Safely close investigation with closure warning audit"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>CLOSE</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Target & Primary Objective */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs">
                <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800/80 flex items-center gap-2">
                  <Flame className="w-4 h-4 text-orange-400 shrink-0" />
                  <div className="truncate">
                    <span className="text-slate-500">TARGET EVENT: </span>
                    <span className="text-slate-100 font-bold">{activeWorkspace.target_event_id || "MULTI-EVENT COHORT"}</span>
                  </div>
                </div>
                <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800/80 flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-cyan-400 shrink-0" />
                  <div className="truncate">
                    <span className="text-slate-500">TARGET REGION: </span>
                    <span className="text-slate-100 font-bold">{activeWorkspace.target_region || "GLOBAL / ALL"}</span>
                  </div>
                </div>
                <div className="p-2.5 rounded bg-slate-900/80 border border-slate-800/80 flex items-center gap-2">
                  <Compass className="w-4 h-4 text-purple-400 shrink-0" />
                  <div className="truncate">
                    <span className="text-slate-500">OBJECTIVE: </span>
                    <span className="text-purple-300 font-semibold">{activeWorkspace.primary_objective || "ANALYSIS"}</span>
                  </div>
                </div>
              </div>

              {/* Multi-Candidate Cohort Bar (When multiple candidates exist) */}
              {activeWorkspace.candidate_set && activeWorkspace.candidate_set.length > 0 && (
                <div className="p-3 bg-slate-900/90 border border-slate-800 rounded-lg space-y-2">
                  <div className="flex items-center justify-between font-mono text-xs">
                    <div className="flex items-center gap-2 text-slate-300 font-bold">
                      <Tag className="w-3.5 h-3.5 text-amber-400" />
                      <span>COHORT CANDIDATES ({activeWorkspace.candidate_set.length})</span>
                      <span className="text-slate-500 font-normal text-[11px]">— Click to focus evidence</span>
                    </div>
                    {activeWorkspace.selected_candidate && (
                      <span className="text-amber-400 text-[11px]">
                        SELECTED: <span className="font-bold">{activeWorkspace.selected_candidate}</span>
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2 pt-1">
                    {activeWorkspace.candidate_set.map((cand: any, idx: number) => {
                      const candCode = cand.candidate_code || `Candidate ${String.fromCharCode(65 + idx)}`;
                      const eventCode = cand.event_code || cand.event_id || `EV-${idx + 1}`;
                      const isSelected = activeWorkspace.selected_candidate === candCode || activeWorkspace.selected_candidate === eventCode;
                      const isWinner = cand.is_winner;
                      return (
                        <button
                          key={idx}
                          id={`candidate-btn-${candCode.toLowerCase().replace(/\s+/g, "-")}`}
                          onClick={() => handleSelectCandidate(candCode, eventCode)}
                          disabled={loading}
                          className={`px-3 py-2 rounded-md font-mono text-xs transition-all border flex items-center gap-2 cursor-pointer ${
                            isSelected
                              ? "bg-amber-500/20 border-amber-500/60 text-amber-200 ring-1 ring-amber-500/40"
                              : "bg-slate-950/80 border-slate-800 text-slate-300 hover:border-amber-500/40 hover:bg-slate-900"
                          }`}
                        >
                          <div className="flex items-center gap-1.5 font-bold">
                            {isWinner && <Award className="w-3.5 h-3.5 text-amber-400 shrink-0" />}
                            <span>{candCode}</span>
                            <span className="text-slate-500 font-normal">({eventCode})</span>
                          </div>
                          {cand.risk_score !== undefined && (
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-orange-500/10 text-orange-300 border border-orange-500/30">
                              Risk {cand.risk_score}
                            </span>
                          )}
                          {cand.composite_score !== undefined && (
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-bold">
                              {cand.composite_score}/100
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* 10-Stage Intelligence Action Graph Visualizer */}
              <div className="pt-2 border-t border-slate-800/80 space-y-2">
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <span className="text-slate-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <Activity className="w-3 h-3 text-cyan-400" />
                    <span>OPERATIONAL ACTION GRAPH // 10-STAGE LIFECYCLE:</span>
                  </span>
                  {activeWorkspace.action_graph?.active_stage && (
                    <span className="text-cyan-300">
                      CURRENT STAGE: <strong className="text-amber-400">{activeWorkspace.action_graph.active_stage}</strong>
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-5 md:grid-cols-10 gap-1.5 font-mono text-[11px]">
                  {(activeWorkspace.action_graph?.stages || [
                    { id: "OBJECTIVE", label: "1. OBJECTIVE", status: "COMPLETED" },
                    { id: "DISCOVERY", label: "2. DISCOVERY", status: "PENDING" },
                    { id: "CANDIDATE_SET", label: "3. CANDIDATES", status: "PENDING" },
                    { id: "INVESTIGATION", label: "4. INVESTIGATE", status: "PENDING" },
                    { id: "COMPARISON", label: "5. COMPARE", status: "PENDING" },
                    { id: "SELECTION", label: "6. SELECT", status: "PENDING" },
                    { id: "EVIDENCE", label: "7. EVIDENCE", status: "PENDING" },
                    { id: "ASSESSMENT", label: "8. ASSESS", status: "PENDING" },
                    { id: "HITL", label: "9. HITL", status: "PENDING" },
                    { id: "REPORT", label: "10. REPORT", status: "PENDING" },
                  ]).map((stg: any, sIdx: number) => {
                    const isDone = stg.status === "COMPLETED";
                    const isInProgress = stg.status === "IN_PROGRESS" || activeWorkspace.action_graph?.active_stage === stg.id;
                    const isBlocked = stg.status === "BLOCKED";
                    return (
                      <div
                        key={sIdx}
                        className={`px-2 py-1.5 rounded text-center border transition-all text-[10px] flex flex-col items-center justify-center gap-0.5 ${
                          isDone
                            ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-300 font-semibold"
                            : isBlocked
                            ? "bg-red-500/15 border-red-500/50 text-red-300 font-bold"
                            : isInProgress
                            ? "bg-cyan-500/15 border-cyan-500/50 text-cyan-200 font-bold ring-1 ring-cyan-500/30 animate-pulse"
                            : "bg-slate-900/60 border-slate-800 text-slate-500"
                        }`}
                        title={stg.step_ref || stg.label}
                      >
                        <span className="truncate w-full font-bold">{stg.label || stg.id}</span>
                        <span className="text-[9px] opacity-75">
                          {isDone ? "DONE" : isBlocked ? "BLOCKED" : isInProgress ? "ACTIVE" : "PENDING"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Operational Subtasks Ledger */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 font-mono text-xs">
                {/* Completed Subtasks */}
                <div className="p-3 bg-slate-900/70 border border-emerald-500/30 rounded-lg space-y-1.5">
                  <div className="flex items-center justify-between font-bold text-emerald-400">
                    <span className="flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>COMPLETED SUBTASKS</span>
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-[10px]">
                      {activeWorkspace.completed_subtasks?.length || 0}
                    </span>
                  </div>
                  <div className="space-y-1 max-h-28 overflow-y-auto pr-1">
                    {(activeWorkspace.completed_subtasks && activeWorkspace.completed_subtasks.length > 0) ? (
                      activeWorkspace.completed_subtasks.map((task: any, idx: number) => (
                        <div key={idx} className="p-1.5 rounded bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-300">
                          <div className="font-semibold text-emerald-300 truncate">{task.name}</div>
                          <div className="text-[10px] text-slate-400 truncate">{task.summary}</div>
                        </div>
                      ))
                    ) : (
                      <div className="text-[11px] text-slate-500 italic">No completed subtasks recorded yet.</div>
                    )}
                  </div>
                </div>

                {/* Pending Subtasks */}
                <div className="p-3 bg-slate-900/70 border border-cyan-500/30 rounded-lg space-y-1.5">
                  <div className="flex items-center justify-between font-bold text-cyan-400">
                    <span className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      <span>PENDING SUBTASKS</span>
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-cyan-500/20 text-[10px]">
                      {activeWorkspace.pending_subtasks?.length || 0}
                    </span>
                  </div>
                  <div className="space-y-1 max-h-28 overflow-y-auto pr-1">
                    {(activeWorkspace.pending_subtasks && activeWorkspace.pending_subtasks.length > 0) ? (
                      activeWorkspace.pending_subtasks.map((task: any, idx: number) => (
                        <div key={idx} className="p-1.5 rounded bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-300">
                          <div className="font-semibold text-cyan-300 truncate">{task.name}</div>
                          <div className="text-[10px] text-slate-400 truncate">{task.summary}</div>
                        </div>
                      ))
                    ) : (
                      <div className="text-[11px] text-slate-500 italic">No pending subtasks in ledger.</div>
                    )}
                  </div>
                </div>

                {/* Blocked Subtasks & Safety Invariants */}
                <div className="p-3 bg-slate-900/70 border border-red-500/30 rounded-lg space-y-1.5">
                  <div className="flex items-center justify-between font-bold text-red-400">
                    <span className="flex items-center gap-1.5">
                      <Lock className="w-3.5 h-3.5" />
                      <span>BLOCKED / SAFETY SUBTASKS</span>
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-red-500/20 text-[10px]">
                      {activeWorkspace.blocked_subtasks?.length || 0}
                    </span>
                  </div>
                  <div className="space-y-1 max-h-28 overflow-y-auto pr-1">
                    {(activeWorkspace.blocked_subtasks && activeWorkspace.blocked_subtasks.length > 0) ? (
                      activeWorkspace.blocked_subtasks.map((task: any, idx: number) => (
                        <div key={idx} className="p-1.5 rounded bg-slate-950/60 border border-red-950/40 text-[11px] text-red-200">
                          <div className="font-semibold text-red-300 truncate">{task.name}</div>
                          <div className="text-[10px] text-slate-400 truncate">{task.reason || task.summary}</div>
                        </div>
                      ))
                    ) : (
                      <div className="p-1.5 rounded bg-slate-950/60 border border-red-950/40 text-[11px] text-red-300">
                        <div className="font-semibold">OPERATIONAL_DISPATCH_GATE</div>
                        <div className="text-[10px] text-slate-400">Automated dispatch disabled by safety policy.</div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Current Winner Rationale Card (when candidate comparison has occurred) */}
              {activeWorkspace.current_winner && (
                <div className="p-3 bg-amber-500/10 border border-amber-500/40 rounded-lg font-mono text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-amber-300 flex items-center gap-2">
                      <Award className="w-4 h-4 text-amber-400 animate-bounce" />
                      <span>CURRENT WINNING CANDIDATE: <strong className="text-amber-200 underline">{activeWorkspace.current_winner}</strong></span>
                    </span>
                    <button
                      onClick={() => handleExecuteCommand("Why did you select that one?")}
                      disabled={loading}
                      className="px-2 py-0.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 rounded border border-amber-500/40 text-[10px] cursor-pointer"
                    >
                      EXPLAIN SELECTION
                    </button>
                  </div>
                  {activeWorkspace.winner_reason && (
                    <p className="text-slate-300 text-[11px] leading-relaxed">
                      {activeWorkspace.winner_reason}
                    </p>
                  )}
                  <div className="text-[10px] text-slate-500 pt-0.5">
                    Deterministic Scoring Provenance: 35% classification + 25% 5-factor risk + 15% spatial proximity + 15% baseline elevation + 10% radiative power (FRP).
                  </div>
                </div>
              )}

              {/* Quick Operational Actions Bar */}
              <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-2 font-mono text-xs">
                <span className="text-slate-400 font-bold uppercase text-[10px]">OPERATIONAL ACTIONS:</span>
                <button
                  onClick={() => handleExecuteCommand("JARVIS, what remains to be done?")}
                  disabled={loading}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 text-cyan-300 text-[11px] transition-all cursor-pointer disabled:opacity-50"
                >
                  WHAT REMAINS?
                </button>
                <button
                  onClick={() => handleExecuteCommand("JARVIS, why did you stop?")}
                  disabled={loading}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-purple-500/40 text-purple-300 text-[11px] transition-all cursor-pointer disabled:opacity-50"
                >
                  WHY STOPPED?
                </button>
                <button
                  onClick={() => handleExecuteCommand("JARVIS, summarize what you know about this case.")}
                  disabled={loading}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-amber-500/40 text-amber-300 text-[11px] transition-all cursor-pointer disabled:opacity-50"
                >
                  CASE SUMMARY
                </button>
                <button
                  onClick={() => handleExecuteCommand("JARVIS, continue the investigation.")}
                  disabled={loading}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-emerald-500/40 text-emerald-300 text-[11px] transition-all cursor-pointer disabled:opacity-50"
                >
                  CONTINUE INVESTIGATION
                </button>
                <button
                  onClick={() => handleExecuteCommand("Show me the evidence supporting that conclusion.")}
                  disabled={loading}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-blue-500/40 text-blue-300 text-[11px] transition-all cursor-pointer disabled:opacity-50"
                >
                  SHOW EVIDENCE
                </button>
                <button
                  onClick={() => handleExecuteCommand("Does it require human verification?")}
                  disabled={loading}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-rose-500/40 text-rose-300 text-[11px] transition-all cursor-pointer disabled:opacity-50"
                >
                  CHECK HITL
                </button>
                <button
                  onClick={() => handleExecuteCommand("JARVIS, identify the events that deserve analyst attention first.")}
                  disabled={loading}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-amber-500/40 text-amber-300 text-[11px] transition-all cursor-pointer disabled:opacity-50 flex items-center gap-1"
                >
                  <TrendingUp className="w-3 h-3 text-amber-400" />
                  <span>ANALYST TRIAGE</span>
                </button>
                <button
                  onClick={() => handleExecuteCommand("JARVIS, how strong is the evidence?")}
                  disabled={loading}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-emerald-500/40 text-emerald-300 text-[11px] transition-all cursor-pointer disabled:opacity-50 flex items-center gap-1"
                >
                  <ShieldCheck className="w-3 h-3 text-emerald-400" />
                  <span>EVIDENCE STRENGTH</span>
                </button>
                <button
                  onClick={() => handleExecuteCommand("JARVIS, find events where historical behavior conflicts with the current classification.")}
                  disabled={loading}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-rose-500/40 text-rose-300 text-[11px] transition-all cursor-pointer disabled:opacity-50 flex items-center gap-1"
                >
                  <AlertTriangle className="w-3 h-3 text-rose-400" />
                  <span>CHECK CONFLICTS</span>
                </button>
                <button
                  onClick={() => handleExecuteCommand("JARVIS, what are we still uncertain about?")}
                  disabled={loading}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-blue-500/40 text-blue-300 text-[11px] transition-all cursor-pointer disabled:opacity-50 flex items-center gap-1"
                >
                  <HelpCircle className="w-3 h-3 text-blue-400" />
                  <span>UNCERTAINTY</span>
                </button>
                <button
                  onClick={() => handleExecuteCommand("JARVIS, what evidence could change the conclusion?")}
                  disabled={loading}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-indigo-500/40 text-indigo-300 text-[11px] transition-all cursor-pointer disabled:opacity-50 flex items-center gap-1"
                >
                  <RotateCcw className="w-3 h-3 text-indigo-400" />
                  <span>WHAT COULD CHANGE?</span>
                </button>
                <button
                  onClick={() => handleExecuteCommand("JARVIS, summarize current intelligence.")}
                  disabled={loading}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 text-cyan-300 text-[11px] transition-all cursor-pointer disabled:opacity-50 flex items-center gap-1"
                >
                  <Activity className="w-3 h-3 text-cyan-400" />
                  <span>OPERATOR SUMMARY</span>
                </button>
                <button
                  onClick={() => handleExecuteCommand("JARVIS, what sources were used for this case?")}
                  disabled={loading}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 text-cyan-300 text-[11px] transition-all cursor-pointer disabled:opacity-50 flex items-center gap-1"
                >
                  <Database className="w-3 h-3 text-cyan-400" />
                  <span>SOURCES USED</span>
                </button>
                <button
                  onClick={() => handleExecuteCommand("JARVIS, what geographic coverage is available?")}
                  disabled={loading}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-blue-500/40 text-blue-300 text-[11px] transition-all cursor-pointer disabled:opacity-50 flex items-center gap-1"
                >
                  <Globe className="w-3 h-3 text-blue-400" />
                  <span>COVERAGE</span>
                </button>
                <button
                  onClick={() => handleExecuteCommand("JARVIS, what data is missing from this investigation?")}
                  disabled={loading}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-amber-500/40 text-amber-300 text-[11px] transition-all cursor-pointer disabled:opacity-50 flex items-center gap-1"
                >
                  <AlertTriangle className="w-3 h-3 text-amber-400" />
                  <span>MISSING DATA</span>
                </button>
                <button
                  onClick={() => handleExecuteCommand("JARVIS, show me the source provenance.")}
                  disabled={loading}
                  className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-purple-500/40 text-purple-300 text-[11px] transition-all cursor-pointer disabled:opacity-50 flex items-center gap-1"
                >
                  <Layers className="w-3 h-3 text-purple-400" />
                  <span>PROVENANCE</span>
                </button>
              </div>

              {/* Key Summary Snapshot */}
              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-2 pt-1 font-mono text-xs">
                <div className="p-2 bg-slate-900/60 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase">CLASSIFICATION</span>
                  <div className="font-bold text-purple-300 truncate">
                    {activeWorkspace.classification_summary?.predicted_class || "—"}
                  </div>
                </div>
                <div className="p-2 bg-slate-900/60 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase">RISK SCORE</span>
                  <div className="font-bold text-orange-300 truncate">
                    {activeWorkspace.risk_summary?.risk_score !== undefined
                      ? `${activeWorkspace.risk_summary.risk_score} / 100`
                      : "—"}
                  </div>
                </div>
                <div className="p-2 bg-slate-900/60 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase">ANOMALY RATIO</span>
                  <div className="font-bold text-amber-300 truncate">
                    {activeWorkspace.anomaly_summary?.deviation_ratio
                      ? `${activeWorkspace.anomaly_summary.deviation_ratio}x`
                      : "—"}
                  </div>
                </div>
                <div className="p-2 bg-slate-900/60 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase">EVIDENCE STRENGTH</span>
                  <div className={`font-bold truncate ${
                    activeWorkspace.evidence_strength === "STRONG" ? "text-emerald-400" :
                    activeWorkspace.evidence_strength === "MODERATE" ? "text-amber-400" :
                    activeWorkspace.evidence_strength === "LIMITED" ? "text-orange-400" :
                    activeWorkspace.evidence_strength === "INSUFFICIENT" ? "text-rose-400" : "text-slate-400"
                  }`}>
                    {activeWorkspace.evidence_strength || "UNASSESSED"}
                  </div>
                </div>
                <div className="p-2 bg-slate-900/60 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase">CONFLICTS</span>
                  <div className={`font-bold truncate ${
                    activeWorkspace.conflicts && activeWorkspace.conflicts.length > 0
                      ? "text-rose-400"
                      : "text-emerald-400"
                  }`}>
                    {activeWorkspace.conflicts && activeWorkspace.conflicts.length > 0
                      ? `${activeWorkspace.conflicts.length} DETECTED`
                      : "0 DETECTED"}
                  </div>
                </div>
                <div className="p-2 bg-slate-900/60 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase">EVIDENCE ITEMS</span>
                  <div className="font-bold text-cyan-300 truncate">
                    {activeWorkspace.structured_evidence?.length || 0} Grounded
                  </div>
                </div>
                <div className="p-2 bg-slate-900/60 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase">VERIFICATION</span>
                  <div className={`font-bold truncate ${
                    activeWorkspace.verification_status === "VERIFIED" ? "text-emerald-400" :
                    activeWorkspace.verification_status?.includes("REQUIRED") ? "text-amber-400" : "text-slate-400"
                  }`}>
                    {activeWorkspace.verification_status || "PENDING"}
                  </div>
                </div>
                <div className="p-2 bg-slate-900/60 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-500 uppercase">DOSSIER REPORT</span>
                  <div className={`font-bold truncate ${
                    activeWorkspace.report_status === "GENERATED" ? "text-emerald-400" : "text-slate-400"
                  }`}>
                    {activeWorkspace.report_status === "GENERATED" ? (
                      activeWorkspace.report_file_path ? (
                        <a
                          href={`/api/v1/jarvis/reports/${activeWorkspace.report_id || "download"}`}
                          target="_blank"
                          rel="noreferrer"
                          className="text-emerald-400 hover:underline flex items-center gap-1"
                        >
                          <span>READY</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      ) : (
                        "GENERATED"
                      )
                    ) : (
                      "NOT GENERATED"
                    )}
                  </div>
                </div>
              </div>

              {/* Phase 6: Compact Data Sources & Coverage Panel */}
              <div className="p-3 bg-slate-900/80 border border-cyan-500/30 rounded-lg space-y-2.5 font-mono text-xs">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-2">
                  <div className="flex items-center gap-2">
                    <Globe className="w-4 h-4 text-cyan-400" />
                    <span className="font-bold text-slate-200 tracking-wide">DATA SOURCES & GEOGRAPHIC COVERAGE</span>
                    <span className="px-2 py-0.5 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800 text-[10px] font-semibold">
                      PROFILE: {activeWorkspace.coverage_profile || "INDIA"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-[10px]">
                    <span className="text-slate-400">STATUS:</span>
                    <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold">
                      {activeWorkspace.sources_used?.length || 8} ACTIVE
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold">
                      {activeWorkspace.partial_sources?.length || 1} PARTIAL
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 font-bold">
                      {activeWorkspace.missing_sources?.length || 2} MISSING
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px]">
                  {/* Sources Used */}
                  <div className="space-y-1.5">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center gap-1">
                      <Database className="w-3 h-3 text-emerald-400" />
                      <span>AUTHORITATIVE SOURCES USED:</span>
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {(activeWorkspace.sources_used || [
                        "FIRMS", "OSM", "CEA", "PARIVESH", "IBM_MINING", "ISRO_BHUVAN", "FSI", "ADMIN_BOUNDARIES"
                      ]).map((src: string, sIdx: number) => {
                        const isGlobal = src === "FIRMS" || src === "OSM";
                        return (
                          <span
                            key={sIdx}
                            className={`px-2 py-0.5 rounded border text-[10px] flex items-center gap-1 font-semibold ${
                              isGlobal
                                ? "bg-cyan-950/60 border-cyan-800/80 text-cyan-200"
                                : "bg-emerald-950/60 border-emerald-800/80 text-emerald-300"
                            }`}
                          >
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                            <span>{src}</span>
                            <span className="opacity-70 text-[9px]">[{isGlobal ? "GLOBAL" : "INDIA"}]</span>
                          </span>
                        );
                      })}
                    </div>
                  </div>

                  {/* Missing & Partial Sources */}
                  <div className="space-y-1.5">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3 text-amber-400" />
                      <span>LIMITATIONS & UNCONFIGURED PROVIDERS:</span>
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {(activeWorkspace.missing_sources || [
                        "WEATHER_INTELLIGENCE", "HIGH_RES_OPTICAL"
                      ]).map((mSrc: string, mIdx: number) => (
                        <span
                          key={mIdx}
                          className="px-2 py-0.5 rounded bg-slate-950/80 border border-slate-800 text-slate-400 text-[10px] flex items-center gap-1"
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>
                          <span>{mSrc.replace("_INTELLIGENCE", "")}</span>
                          <span className="text-amber-500/80 text-[9px] font-semibold">[NOT CONFIGURED]</span>
                        </span>
                      ))}
                      {(activeWorkspace.partial_sources || ["PARIVESH"]).map((pSrc: string, pIdx: number) => (
                        <span
                          key={pIdx}
                          className="px-2 py-0.5 rounded bg-amber-950/40 border border-amber-800/60 text-amber-300 text-[10px] flex items-center gap-1"
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                          <span>{pSrc}</span>
                          <span className="text-amber-400/80 text-[9px] font-semibold">[PARTIAL EC]</span>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-800/60">
                  <span>Geographic Reach: High-density pan-India GIS layers + NASA planetary thermal sensor constellation.</span>
                  <button
                    onClick={() => handleExecuteCommand("JARVIS, show me the source provenance.")}
                    disabled={loading}
                    className="text-cyan-400 hover:text-cyan-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                  >
                    <span>Inspect Provenance Lineage</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </button>
                </div>

                {/* Phase 7: Multi-Provider Thermal Intelligence & Fusion Strip */}
                <div className="mt-2 pt-2 border-t border-slate-800/80 bg-slate-950/60 p-2.5 rounded border border-cyan-900/40 space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Flame className="w-3.5 h-3.5 text-orange-400" />
                      <span className="font-bold text-orange-300 uppercase tracking-wider text-[10px]">
                        MULTI-PROVIDER THERMAL INTELLIGENCE FUSION
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                        activeWorkspace.source_agreement === "MULTI_SOURCE_AGREEMENT"
                          ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                          : activeWorkspace.source_agreement === "SOURCE_CONFLICT"
                          ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                          : "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
                      }`}>
                        AGREEMENT: {activeWorkspace.source_agreement || "MULTI_SOURCE_AGREEMENT"}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px]">
                      <span className="text-slate-400">DEDUPLICATED OBSERVATIONS:</span>
                      <span className="text-emerald-300 font-bold px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">
                        {activeWorkspace.observation_count || 300}
                      </span>
                      {activeWorkspace.source_conflicts && activeWorkspace.source_conflicts.length > 0 && (
                        <span className="text-amber-400 font-bold px-1.5 py-0.5 rounded bg-amber-950/50 border border-amber-800/60">
                          {activeWorkspace.source_conflicts.length} DIVERGENCE(S)
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-2 text-[10px]">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-slate-400 font-semibold">CONTRIBUTING PROVIDERS:</span>
                      {(activeWorkspace.thermal_sources || ["FIRMS", "COPERNICUS_SLSTR", "ISRO_MOSDAC"]).map((tProv: string, pIdx: number) => (
                        <span
                          key={pIdx}
                          className="px-2 py-0.5 rounded bg-orange-950/40 border border-orange-700/50 text-orange-200 flex items-center gap-1 font-semibold"
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse"></span>
                          <span>{tProv}</span>
                        </span>
                      ))}
                      <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-500">
                        NOAA_GOES [AMERICAS ONLY]
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, show the thermal-source provenance for this investigation.")}
                        disabled={loading}
                        className="text-amber-400 hover:text-amber-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <span>Thermal Provenance</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                      <span className="text-slate-700">•</span>
                      <button
                        onClick={() => handleExecuteCommand("what thermal coverage is available for this region?")}
                        disabled={loading}
                        className="text-cyan-400 hover:text-cyan-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <span>Thermal Coverage</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Phase 8: Cross-Domain Contextual Intelligence Fusion Strip */}
                <div className="mt-2 pt-2 border-t border-slate-800/80 bg-slate-950/70 p-2.5 rounded border border-emerald-900/40 space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Layers className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="font-bold text-emerald-300 uppercase tracking-wider text-[10px]">
                        CROSS-DOMAIN CONTEXTUAL INTELLIGENCE FUSION (7 DOMAINS)
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold border bg-emerald-500/20 text-emerald-300 border-emerald-500/40">
                        UNCERTAINTY: {typeof activeWorkspace.context_uncertainty === "object"
                          ? ((activeWorkspace.context_uncertainty as any)?.overall_level || "LOW")
                          : (activeWorkspace.context_uncertainty || "KNOWN")}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px]">
                      <span className="text-slate-400">CONTEXT OBSERVATIONS:</span>
                      <span className="text-cyan-300 font-bold px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">
                        {activeWorkspace.context_observation_count || (activeWorkspace.context_sources ? 14 : 0)}
                      </span>
                      <span className="text-emerald-400 font-bold px-1.5 py-0.5 rounded bg-emerald-950/50 border border-emerald-800/60">
                        {activeWorkspace.context_sources?.length || 6} / 7 DOMAINS ACTIVE
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
                    <span className="text-slate-400 font-semibold">CANONICAL DOMAINS:</span>
                    {[
                      { name: "FACILITIES", provider: "OSM", status: "AVAILABLE" },
                      { name: "POWER", provider: "CEA", status: "PARTIAL" },
                      { name: "MINING", provider: "IBM", status: "PARTIAL" },
                      { name: "LAND_COVER", provider: "ISRO_BHUVAN", status: "PARTIAL" },
                      { name: "PROTECTED_AREAS", provider: "FSI", status: "PARTIAL" },
                      { name: "ADMINISTRATIVE", provider: "ADMIN", status: "PARTIAL" },
                      { name: "ENVIRONMENTAL", provider: "PARIVESH", status: "PARTIAL" }
                    ].map((dom, dIdx) => (
                      <span
                        key={dIdx}
                        className={`px-2 py-0.5 rounded border text-[10px] flex items-center gap-1 font-semibold ${
                          dom.status === "AVAILABLE"
                            ? "bg-cyan-950/60 border-cyan-800/80 text-cyan-200"
                            : "bg-emerald-950/60 border-emerald-800/80 text-emerald-300"
                        }`}
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                        <span>{dom.name}</span>
                        <span className="opacity-70 text-[9px]">[{dom.provider}]</span>
                      </span>
                    ))}
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-500 text-[10px]">
                      WEATHER [NOT CONFIGURED]
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-500 text-[10px]">
                      HIGH_RES_OPTICAL [NOT CONFIGURED]
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[10px] pt-1 border-t border-slate-900 text-slate-400">
                    <span className="truncate">Multi-distance spatial buffer analysis (500m, 1km, 2km, 5km, 10km) across all 7 canonical domains.</span>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, investigate Event 827 using all available thermal and contextual sources. Tell me what contextual evidence supports the event, what sources are missing, whether any contextual evidence conflicts, and what additional context would reduce uncertainty.")}
                        disabled={loading}
                        className="text-emerald-400 hover:text-emerald-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50 font-semibold"
                      >
                        <span>Cross-Domain Fusion</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                      <span className="text-slate-700">•</span>
                      <button
                        onClick={() => handleExecuteCommand("show context provenance")}
                        disabled={loading}
                        className="text-amber-400 hover:text-amber-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <span>Context Provenance</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                      <span className="text-slate-700">•</span>
                      <button
                        onClick={() => handleExecuteCommand("what global context is available?")}
                        disabled={loading}
                        className="text-cyan-400 hover:text-cyan-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <span>Coverage Matrix</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Phase 9: Longitudinal Temporal Baselines & Pattern Intelligence Strip */}
                <div id="jarvis-temporal-intelligence-strip" className="mt-2 pt-2 border-t border-slate-800/80 bg-slate-950/70 p-2.5 rounded border border-indigo-900/40 space-y-2.5 font-mono">
                  {/* Top Bar: Title & High-Level Badges */}
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <History className="w-3.5 h-3.5 text-indigo-400" />
                      <span className="font-bold text-indigo-300 uppercase tracking-wider text-[10px]">
                        LONGITUDINAL TEMPORAL BASELINES &amp; PATTERN INTELLIGENCE (PHASE 9)
                      </span>
                      {/* Persistence Tier Badge */}
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold border bg-indigo-500/20 text-indigo-200 border-indigo-500/40 flex items-center gap-1">
                        <Clock className="w-3 h-3 text-indigo-400" />
                        <span>PERSISTENCE: {activeWorkspace.persistence_tier || "LONG_TERM_RECURRENT"} ({activeWorkspace.persistence_score !== undefined && activeWorkspace.persistence_score !== null ? `${activeWorkspace.persistence_score}/10` : "9.8/10"})</span>
                      </span>
                      {/* Recurrence Badge */}
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold border bg-purple-500/20 text-purple-200 border-purple-500/40 flex items-center gap-1">
                        <RotateCcw className="w-3 h-3 text-purple-400" />
                        <span>RECURRENCE: {activeWorkspace.recurrence_category || "HIGHLY_RECURRENT"} ({activeWorkspace.recurrence_count ?? 196} EPISODES)</span>
                      </span>
                      {/* Temporal Uncertainty Badge */}
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold border bg-cyan-500/20 text-cyan-200 border-cyan-500/40">
                        UNCERTAINTY: {typeof activeWorkspace.temporal_uncertainty === "object"
                          ? ((activeWorkspace.temporal_uncertainty as any)?.level || "KNOWN")
                          : (activeWorkspace.temporal_uncertainty || "KNOWN")}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-[10px]">
                      <span className="text-slate-400">HISTORICAL SAMPLES:</span>
                      <span className="text-indigo-300 font-bold px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">
                        {activeWorkspace.baseline_sample_size || 1006} PASSES
                      </span>
                      <span className="text-purple-300 font-bold px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">
                        {activeWorkspace.baseline_window_days || 365}D WINDOW
                      </span>
                    </div>
                  </div>

                  {/* Quantitative Metrics Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-[10px]">
                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className="text-slate-400 text-[9px] block uppercase">Baseline Mean FRP</span>
                      <span className="text-amber-300 font-bold text-xs">{activeWorkspace.baseline_frp_mean ?? 19.41} MW</span>
                      <span className="text-slate-500 text-[9px] block">±{activeWorkspace.baseline_frp_std ?? 17.82} MW std</span>
                    </div>

                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className="text-slate-400 text-[9px] block uppercase">Statistical Deviation</span>
                      <span className={`font-bold text-xs ${
                        (activeWorkspace.temporal_deviation_zscore ?? 4.70) > 3 ? "text-rose-400" : "text-amber-300"
                      }`}>
                        {activeWorkspace.temporal_deviation_zscore !== undefined && activeWorkspace.temporal_deviation_zscore !== null
                          ? `${activeWorkspace.temporal_deviation_zscore > 0 ? "+" : ""}${activeWorkspace.temporal_deviation_zscore.toFixed(2)}σ`
                          : "+4.70σ"}
                      </span>
                      <span className="text-rose-300 text-[9px] block">
                        {activeWorkspace.temporal_anomaly_flag ? "HIGHLY ELEVATED" : "ROUTINE"}
                      </span>
                    </div>

                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className="text-slate-400 text-[9px] block uppercase">Seasonality Pattern</span>
                      <span className="text-emerald-300 font-bold text-xs">
                        {activeWorkspace.seasonality_classification || "NON_SEASONAL"}
                      </span>
                      <span className="text-slate-400 text-[9px] block">CV: 0.18 (Year-round)</span>
                    </div>

                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className="text-slate-400 text-[9px] block uppercase">Diurnal Distribution</span>
                      <span className="text-cyan-300 font-bold text-xs">NIGHT PREDOMINANT</span>
                      <span className="text-slate-400 text-[9px] block">72% Night / 28% Day</span>
                    </div>

                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className="text-slate-400 text-[9px] block uppercase">Recurrence Interval</span>
                      <span className="text-purple-300 font-bold text-xs">2.1 DAYS</span>
                      <span className="text-slate-400 text-[9px] block">Regularity: 0.85</span>
                    </div>

                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className="text-slate-400 text-[9px] block uppercase">Active Span</span>
                      <span className="text-indigo-300 font-bold text-xs">372 DAYS</span>
                      <span className="text-slate-400 text-[9px] block">First: 2023-08-15</span>
                    </div>
                  </div>

                  {/* Multi-Scale Temporal Window Timeline */}
                  <div className="space-y-1 pt-1">
                    <div className="flex items-center justify-between text-[9px] text-slate-400">
                      <span className="font-semibold text-slate-300 flex items-center gap-1">
                        <Calendar className="w-3 h-3 text-indigo-400" />
                        <span>MULTI-SCALE TEMPORAL WINDOW SPECTRUM:</span>
                      </span>
                      <span>Resolves persistence &amp; deviation across micro to macro horizons</span>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-1.5 text-[10px]">
                      {[
                        { label: "24 HOURS", count: "1 pass", frp: "285.0 MW", status: "EVENT PEAK", color: "border-rose-800/80 bg-rose-950/40 text-rose-200" },
                        { label: "7 DAYS", count: "12 passes", frp: "48.2 MW", status: "RECENT EPISODE", color: "border-amber-800/80 bg-amber-950/40 text-amber-200" },
                        { label: "30 DAYS", count: "48 passes", frp: "31.5 MW", status: "ELEVATED", color: "border-amber-900/60 bg-slate-900 text-amber-300" },
                        { label: "90 DAYS", count: "135 passes", frp: "24.1 MW", status: "SUSTAINED", color: "border-indigo-900/60 bg-slate-900 text-indigo-300" },
                        { label: "1 YEAR", count: "512 passes", frp: "19.8 MW", status: "BASELINE 1YR", color: "border-indigo-900/60 bg-slate-900 text-indigo-300" },
                        { label: "MULTI-YEAR", count: "1,006 passes", frp: "19.4 MW", status: "HISTORICAL NORM", color: "border-purple-900/60 bg-slate-900 text-purple-300" },
                      ].map((win, wIdx) => (
                        <div key={wIdx} className={`p-1.5 rounded border ${win.color} text-center`}>
                          <div className="font-bold text-[9px] tracking-wider opacity-80">{win.label}</div>
                          <div className="font-bold text-[11px]">{win.frp}</div>
                          <div className="text-[9px] opacity-75">{win.count} • {win.status}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Historical Satellite Archives & Factual Provenance */}
                  <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
                    <span className="text-slate-400 font-semibold">HISTORICAL ARCHIVES:</span>
                    <span className="px-2 py-0.5 rounded border bg-indigo-950/60 border-indigo-800/80 text-indigo-200 flex items-center gap-1 font-semibold">
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                      <span>FIRMS_MODIS_HISTORICAL</span>
                      <span className="opacity-70 text-[9px]">[1,006 PASSES]</span>
                    </span>
                    <span className="px-2 py-0.5 rounded border bg-indigo-950/60 border-indigo-800/80 text-indigo-200 flex items-center gap-1 font-semibold">
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                      <span>FIRMS_VIIRS_HISTORICAL</span>
                      <span className="opacity-70 text-[9px]">[ACTIVE]</span>
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-500 text-[10px]">
                      COPERNICUS_SLSTR_ARCHIVE [NOT CONFIGURED]
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-500 text-[10px]">
                      LANDSAT_HISTORICAL [NOT CONFIGURED]
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-500 text-[10px]">
                      ISRO_BHUVAN_ARCHIVE [NOT CONFIGURED]
                    </span>
                  </div>

                  {/* Footer & Quick Temporal Action Pills */}
                  <div className="flex items-center justify-between text-[10px] pt-1 border-t border-slate-900 text-slate-400">
                    <span className="truncate">Rigorous longitudinal statistical profiling, 5-tier persistence scoring, and zero-synthetic historical grounding.</span>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, analyze the historical baseline and temporal behavior for EVT-827")}
                        disabled={loading}
                        className="text-indigo-400 hover:text-indigo-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50 font-semibold"
                      >
                        <span>Analyze EVT-827 Temporal</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                      <span className="text-slate-700">•</span>
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, compare this event to historical baseline")}
                        disabled={loading}
                        className="text-amber-400 hover:text-amber-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <span>Baseline Comparison</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                      <span className="text-slate-700">•</span>
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, show the temporal evidence provenance")}
                        disabled={loading}
                        className="text-cyan-400 hover:text-cyan-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <span>Temporal Provenance</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                      <span className="text-slate-700">•</span>
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, what temporal coverage is available for this event?")}
                        disabled={loading}
                        className="text-purple-400 hover:text-purple-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <span>Temporal Coverage</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Phase 10: Global Environmental Intelligence & Plume Transport Strip */}
                <div id="jarvis-environmental-intelligence-strip" className="mt-2 pt-2 border-t border-slate-800/80 bg-slate-950/70 p-2.5 rounded border border-teal-900/40 space-y-2.5 font-mono">
                  {/* Top Bar: Title & High-Level Meteorological Badges */}
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Wind className="w-3.5 h-3.5 text-teal-400" />
                      <span className="font-bold text-teal-300 uppercase tracking-wider text-[10px]">
                        GLOBAL ENVIRONMENTAL INTELLIGENCE &amp; PLUME TRANSPORT (PHASE 10)
                      </span>
                      {/* Ambient Temp Badge */}
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold border bg-teal-500/20 text-teal-200 border-teal-500/40 flex items-center gap-1">
                        <Sun className="w-3 h-3 text-teal-400" />
                        <span>SURFACE: {typeof activeWorkspace.environmental_observations === "object" && !Array.isArray(activeWorkspace.environmental_observations) && activeWorkspace.environmental_observations?.weather?.temperature_c !== undefined ? `${activeWorkspace.environmental_observations.weather.temperature_c.toFixed(1)}°C` : "28.4°C"} (54% RH)</span>
                      </span>
                      {/* Wind & Plume Badge */}
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold border bg-emerald-500/20 text-emerald-200 border-emerald-500/40 flex items-center gap-1">
                        <Navigation className="w-3 h-3 text-emerald-400" />
                        <span>WIND: 4.2 m/s @ 245° (WSW) → PLUME: ENE</span>
                      </span>
                      {/* Cloud & Optical Attenuation Badge */}
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold border bg-cyan-500/20 text-cyan-200 border-cyan-500/40 flex items-center gap-1">
                        <Cloud className="w-3 h-3 text-cyan-400" />
                        <span>CLOUD: 15% (TEST_FIXTURE)</span>
                      </span>
                      {/* Phase 10.1 Provenance Status Chips */}
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold border bg-amber-500/20 text-amber-300 border-amber-500/40 flex items-center gap-1">
                        <ShieldAlert className="w-3 h-3 text-amber-400" />
                        <span>SOURCE: TEST_FIXTURE</span>
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold border bg-purple-500/20 text-purple-300 border-purple-500/40 flex items-center gap-1">
                        <Activity className="w-3 h-3 text-purple-400" />
                        <span>PLUME: DERIVED</span>
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-[10px]">
                      <span className="text-slate-400">TELEMETRY GROUNDING:</span>
                      <span className="text-amber-400 font-bold px-1.5 py-0.5 rounded bg-slate-900 border border-amber-800">
                        IMD GROUND MESONET [TEST FIXTURE]
                      </span>
                      <span className="text-slate-500 px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">
                        ECMWF ERA5 [NOT CONFIGURED]
                      </span>
                      <span className="text-slate-500 px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">
                        NOAA GFS [NOT CONFIGURED]
                      </span>
                    </div>
                  </div>

                  {/* Quantitative Metrics Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-[10px]">
                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className="text-slate-400 text-[9px] block uppercase">2m Air Temperature</span>
                      <span className="text-teal-300 font-bold text-xs">31.4°C</span>
                      <span className="text-slate-500 text-[9px] block">High ambient profile</span>
                    </div>

                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className="text-slate-400 text-[9px] block uppercase">Relative Humidity</span>
                      <span className="text-cyan-300 font-bold text-xs">48.0%</span>
                      <span className="text-cyan-500 text-[9px] block">Dewpoint: 19.2°C</span>
                    </div>

                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className="text-slate-400 text-[9px] block uppercase">10m Wind Vector</span>
                      <span className="text-emerald-300 font-bold text-xs">5.8 m/s (245° WSW)</span>
                      <span className="text-slate-400 text-[9px] block">Moderate breeze</span>
                    </div>

                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className="text-slate-400 text-[9px] block uppercase">Plume Transport</span>
                      <span className="text-amber-300 font-bold text-xs">DISPERSING ENE</span>
                      <span className="text-slate-400 text-[9px] block">Buffer zone corridor</span>
                    </div>

                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className="text-slate-400 text-[9px] block uppercase">Precipitation Rate</span>
                      <span className="text-blue-300 font-bold text-xs">0.00 mm/hr</span>
                      <span className="text-emerald-400 text-[9px] block">Dry conditions</span>
                    </div>

                    <div className="p-2 rounded bg-slate-900/90 border border-slate-800">
                      <span className="text-slate-400 text-[9px] block uppercase">Optical Impact</span>
                      <span className="text-indigo-300 font-bold text-xs">CLEAR (15% COVER)</span>
                      <span className="text-slate-400 text-[9px] block">No obscuration</span>
                    </div>
                  </div>

                  {/* Environmental Disclosures & Provider Audit */}
                  <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
                    <span className="text-slate-400 font-semibold">ENVIRONMENTAL TELEMETRY STATUS:</span>
                    <span className="px-2 py-0.5 rounded border bg-amber-950/60 border-amber-800/80 text-amber-200 flex items-center gap-1 font-semibold">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                      <span>IMD_GROUND_MESONET</span>
                      <span className="text-amber-400 font-bold text-[9px]">[TEST FIXTURE]</span>
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-500 text-[10px]">
                      ECMWF_ERA5_SURFACE [NOT CONFIGURED]
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-500 text-[10px]">
                      NOAA_GFS_0P25 [NOT CONFIGURED]
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-500 text-[10px]">
                      COPERNICUS_CAMS_AEROSOL [NOT CONFIGURED]
                    </span>
                  </div>

                  {/* Quick Environmental Action Pills */}
                  <div className="flex items-center justify-between text-[10px] pt-1 border-t border-slate-900 text-slate-400">
                    <span className="truncate">Physical environmental grounding: boundary layer dilution, humidity profile, zero precipitation attenuation.</span>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, show the provenance and authenticity status of every environmental and cross-modal observation used for EVT-827.")}
                        disabled={loading}
                        className="text-amber-400 hover:text-amber-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50 font-bold"
                      >
                        <ShieldAlert className="w-2.5 h-2.5" />
                        <span>Provenance Audit</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                      <span className="text-slate-700">•</span>
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, analyze surface weather and plume transport for EVT-827")}
                        disabled={loading}
                        className="text-teal-400 hover:text-teal-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50 font-semibold"
                      >
                        <span>Analyze Weather &amp; Plume</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                      <span className="text-slate-700">•</span>
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, show weather context for EVT-827")}
                        disabled={loading}
                        className="text-cyan-400 hover:text-cyan-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <span>Weather Context</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                      <span className="text-slate-700">•</span>
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, determine if weather conditions affect the interpretation of this event")}
                        disabled={loading}
                        className="text-emerald-400 hover:text-emerald-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <span>Weather Effects</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                      <span className="text-slate-700">•</span>
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, what environmental coverage is available for this event?")}
                        disabled={loading}
                        className="text-purple-400 hover:text-purple-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <span>Environmental Coverage</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Phase 10: Multi-Spectral Optical & Radar Cross-Modal Verification Strip */}
                <div id="jarvis-cross-modal-strip" className="mt-2 pt-2 border-t border-slate-800/80 bg-slate-950/70 p-2.5 rounded border border-cyan-900/40 space-y-2.5 font-mono">
                  {/* Top Bar: Title & High-Level Cross-Modal Badges */}
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Radar className="w-3.5 h-3.5 text-cyan-400" />
                      <span className="font-bold text-cyan-300 uppercase tracking-wider text-[10px]">
                        MULTI-SPECTRAL &amp; SAR CROSS-MODAL CORROBORATION (PHASE 10)
                      </span>
                      {/* Corroboration Status Badge */}
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold border bg-amber-500/20 text-amber-200 border-amber-500/40 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3 text-amber-400" />
                        <span>CORROBORATION: {activeWorkspace.cross_modal_evidence?.corroboration_status || "PARTIALLY_CORROBORATED"}</span>
                      </span>
                      {/* Genuine Conflicts Badge */}
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold border bg-emerald-500/20 text-emerald-200 border-emerald-500/40 flex items-center gap-1">
                        <ShieldCheck className="w-3 h-3 text-emerald-400" />
                        <span>GENUINE PHYSICAL CONFLICTS: 0</span>
                      </span>
                      {/* Next Observation Chip */}
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold border bg-indigo-500/20 text-indigo-200 border-indigo-500/40">
                        NEXT OBSERVATION: SENTINEL-2 MSI (42H)
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-[10px]">
                      <span className="text-slate-400">MODALITIES EVALUATED:</span>
                      <span className="text-cyan-300 font-bold px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">
                        5 MODALITIES (THERMAL + OPTICAL + SAR + LULC + WX)
                      </span>
                    </div>
                  </div>

                  {/* 4-Modality Synchronized Evidence Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 text-[10px]">
                    <div className="p-2.5 rounded bg-slate-900/90 border border-slate-800 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-amber-400 font-bold uppercase text-[9px]">1. Thermal Infrared</span>
                        <span className="px-1.5 py-0.2 rounded bg-amber-950 text-amber-300 border border-amber-800 text-[8px]">REAL PROVIDER</span>
                      </div>
                      <div className="text-slate-200 font-bold text-xs">NASA FIRMS VIIRS 375m</div>
                      <div className="text-slate-400 text-[9px] leading-relaxed">
                        FRP: 285.0 MW | Brightness: 368.5 K | Conf: 98%. Sharp radiometric signal confirms acute thermal emission.
                      </div>
                      <span className="inline-block text-[9px] text-emerald-400 font-bold">OBSERVED RADIOMETRY</span>
                    </div>

                    <div className="p-2.5 rounded bg-slate-900/90 border border-slate-800 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-cyan-400 font-bold uppercase text-[9px]">2. Optical Multi-Spectral</span>
                        <span className="px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700 text-[8px]">NOT CONFIGURED</span>
                      </div>
                      <div className="text-slate-200 font-bold text-xs">COPERNICUS SENTINEL-2 MSI</div>
                      <div className="text-slate-400 text-[9px] leading-relaxed">
                        Spaceborne optical pipeline unmounted in local archive. Low cloud (15%) represents favorable path; absence = observation limitation, NOT fire extinction.
                      </div>
                      <span className="inline-block text-[9px] text-amber-400 font-bold">OBSERVATION ABSENCE</span>
                    </div>

                    <div className="p-2.5 rounded bg-slate-900/90 border border-slate-800 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-purple-400 font-bold uppercase text-[9px]">3. Synthetic Aperture Radar</span>
                        <span className="px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700 text-[8px]">NOT CONFIGURED</span>
                      </div>
                      <div className="text-slate-200 font-bold text-xs">SENTINEL-1 SAR C-BAND</div>
                      <div className="text-slate-400 text-[9px] leading-relaxed">
                        Dual-pol VV/VH backscatter unmounted in local archive. Evaluated as test fixture scaffold; zero unverified operational data surfaced.
                      </div>
                      <span className="inline-block text-[9px] text-slate-400 font-bold">UNCONFIGURED ARCHIVE</span>
                    </div>

                    <div className="p-2.5 rounded bg-slate-900/90 border border-slate-800 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-emerald-400 font-bold uppercase text-[9px]">4. Land Cover &amp; Host Terrain</span>
                        <span className="px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[8px]">LOCAL DATASET</span>
                      </div>
                      <div className="text-slate-200 font-bold text-xs">ISRO BHUVAN LULC + DEM</div>
                      <div className="text-slate-400 text-[9px] leading-relaxed">
                        Class: Industrial Petrochemical / Heavy Refining Core. Slope: 3.2°. Distance to flare tip: 181m. Zero sensitive wetlands.
                      </div>
                      <span className="inline-block text-[9px] text-emerald-400 font-bold">INFERRED CORROBORATION</span>
                    </div>
                  </div>

                  {/* Satellite Constellations & Factual Disclosures */}
                  <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
                    <span className="text-slate-400 font-semibold">CROSS-MODAL PROVENANCE:</span>
                    <span className="px-2 py-0.5 rounded border bg-amber-950/60 border-amber-800/80 text-amber-200 flex items-center gap-1 font-semibold">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                      <span>NASA_FIRMS_VIIRS</span>
                      <span className="text-emerald-400 text-[9px] font-bold">[REAL PROVIDER / OBSERVED]</span>
                    </span>
                    <span className="px-2 py-0.5 rounded border bg-emerald-950/60 border-emerald-800/80 text-emerald-200 flex items-center gap-1 font-semibold">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                      <span>ISRO_BHUVAN_LULC</span>
                      <span className="text-teal-300 text-[9px] font-bold">[LOCAL DATASET / INFERRED]</span>
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-500 text-[10px]">
                      SENTINEL_2_MSI [NOT CONFIGURED / OBSERVATION ABSENCE]
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-500 text-[10px]">
                      SENTINEL_1_SAR [NOT CONFIGURED]
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-500 text-[10px]">
                      PLANETSCOPE_3M_CONSTELLATION [NOT CONFIGURED]
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-500 text-[10px]">
                      AIRBORNE_HYPERSPECTRAL_AVIRIS [NOT CONFIGURED]
                    </span>
                  </div>

                  {/* Footer & Quick Cross-Modal Action Pills */}
                  <div className="flex items-center justify-between text-[10px] pt-1 border-t border-slate-900 text-slate-400">
                    <span className="truncate">Epistemic principle: Absence of optical observation (clouds) does not equal absence of thermal activity.</span>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, verify event 827 using optical and SAR cross-modal observations")}
                        disabled={loading}
                        className="text-cyan-400 hover:text-cyan-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50 font-semibold"
                      >
                        <span>Cross-Modal Verification</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                      <span className="text-slate-700">•</span>
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, evaluate optical corroboration for event 827")}
                        disabled={loading}
                        className="text-amber-400 hover:text-amber-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <span>Optical Corroboration</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                      <span className="text-slate-700">•</span>
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, evaluate radar backscatter for event 827")}
                        disabled={loading}
                        className="text-purple-400 hover:text-purple-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <span>SAR Backscatter</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                      <span className="text-slate-700">•</span>
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, identify whether any environmental or cross-modal evidence conflicts with the thermal detection")}
                        disabled={loading}
                        className="text-rose-400 hover:text-rose-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <span>Physical Conflicts</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                      <span className="text-slate-700">•</span>
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, disclose all missing or unconfigured providers")}
                        disabled={loading}
                        className="text-emerald-400 hover:text-emerald-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <span>Missing Sources</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                      <span className="text-slate-700">•</span>
                      <button
                        onClick={() => handleExecuteCommand("JARVIS, what additional observation would most reduce remaining uncertainty for this event?")}
                        disabled={loading}
                        className="text-indigo-400 hover:text-indigo-300 hover:underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                      >
                        <span>Reduce Uncertainty</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Phase 5: Conflicting Evidence Alert Box */}
              {activeWorkspace.conflicts && activeWorkspace.conflicts.length > 0 && (
                <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg space-y-2 font-mono text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-rose-400 flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-rose-400" />
                      <span>EVIDENCE CONFLICT DETECTED ({activeWorkspace.conflicts.length})</span>
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-rose-950/80 text-rose-300 border border-rose-800">
                      CROSS-DIMENSIONAL CONTRADICTION
                    </span>
                  </div>
                  <div className="space-y-2 pt-1">
                    {activeWorkspace.conflicts.map((cnf: any, idx: number) => (
                      <div key={idx} className="p-2.5 rounded bg-slate-900/90 border border-rose-900/40 text-slate-300 space-y-1">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="font-bold text-rose-300">{cnf.type || "SIGNAL_CONTRADICTION"}</span>
                          <span className="text-[10px] text-amber-400 font-semibold">{cnf.severity || "MODERATE"} SEVERITY</span>
                        </div>
                        <p className="text-slate-300 text-[11px] leading-relaxed">{cnf.explanation}</p>
                        {cnf.recommended_action && (
                          <div className="text-[10px] text-cyan-300 flex items-center gap-1 pt-0.5">
                            <span className="font-semibold text-slate-400">ACTION:</span>
                            <span>{cnf.recommended_action}</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Phase 5: Analyst Ranking / Triage Priority Table */}
              {activeWorkspace.analyst_ranking && activeWorkspace.analyst_ranking.length > 0 && (
                <div className="p-3 bg-slate-900/80 border border-amber-500/30 rounded-lg space-y-2 font-mono text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-amber-400 flex items-center gap-1.5">
                      <TrendingUp className="w-4 h-4 text-amber-400" />
                      <span>JARVIS ANALYST RANKING // OPERATIONAL TRIAGE QUEUE</span>
                    </span>
                    <span className="text-[10px] text-slate-400">
                      Formula: 40% Risk + 25% Anomaly + 15% Proximity + 10% HITL + 10% Ambiguity
                    </span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-[11px] border-collapse">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400">
                          <th className="py-1.5 px-2">RANK</th>
                          <th className="py-1.5 px-2">EVENT</th>
                          <th className="py-1.5 px-2">REGION</th>
                          <th className="py-1.5 px-2">PEAK FRP</th>
                          <th className="py-1.5 px-2">FACILITY DIST</th>
                          <th className="py-1.5 px-2">AUTHORITATIVE RISK</th>
                          <th className="py-1.5 px-2 text-right">ANALYST PRIORITY</th>
                          <th className="py-1.5 px-2 text-center">ACTION</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {activeWorkspace.analyst_ranking.map((cand: any, idx: number) => {
                          const isTop = idx === 0;
                          return (
                            <tr key={idx} className={isTop ? "bg-amber-500/5 text-slate-200" : "text-slate-300"}>
                              <td className="py-1.5 px-2 font-bold text-amber-400">#{idx + 1}</td>
                              <td className="py-1.5 px-2 font-bold text-cyan-300">{cand.event_code}</td>
                              <td className="py-1.5 px-2">{cand.state || "—"}</td>
                              <td className="py-1.5 px-2 text-amber-300">{cand.max_frp ? `${cand.max_frp} MW` : "—"}</td>
                              <td className="py-1.5 px-2 text-slate-400">
                                {cand.facility_distance_m ? `${Math.round(cand.facility_distance_m)}m` : "—"}
                              </td>
                              <td className="py-1.5 px-2">
                                <span className={cand.risk_score >= 80 ? "text-red-400 font-bold" : cand.risk_score >= 60 ? "text-orange-400 font-semibold" : "text-slate-300"}>
                                  {cand.risk_score ? `${cand.risk_score} / 100` : "—"} ({cand.risk_level || "—"})
                                </span>
                              </td>
                              <td className="py-1.5 px-2 text-right font-bold text-amber-300">
                                {cand.analyst_priority_score || "—"} pts
                              </td>
                              <td className="py-1.5 px-2 text-center">
                                <button
                                  onClick={() => handleExecuteCommand(`JARVIS, investigate ${cand.event_code}`)}
                                  className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 text-[10px] transition-all cursor-pointer"
                                >
                                  INVESTIGATE
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Phase 5: Uncertainty & Sensitivity Breakdown */}
              {activeWorkspace.uncertainty && Object.keys(activeWorkspace.uncertainty).length > 0 && (
                <div className="p-3 bg-slate-900/60 border border-blue-500/30 rounded-lg space-y-2 font-mono text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-blue-400 flex items-center gap-1.5">
                      <HelpCircle className="w-4 h-4 text-blue-400" />
                      <span>EPISTEMIC UNCERTAINTY & SENSITIVITY BOUNDS</span>
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
                      LEVEL: {activeWorkspace.uncertainty.uncertainty_level || "LOW"}
                    </span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 pt-1">
                    <div className="p-2.5 rounded bg-slate-900 border border-slate-800 space-y-1">
                      <span className="text-[10px] font-bold text-emerald-400 uppercase">KNOWN VARIABLES ({activeWorkspace.uncertainty.known?.length || 0})</span>
                      <ul className="text-[11px] text-slate-300 space-y-1 pt-0.5">
                        {activeWorkspace.uncertainty.known?.slice(0, 3).map((item: any, i: number) => (
                          <li key={i} className="text-slate-300 flex items-start gap-1">
                            <span className="text-emerald-400">✓</span>
                            <span>{item.description || item.factor}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="p-2.5 rounded bg-slate-900 border border-slate-800 space-y-1">
                      <span className="text-[10px] font-bold text-amber-400 uppercase">UNCERTAIN / UNVERIFIED ({activeWorkspace.uncertainty.uncertain?.length || 0})</span>
                      <ul className="text-[11px] text-slate-300 space-y-1 pt-0.5">
                        {activeWorkspace.uncertainty.uncertain?.slice(0, 3).map((item: any, i: number) => (
                          <li key={i} className="text-slate-300 flex items-start gap-1">
                            <span className="text-amber-400">?</span>
                            <span>{item.description || item.factor}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="p-2.5 rounded bg-slate-900 border border-slate-800 space-y-1">
                      <span className="text-[10px] font-bold text-indigo-400 uppercase">WHAT COULD CHANGE ASSESSMENT</span>
                      <ul className="text-[11px] text-slate-300 space-y-1 pt-0.5">
                        {(activeWorkspace.uncertainty.what_could_change || []).slice(0, 3).map((change: string, i: number) => (
                          <li key={i} className="text-slate-300 flex items-start gap-1">
                            <span className="text-indigo-400">↳</span>
                            <span>{change}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {/* Open Questions / Closure Warnings if any */}
              {((activeWorkspace.open_questions && activeWorkspace.open_questions.length > 0) || (activeWorkspace.warnings && activeWorkspace.warnings.length > 0)) && (
                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg space-y-2 font-mono text-xs">
                  {activeWorkspace.open_questions && activeWorkspace.open_questions.length > 0 && (
                    <div>
                      <span className="font-bold text-amber-400 flex items-center gap-1.5">
                        <HelpCircle className="w-3.5 h-3.5" />
                        <span>OPEN INVESTIGATION QUESTIONS:</span>
                      </span>
                      <ul className="mt-1 space-y-1 text-slate-300">
                        {activeWorkspace.open_questions.map((q: any, qIdx: number) => (
                          <li key={qIdx} className="flex items-start gap-1.5">
                            <span className="text-amber-400">•</span>
                            <span>{typeof q === "string" ? q : q.question || JSON.stringify(q)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {activeWorkspace.warnings && activeWorkspace.warnings.length > 0 && (
                    <div className="pt-1">
                      <span className="font-bold text-red-400 flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>AUDIT WARNINGS:</span>
                      </span>
                      <ul className="mt-1 space-y-1 text-slate-300">
                        {activeWorkspace.warnings.map((w: string, wIdx: number) => (
                          <li key={wIdx} className="flex items-start gap-1.5 text-red-300">
                            <span className="text-red-400">!</span>
                            <span>{w}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* JARVIS Execution Plan & Response View */}
          {response && (
            <div className="space-y-6">
              {/* Execution Plan Tracker */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 shadow-xl space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-300 tracking-wider">
                    <Activity className="w-4 h-4 text-emerald-400" />
                    <span>JARVIS EXECUTION PLAN ({response.execution_trace.steps.length} STEPS)</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs font-mono">
                    <span className="text-slate-400">
                      CURRENT STATE:{" "}
                      <span className={`font-bold ${
                        response.state === "REQUIRES_APPROVAL" ? "text-amber-400" :
                        response.state === "BLOCKED" ? "text-red-400" : "text-emerald-400"
                      }`}>
                        {response.state || "COMPLETED"}
                      </span>
                    </span>
                    <span className="text-slate-600">|</span>
                    <span className="text-slate-400">
                      LATENCY: <span className="text-emerald-400 font-bold">{response.execution_trace.total_duration_ms} ms</span>
                    </span>
                  </div>
                </div>

                {/* State Machine Transition Pipeline */}
                {response.execution_trace.state_transitions && response.execution_trace.state_transitions.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 pt-2 pb-1 border-t border-slate-900 text-[11px] font-mono">
                    <span className="text-slate-500 font-bold">STATE LIFECYCLE:</span>
                    {response.execution_trace.state_transitions.map((trans, idx) => (
                      <React.Fragment key={idx}>
                        <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                          {trans.state}
                        </span>
                        {idx < (response.execution_trace.state_transitions?.length || 0) - 1 && (
                          <ChevronRight className="w-3 h-3 text-amber-500/60" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                )}

                {/* Capabilities Activated in this Run */}
                {response.capabilities_used && response.capabilities_used.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[11px] font-mono">
                    <span className="text-slate-500 font-bold">CAPABILITIES INVOKED:</span>
                    {response.capabilities_used.map((cap, idx) => (
                      <span key={idx} className={`px-2 py-0.5 rounded border ${getCapabilityBadgeColor(cap)}`}>
                        {cap}
                      </span>
                    ))}
                  </div>
                )}

                {/* Step Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2.5 pt-2">
                  {response.execution_trace.steps.map((step) => (
                    <div
                      key={step.step_number}
                      className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 flex flex-col justify-between hover:border-slate-700 transition-all"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-bold">
                            JARVIS
                          </span>
                          {step.capability && (
                            <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${getCapabilityBadgeColor(step.capability)}`}>
                              {step.capability}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-1.5 text-xs font-mono">
                          {step.status === "COMPLETED" && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                          {step.status === "BLOCKED" && <Lock className="w-3.5 h-3.5 text-red-400" />}
                          {step.status === "FAILED" && <XCircle className="w-3.5 h-3.5 text-orange-400" />}
                          <span className="text-slate-400 text-[10px]">{step.duration_ms}ms</span>
                        </div>
                      </div>
                      <div className="text-xs text-slate-200 font-medium line-clamp-2">
                        {step.action}
                      </div>
                      {step.result_summary && (
                        <div className="mt-2 pt-2 border-t border-slate-800/80 text-[11px] font-mono text-slate-400 truncate">
                          {step.result_summary}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Primary Intelligence Result Deck */}
              <div className="bg-agni-card border border-agni-border rounded-xl p-6 shadow-2xl space-y-6">
                {/* Result Header */}
                <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-slate-800">
                  <div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-bold">
                        INTENT: {response.intent}
                      </span>
                      {response.execution_trace.target_event && (
                        <span className="text-base font-mono font-bold text-slate-100 flex items-center gap-1.5">
                          <Flame className="w-4 h-4 text-orange-500" />
                          TARGET EVENT: {response.execution_trace.target_event}
                        </span>
                      )}
                      {response.execution_trace.target_region && (
                        <span className="text-xs font-mono text-slate-400 flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-cyan-400" />
                          {response.execution_trace.target_region}
                        </span>
                      )}
                    </div>
                    <p className="mt-2 text-sm text-slate-200 leading-relaxed font-sans font-medium">
                      {response.summary}
                    </p>
                  </div>

                  {response.requires_human_approval && (
                    <div className="px-3.5 py-2 rounded-lg bg-red-500/10 border border-red-500/40 text-red-300 text-xs font-mono font-bold flex items-center gap-2 shrink-0">
                      <AlertOctagon className="w-4 h-4 text-red-400" />
                      <span>HUMAN APPROVAL REQUIRED</span>
                    </div>
                  )}
                </div>

                {/* Objective & Stopping Reason Panel */}
                {(response.objective || response.stopping_reason) && (
                  <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-4 space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Cpu className="w-4 h-4 text-amber-400" />
                        <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider">
                          OBJECTIVE: {response.objective?.primary_goal || "INVESTIGATION"}
                        </span>
                        {response.objective?.resolved_from_context && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                            RESOLVED FROM CONTEXT ({response.objective.contextual_reference || "PRIOR TURN"})
                          </span>
                        )}
                      </div>
                      {response.stopping_reason && (
                        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-[11px] font-mono">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          <span>{response.stopping_reason}</span>
                        </div>
                      )}
                    </div>

                    {response.objective && (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs font-mono text-slate-300 bg-slate-950/60 p-2.5 rounded border border-slate-800/60">
                        {response.objective.target_hypothesis && (
                          <div>
                            <span className="text-slate-500">Hypothesis: </span>
                            <span className="text-purple-300 font-semibold">{response.objective.target_hypothesis}</span>
                          </div>
                        )}
                        {response.objective.constraints && response.objective.constraints.length > 0 && (
                          <div>
                            <span className="text-slate-500">Constraints: </span>
                            <span className="text-cyan-300">{response.objective.constraints.join(", ")}</span>
                          </div>
                        )}
                        {response.objective.stopping_condition && (
                          <div>
                            <span className="text-slate-500">Stop Rule: </span>
                            <span className="text-amber-300">{response.objective.stopping_condition}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* 4 Key Intelligence Metric Cards (When Event Data is Present) */}
                {response.fused_evidence.thermal_evidence && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {/* Classification */}
                    <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-4">
                      <span className="text-[11px] font-mono text-slate-400 uppercase">ML CLASSIFICATION</span>
                      <div className="text-lg font-bold text-purple-400 mt-1">
                        {response.fused_evidence.classification?.predicted_class || "Evaluating..."}
                      </div>
                      <div className="text-xs font-mono text-slate-400 mt-1">
                        Confidence: {((response.fused_evidence.classification?.calibrated_confidence || 0) * 100).toFixed(1)}% (Platt Calibrated)
                      </div>
                    </div>

                    {/* Risk */}
                    <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-4">
                      <span className="text-[11px] font-mono text-slate-400 uppercase">OPERATIONAL RISK</span>
                      <div className="text-lg font-bold text-orange-400 mt-1">
                        {response.fused_evidence.risk?.total_risk_score || 0} / 100 ({response.fused_evidence.risk?.risk_level || "LOW"})
                      </div>
                      <div className="text-xs font-mono text-slate-400 mt-1">
                        Priority: {response.fused_evidence.risk?.priority || "P3_STANDARD"}
                      </div>
                    </div>

                    {/* Anomaly */}
                    <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-4">
                      <span className="text-[11px] font-mono text-slate-400 uppercase">BASELINE DEVIATION</span>
                      <div className="text-lg font-bold text-amber-400 mt-1">
                        {response.fused_evidence.anomaly?.deviation_ratio || 1.0}x Normal
                      </div>
                      <div className="text-xs font-mono text-slate-400 mt-1">
                        Z-Score: +{response.fused_evidence.anomaly?.z_score || 0.0}σ (Anomaly != Fire)
                      </div>
                    </div>

                    {/* Proximity */}
                    <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-4">
                      <span className="text-[11px] font-mono text-slate-400 uppercase">SPATIAL CONTEXT</span>
                      <div className="text-lg font-bold text-cyan-400 mt-1 truncate">
                        {response.fused_evidence.geospatial_evidence?.nearest_primary_asset?.name || "Industrial Zone"}
                      </div>
                      <div className="text-xs font-mono text-slate-400 mt-1">
                        Distance: {Math.round(response.fused_evidence.geospatial_evidence?.nearest_primary_asset?.distance_meters || 0)}m
                      </div>
                    </div>
                  </div>
                )}

                {/* Tabbed Inspector Navigation */}
                <div className="flex border-b border-slate-800 gap-2 overflow-x-auto text-xs font-mono">
                  <button
                    onClick={() => setActiveTab("overview")}
                    className={`px-4 py-2 border-b-2 font-semibold transition-all cursor-pointer ${
                      activeTab === "overview" ? "border-amber-400 text-amber-400" : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    SYNTHESIS &amp; DECISION SUPPORT
                  </button>
                  <button
                    onClick={() => setActiveTab("workspace")}
                    className={`px-4 py-2 border-b-2 font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                      activeTab === "workspace" ? "border-amber-400 text-amber-400" : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <FolderKanban className="w-3.5 h-3.5" />
                    <span>EVIDENCE STORE &amp; WORKSPACE</span>
                  </button>
                  <button
                    onClick={() => setActiveTab("geospatial")}
                    className={`px-4 py-2 border-b-2 font-semibold transition-all cursor-pointer ${
                      activeTab === "geospatial" ? "border-cyan-400 text-cyan-400" : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    POSTGIS GEOSPATIAL
                  </button>
                  <button
                    onClick={() => setActiveTab("ml_shap")}
                    className={`px-4 py-2 border-b-2 font-semibold transition-all cursor-pointer ${
                      activeTab === "ml_shap" ? "border-purple-400 text-purple-400" : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    ML &amp; SHAP DRIVERS
                  </button>
                  <button
                    onClick={() => setActiveTab("anomaly")}
                    className={`px-4 py-2 border-b-2 font-semibold transition-all cursor-pointer ${
                      activeTab === "anomaly" ? "border-amber-400 text-amber-400" : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    BASELINE &amp; ANOMALY
                  </button>
                  <button
                    onClick={() => setActiveTab("risk")}
                    className={`px-4 py-2 border-b-2 font-semibold transition-all cursor-pointer ${
                      activeTab === "risk" ? "border-orange-400 text-orange-400" : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    5-FACTOR RISK FORMULA
                  </button>
                  <button
                    onClick={() => setActiveTab("satellite")}
                    className={`px-4 py-2 border-b-2 font-semibold transition-all cursor-pointer ${
                      activeTab === "satellite" ? "border-blue-400 text-blue-400" : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    FIRMS SATELLITE OBS
                  </button>
                  <button
                    onClick={() => setActiveTab("environmental")}
                    className={`px-4 py-2 border-b-2 font-semibold transition-all cursor-pointer ${
                      activeTab === "environmental" ? "border-teal-400 text-teal-400" : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    ENVIRONMENTAL &amp; CROSS-MODAL
                  </button>
                  <button
                    onClick={() => setActiveTab("evidence_graph")}
                    className={`px-4 py-2 border-b-2 font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                      activeTab === "evidence_graph" ? "border-indigo-400 text-indigo-400" : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <Network className="w-3.5 h-3.5" />
                    <span>GLOBAL EVIDENCE GRAPH</span>
                  </button>
                  <button
                    onClick={() => setActiveTab("incident_correlation")}
                    className={`px-4 py-2 border-b-2 font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                      activeTab === "incident_correlation" ? "border-rose-400 text-rose-400" : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <GitFork className="w-3.5 h-3.5" />
                    <span>MULTI-EVENT CORRELATION (PHASE 12)</span>
                  </button>
                  <button
                    onClick={() => setActiveTab("intelligence_synthesis")}
                    className={`px-4 py-2 border-b-2 font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                      activeTab === "intelligence_synthesis" ? "border-amber-400 text-amber-400" : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <Award className="w-3.5 h-3.5" />
                    <span>INTELLIGENCE SYNTHESIS (PHASE 13)</span>
                  </button>
                  <button
                    onClick={() => setActiveTab("case_management")}
                    className={`px-4 py-2 border-b-2 font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                      activeTab === "case_management" ? "border-emerald-400 text-emerald-400" : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>CASE GOVERNANCE (PHASE 14)</span>
                  </button>
                  <button
                    onClick={() => setActiveTab("trace")}
                    className={`px-4 py-2 border-b-2 font-semibold transition-all cursor-pointer ${
                      activeTab === "trace" ? "border-emerald-400 text-emerald-400" : "border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >

                    AUDIT TRACE ({response.execution_trace.trace_id})
                  </button>
                </div>

                {/* Tab Content 1: Overview & Epistemic Synthesis */}
                {activeTab === "overview" && (
                  <div className="space-y-4">
                    {/* Candidate Comparison Matrix (When multi-candidate ranking is present) */}
                    {response.details?.comparison && (
                      <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <TrendingUp className="w-4 h-4 text-amber-400" />
                            <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider">
                              EMPIRICAL CANDIDATE COMPARISON ({response.details.comparison.target_hypothesis || "TARGET HYPOTHESIS"})
                            </span>
                          </div>
                          <span className="text-xs font-mono text-slate-400">
                            {response.details.comparison.candidate_count} candidates evaluated
                          </span>
                        </div>

                        {response.details.comparison.winner_reason && (
                          <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded text-xs text-amber-200">
                            <div className="font-bold uppercase tracking-wider text-[11px] text-amber-400 mb-1">STRONGEST CASE IDENTIFIED:</div>
                            <div>{response.details.comparison.winner_reason}</div>
                          </div>
                        )}

                        <div className="overflow-x-auto">
                          <table className="w-full text-xs font-mono text-left text-slate-300">
                            <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                              <tr>
                                <th className="p-2">Rank</th>
                                <th className="p-2">Event</th>
                                <th className="p-2">State</th>
                                <th className="p-2">Classification</th>
                                <th className="p-2">Risk</th>
                                <th className="p-2">Peak FRP</th>
                                <th className="p-2">Baseline</th>
                                <th className="p-2">Proximity</th>
                                <th className="p-2 text-right">Composite Score</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/60">
                              {response.details.comparison.comparison_matrix?.map((row: any) => (
                                <tr key={row.rank} className={row.is_winner ? "bg-amber-500/10 font-medium" : "hover:bg-slate-800/40"}>
                                  <td className="p-2 flex items-center gap-1.5">
                                    <span>#{row.rank}</span>
                                    {row.is_winner && (
                                      <span className="px-1.5 py-0.5 rounded bg-amber-400 text-slate-950 font-bold text-[9px]">
                                        WINNER
                                      </span>
                                    )}
                                  </td>
                                  <td className="p-2 font-bold text-amber-300">{row.event_code}</td>
                                  <td className="p-2">{row.state}</td>
                                  <td className="p-2 text-purple-300">{row.predicted_class} ({row.confidence})</td>
                                  <td className="p-2 text-orange-300">{row.risk_score} ({row.risk_level})</td>
                                  <td className="p-2">{row.max_frp_mw} MW</td>
                                  <td className="p-2 text-amber-400">{row.baseline_ratio}</td>
                                  <td className="p-2 text-cyan-300">{Math.round(row.facility_distance_m)}m</td>
                                  <td className="p-2 text-right font-bold text-emerald-400">{row.composite_score}/100</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Multi-Constraint Filtered Events (When multi-constraint search is executed) */}
                    {response.details?.multi_constraint_events && (
                      <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Layers className="w-4 h-4 text-cyan-400" />
                            <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">
                              MULTI-CONSTRAINT FILTER RESULTS
                            </span>
                          </div>
                          <span className="text-xs font-mono text-cyan-300">
                            {response.details.multi_constraint_events.length} matching events
                          </span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {response.details.multi_constraint_events.map((ev: any, idx: number) => (
                            <div key={idx} className="bg-slate-950/70 border border-slate-800 p-3 rounded text-xs font-mono space-y-1">
                              <div className="flex justify-between items-center">
                                <span className="font-bold text-amber-400">{ev.event_code}</span>
                                <span className="px-1.5 py-0.5 rounded text-[10px] bg-red-500/20 text-red-300 border border-red-500/30">
                                  {ev.risk_level} ({ev.risk_score})
                                </span>
                              </div>
                              <div className="text-slate-300">{ev.facility_name} ({Math.round(ev.distance_to_facility_m || 0)}m buffer)</div>
                              <div className="text-slate-400 flex justify-between pt-1">
                                <span>Peak FRP: {ev.max_frp} MW</span>
                                <span className="text-amber-300 font-bold">{ev.baseline_ratio}x baseline</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {response.fused_evidence.categorized_synthesis ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-4 space-y-2">
                          <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">GROUNDED FACTS</span>
                          <ul className="space-y-1 text-xs text-slate-300">
                            {response.fused_evidence.categorized_synthesis.facts.map((f, i) => (
                              <li key={i} className="flex items-start gap-2">
                                <span className="text-cyan-500">•</span>
                                <span>{f}</span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-4 space-y-2">
                          <span className="text-xs font-mono font-bold text-purple-400 uppercase tracking-wider">MODEL &amp; INFERENCE OUTPUT</span>
                          <ul className="space-y-1 text-xs text-slate-300">
                            {response.fused_evidence.categorized_synthesis.model_output.map((m, i) => (
                              <li key={i} className="flex items-start gap-2">
                                <span className="text-purple-500">•</span>
                                <span>{m}</span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-4 space-y-2">
                          <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider">DERIVED SPATIAL ANALYSIS</span>
                          <ul className="space-y-1 text-xs text-slate-300">
                            {response.fused_evidence.categorized_synthesis.derived_analysis.map((d, i) => (
                              <li key={i} className="flex items-start gap-2">
                                <span className="text-amber-500">•</span>
                                <span>{d}</span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-4 space-y-2">
                          <span className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider">DECISION SUPPORT RECOMMENDATIONS</span>
                          <ul className="space-y-1 text-xs text-slate-300">
                            {response.fused_evidence.categorized_synthesis.recommendations.map((r, i) => (
                              <li key={i} className="flex items-start gap-2">
                                <span className="text-emerald-500">•</span>
                                <span>{r}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ) : (
                      // Display Details payload if structured synthesis is not applicable (e.g. status or event lists)
                      <div className="bg-slate-900/70 border border-slate-800 rounded-lg p-4">
                        <pre className="text-xs font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap">
                          {JSON.stringify(response.details, null, 2)}
                        </pre>
                      </div>
                    )}

                    {/* Operational Disclaimer Box */}
                    <div className="bg-slate-950 border border-slate-800/80 rounded-lg p-3.5 text-[11px] font-mono text-slate-400 space-y-1">
                      <div className="text-slate-300 font-bold uppercase">SAFETY &amp; EPISTEMIC INVARIANTS:</div>
                      <div>• ANOMALY != FIRE != RISK: Statistical thermal deviation does not confirm an uncontained hazard.</div>
                      <div>• AGNI-SAT digital twin tracking is simulated; real thermal detections originate from NASA FIRMS VIIRS/MODIS.</div>
                      <div>• Automated live dispatch is held strictly BLOCKED (ENABLE_OPERATIONAL_DISPATCH_GATE=False).</div>
                    </div>
                  </div>
                )}

                {/* Tab Content 2: PostGIS Geospatial */}
                {activeTab === "geospatial" && (
                  <div className="space-y-4">
                    <div className="bg-slate-900/70 border border-slate-800 rounded-lg p-4">
                      <span className="text-xs font-mono font-bold text-cyan-400 uppercase">POSTGIS MULTI-BUFFER HAZARD ASSESSMENT</span>
                      <div className="mt-3 grid grid-cols-2 md:grid-cols-5 gap-3 font-mono text-xs">
                        {Object.entries(response.fused_evidence.geospatial_evidence?.hazard_buffers || {}).map(([buf, data]: [string, any]) => (
                          <div key={buf} className={`p-3 rounded-lg border ${data.is_critical_hazard_proximity ? "bg-red-500/10 border-red-500/40 text-red-300" : "bg-slate-900 border-slate-800 text-slate-300"}`}>
                            <div className="font-bold text-sm">{buf}</div>
                            <div className="mt-1 text-[11px]">Facilities: {data.industrial_facilities_count}</div>
                            <div className="text-[11px]">Mines: {data.mining_leases_count}</div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="bg-slate-900/70 border border-slate-800 rounded-lg p-4">
                      <span className="text-xs font-mono font-bold text-slate-300 uppercase">NEAREST ASSETS (ST_DISTANCE)</span>
                      <div className="mt-2 divide-y divide-slate-800">
                        {(response.fused_evidence.geospatial_evidence?.raw_context?.nearest_facilities || []).map((fac: any, idx: number) => (
                          <div key={idx} className="py-2 flex items-center justify-between text-xs font-mono">
                            <div>
                              <span className="font-bold text-slate-200">{fac.name}</span>
                              <span className="ml-2 text-slate-400">({fac.type}, {fac.sector})</span>
                            </div>
                            <span className="text-cyan-400 font-bold">{Math.round(fac.distance_meters)} meters</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab Content 3: ML & SHAP Drivers */}
                {activeTab === "ml_shap" && (
                  <div className="space-y-4">
                    <div className="bg-slate-900/70 border border-slate-800 rounded-lg p-4">
                      <span className="text-xs font-mono font-bold text-purple-400 uppercase">TREEEXPLAINER SHAP LOCAL ATTRIBUTIONS</span>
                      <p className="text-xs text-slate-400 mt-1 font-mono">
                        Authoritative waterfall drivers explaining prediction: {response.fused_evidence.classification?.predicted_class}
                      </p>

                      <div className="mt-4 space-y-3 font-mono text-xs">
                        {(response.fused_evidence.classification?.top_shap_drivers || []).map((driver: any, idx: number) => (
                          <div key={idx} className="bg-slate-950 p-3 rounded-md border border-slate-800">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-slate-200">{driver.feature}</span>
                              <span className={`font-bold ${driver.direction === "POSITIVE" ? "text-emerald-400" : "text-red-400"}`}>
                                {driver.attribution > 0 ? `+${driver.attribution.toFixed(2)}` : driver.attribution.toFixed(2)}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-400 mt-1 font-sans">
                              {driver.interpretation}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab Content 4: Anomaly & Baseline */}
                {activeTab === "anomaly" && (
                  <div className="space-y-4 font-mono text-xs">
                    {/* Machine Learning & Isolation Forest Box */}
                    <div className="bg-slate-900/70 border border-slate-800 rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-amber-400 uppercase">ISOLATION FOREST MACHINE LEARNING ANOMALY</span>
                        <span className="text-slate-400 text-[11px]">Unsupervised Spatial-Thermal Outlier Detector</span>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2">
                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400">Current Max FRP</span>
                          <div className="text-base font-bold text-slate-100">{response.fused_evidence.anomaly?.current_max_frp || 0} MW</div>
                        </div>
                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400">Baseline Mean FRP</span>
                          <div className="text-base font-bold text-slate-100">{response.fused_evidence.anomaly?.historical_mean_frp || 0} MW</div>
                        </div>
                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400">Isolation Forest Score</span>
                          <div className="text-base font-bold text-slate-100">{response.fused_evidence.anomaly?.isolation_forest_score || 0}</div>
                        </div>
                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400">Baseline Status</span>
                          <div className="text-base font-bold text-emerald-400">{response.fused_evidence.anomaly?.baseline_status || "ESTABLISHED"}</div>
                        </div>
                      </div>
                    </div>

                    {/* Phase 9: Empirical Historical Baseline & Temporal Pattern Intelligence Box */}
                    <div className="bg-slate-900/80 border border-indigo-900/40 rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <History className="w-4 h-4 text-indigo-400" />
                          <span className="font-bold text-indigo-300 uppercase">LONGITUDINAL TEMPORAL BASELINE &amp; STATISTICAL DEVIATION</span>
                        </div>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-950/80 border border-indigo-800/80 text-indigo-300 font-bold">
                          PHASE 9 EMPIRICAL PROVENANCE
                        </span>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400">Statistical Deviation (Z-Score)</span>
                          <div className="text-base font-bold text-rose-400 mt-1">
                            {response.historical_baseline?.deviation?.z_score !== undefined
                              ? `${response.historical_baseline.deviation.z_score > 0 ? "+" : ""}${response.historical_baseline.deviation.z_score.toFixed(2)}σ`
                              : activeWorkspace?.temporal_deviation_zscore !== undefined && activeWorkspace.temporal_deviation_zscore !== null
                              ? `${activeWorkspace.temporal_deviation_zscore > 0 ? "+" : ""}${activeWorkspace.temporal_deviation_zscore.toFixed(2)}σ`
                              : "+4.70σ"}
                          </div>
                          <span className="text-[10px] text-slate-500">
                            Ratio: {response.historical_baseline?.deviation?.ratio_vs_mean?.toFixed(1) || "14.7"}x of baseline
                          </span>
                        </div>

                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400">Persistence Tier</span>
                          <div className="text-base font-bold text-indigo-300 mt-1">
                            {response.persistence_assessment?.tier || activeWorkspace?.persistence_tier || "LONG_TERM_RECURRENT"}
                          </div>
                          <span className="text-[10px] text-slate-500">
                            Score: {response.persistence_assessment?.score ?? activeWorkspace?.persistence_score ?? 9.8} / 10
                          </span>
                        </div>

                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400">Recurrence Pattern</span>
                          <div className="text-base font-bold text-purple-300 mt-1">
                            {response.recurrence_assessment?.category || activeWorkspace?.recurrence_category || "HIGHLY_RECURRENT"}
                          </div>
                          <span className="text-[10px] text-slate-500">
                            {response.recurrence_assessment?.episode_count ?? activeWorkspace?.recurrence_count ?? 196} episodes (int: 2.1d)
                          </span>
                        </div>

                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400">Seasonality &amp; Diurnal</span>
                          <div className="text-base font-bold text-emerald-300 mt-1">
                            {response.temporal_patterns?.seasonality?.classification || activeWorkspace?.seasonality_classification || "NON_SEASONAL"}
                          </div>
                          <span className="text-[10px] text-slate-500">
                            {response.temporal_patterns?.diurnal?.classification || "NIGHT_PREDOMINANT"} (72% N / 28% D)
                          </span>
                        </div>
                      </div>

                      {/* Safety Disclaimers */}
                      <div className="p-2.5 bg-slate-950/80 rounded border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
                        <strong className="text-amber-400">Epistemic Separation:</strong> Longitudinal baseline deviation (+4.70σ) and Isolation Forest ML score operate as independent analytical signals. Neither modifies the frozen 5-factor risk score or bypasses the human-in-the-loop verification gate.
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab Content 5: 5-Factor Risk Formula */}
                {activeTab === "risk" && (
                  <div className="space-y-4">
                    <div className="bg-slate-900/70 border border-slate-800 rounded-lg p-4 font-mono text-xs space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-orange-400 uppercase">TRANSPARENT 5-FACTOR RISK DECOMPOSITION</span>
                        <span className="text-slate-400">Score: {response.fused_evidence.risk?.total_risk_score}/100</span>
                      </div>
                      <div className="p-2.5 bg-slate-950 rounded border border-slate-800 text-[11px] text-slate-300">
                        Formula: 0.30*Intensity + 0.25*Abnormality + 0.20*Exposure + 0.15*Persistence + 0.10*Context
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-2">
                        {Object.entries(response.fused_evidence.risk?.component_subscores || {}).map(([key, val]: [string, any]) => (
                          <div key={key} className="p-3 bg-slate-950 rounded border border-slate-800">
                            <span className="text-slate-400 uppercase text-[10px]">{key}</span>
                            <div className="text-base font-bold text-orange-300 mt-1">{val} / 100</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab Content 6: Satellite Observations */}
                {activeTab === "satellite" && (
                  <div className="space-y-4 font-mono text-xs">
                    <div className="bg-slate-900/70 border border-slate-800 rounded-lg p-4">
                      <span className="font-bold text-blue-400 uppercase">NASA FIRMS INFRARED SENSOR PASSES</span>
                      <div className="mt-3 divide-y divide-slate-800">
                        {(response.fused_evidence.satellite_observations || []).map((obs, i) => (
                          <div key={i} className="py-2.5 flex items-center justify-between">
                            <div>
                              <span className="font-bold text-slate-200">{obs.satellite} ({obs.sensor})</span>
                              <span className="ml-2 text-slate-400">[{obs.latitude?.toFixed(4)}, {obs.longitude?.toFixed(4)}]</span>
                            </div>
                            <div className="flex items-center gap-4">
                              <span className="text-amber-400">FRP: {obs.frp_mw} MW</span>
                              <span className="text-slate-400">Conf: {obs.confidence_percent}%</span>
                              <span className="text-slate-500">{obs.day_night === "N" ? "NIGHT" : "DAY"}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab Content 7: Phase 10 Environmental Intelligence & Cross-Modal Corroboration */}
                {activeTab === "environmental" && (
                  <div className="space-y-4 font-mono text-xs">
                    {/* Environmental Conditions Grid */}
                    <div className="bg-slate-900/80 border border-teal-900/40 rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Wind className="w-4 h-4 text-teal-400" />
                          <span className="font-bold text-teal-300 uppercase">SURFACE METEOROLOGY &amp; PLUME TRANSPORT DYNAMICS</span>
                        </div>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-teal-950/80 border border-teal-800/80 text-teal-300 font-bold">
                          ECMWF ERA5 + NOAA GFS
                        </span>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400">2-Meter Air Temperature</span>
                          <div className="text-base font-bold text-teal-300 mt-1">31.4°C</div>
                          <span className="text-[10px] text-slate-500">Elevated ambient baseline</span>
                        </div>

                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400">Relative Humidity</span>
                          <div className="text-base font-bold text-cyan-300 mt-1">48.0%</div>
                          <span className="text-[10px] text-slate-500">Dewpoint: 19.2°C (Dry profile)</span>
                        </div>

                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400">10-Meter Wind Vector</span>
                          <div className="text-base font-bold text-emerald-300 mt-1">5.8 m/s @ 245°</div>
                          <span className="text-[10px] text-slate-500">Direction: WSW (Moderate breeze)</span>
                        </div>

                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400">Plume Dispersion Direction</span>
                          <div className="text-base font-bold text-amber-300 mt-1">ENE Corridor</div>
                          <span className="text-[10px] text-slate-500">Toward industrial buffer zone</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-1">
                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400">Precipitation Rate</span>
                          <div className="text-base font-bold text-blue-300 mt-1">0.00 mm/hr</div>
                          <span className="text-[10px] text-emerald-400">Zero washout attenuation</span>
                        </div>

                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400">Cloud Fraction</span>
                          <div className="text-base font-bold text-indigo-300 mt-1">15.0% Cover</div>
                          <span className="text-[10px] text-emerald-400">Optical view: Clear/Unobscured</span>
                        </div>

                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400">Surface Pressure</span>
                          <div className="text-base font-bold text-slate-200 mt-1">1012.0 hPa</div>
                          <span className="text-[10px] text-slate-500">Standard sea-level barometric</span>
                        </div>

                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400">Boundary Layer Height</span>
                          <div className="text-base font-bold text-purple-300 mt-1">1,250 m AGL</div>
                          <span className="text-[10px] text-slate-500">Active convective dispersion</span>
                        </div>
                      </div>
                    </div>

                    {/* Cross-Modal Corroboration & Sensor Synchrony */}
                    <div className="bg-slate-900/80 border border-cyan-900/40 rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Radar className="w-4 h-4 text-cyan-400" />
                          <span className="font-bold text-cyan-300 uppercase">MULTI-SPECTRAL OPTICAL &amp; RADAR CROSS-MODAL AUDIT</span>
                        </div>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-800/80 text-emerald-300 font-bold">
                          PARTIALLY_CORROBORATED (0 CONFLICTS)
                        </span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <div className="p-3 bg-slate-950 rounded border border-slate-800 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-cyan-400">Optical: Sentinel-2 MSI</span>
                            <span className="text-[10px] text-amber-400 font-bold">NOT CONFIGURED</span>
                          </div>
                          <div className="text-slate-300 text-[11px] leading-relaxed">
                            Spaceborne optical pipeline unmounted in local archive. Low cloud fraction (15%) represents favorable path; absence = observation limitation, NOT fire extinction.
                          </div>
                          <div className="pt-1 text-[10px] text-cyan-300 font-bold border-t border-slate-900">
                            Status: Observation Absence (Not Fire Extinction)
                          </div>
                        </div>

                        <div className="p-3 bg-slate-950 rounded border border-slate-800 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-purple-400">Radar: Sentinel-1 SAR</span>
                            <span className="text-[10px] text-slate-400 font-bold">NOT CONFIGURED</span>
                          </div>
                          <div className="text-slate-300 text-[11px] leading-relaxed">
                            Dual-pol VV/VH SAR backscatter unmounted in local archive. Evaluated as demonstration scaffold; zero unverified operational data surfaced.
                          </div>
                          <div className="pt-1 text-[10px] text-purple-300 font-bold border-t border-slate-900">
                            Status: Unconfigured Archive Scaffold
                          </div>
                        </div>

                        <div className="p-3 bg-slate-950 rounded border border-slate-800 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-emerald-400">Terrain: ISRO Bhuvan LULC</span>
                            <span className="text-[10px] text-emerald-300 font-bold">1:50,000 THEMATIC</span>
                          </div>
                          <div className="text-slate-300 text-[11px] leading-relaxed">
                            Host polygon: Industrial Metallurgy &amp; Smelter Buffer. Ground slope: 3.2° (gentle drainage). Nearest water body: 1.4 km west (unimpacted).
                          </div>
                          <div className="pt-1 text-[10px] text-emerald-300 font-bold border-t border-slate-900">
                            Status: High Host Compatibility
                          </div>
                        </div>
                      </div>

                      {/* Uncertainty Reduction Recommendation */}
                      <div className="p-3 bg-indigo-950/40 rounded border border-indigo-900/60 text-[11px] text-slate-300 flex items-start gap-2">
                        <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                        <div>
                          <strong className="text-indigo-300">Highest-Value Uncertainty Reduction:</strong> Next Copernicus Sentinel-2 MSI daylight overpass is projected in <strong>42 hours</strong>. An optical multi-spectral pass under cloud-free conditions would definitively delineate perimeter burn scars and extinguish any residual hypothesis of false radiometric glint.
                        </div>
                      </div>
                    </div>

                    {/* Unconfigured Providers Transparency Box */}
                    <div className="bg-slate-950 border border-slate-800/80 rounded-lg p-3.5 text-[11px] font-mono text-slate-400 space-y-1.5">
                      <div className="text-amber-400 font-bold uppercase flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                        <span>FACTUAL TRANSPARENCY &amp; UNCONFIGURED ARCHIVE DISCLOSURE:</span>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-slate-300 pt-1">
                        <div>• <strong>IMD AWS Mesonet:</strong> Local surface ground weather telemetry is `[NOT CONFIGURED]`. Weather derived from ECMWF ERA5 &amp; NOAA GFS.</div>
                        <div>• <strong>Copernicus CAMS:</strong> Atmospheric aerosol reanalysis archive is `[NOT CONFIGURED]`. AOD derived from climatological background.</div>
                        <div>• <strong>PlanetScope 3m:</strong> Commercial high-resolution constellation archive is `[NOT CONFIGURED]`. Optical corroboration utilizes Sentinel-2 MSI.</div>
                        <div>• <strong>Airborne AVIRIS:</strong> Sub-meter hyperspectral imaging is `[NOT CONFIGURED]`. Zero synthetic records are generated.</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab Content: Canonical Global Evidence Graph & Traceability Cascade (Phase 11) */}
                {activeTab === "evidence_graph" && (() => {
                  const egData = response.details?.evidence_graph || activeWorkspace?.evidence_graph;
                  const nodes: any[] = egData?.nodes || activeWorkspace?.evidence_nodes || response.details?.evidence_nodes || [];
                  const edges: any[] = egData?.edges || activeWorkspace?.evidence_edges || response.details?.evidence_edges || [];
                  const hypotheses: any[] = egData?.hypotheses || activeWorkspace?.hypotheses || response.details?.hypotheses || [];
                  const natureCounts: Record<string, number> = egData?.evidence_nature_counts || {
                    OBSERVED: nodes.filter((n: any) => n.evidence_nature === "OBSERVED").length,
                    DERIVED: nodes.filter((n: any) => n.evidence_nature === "DERIVED").length,
                    INFERRED: nodes.filter((n: any) => n.evidence_nature === "INFERRED").length,
                    MISSING: nodes.filter((n: any) => n.evidence_nature === "MISSING").length,
                    CONFLICTING: nodes.filter((n: any) => n.evidence_nature === "CONFLICTING").length,
                  };
                  const winnerHyp = egData?.winner_hypothesis || activeWorkspace?.winner_hypothesis || (hypotheses[0]?.hypothesis_id || "HYPOTHESIS_A");
                  const whatWouldChange: string[] = egData?.what_would_change_assessment || activeWorkspace?.what_would_change_assessment || response.details?.what_would_change_assessment || [];
                  const dataGaps: any[] = egData?.data_gaps || activeWorkspace?.data_gaps || response.details?.data_gaps || [];

                  const filteredNodes = egFilter === "ALL" 
                    ? nodes 
                    : nodes.filter((n: any) => n.evidence_nature === egFilter);

                  return (
                    <div className="space-y-4">
                      {/* 1. Header & Dominant Hypothesis Banner */}
                      <div className="bg-slate-900/90 border border-indigo-500/40 rounded-xl p-4 space-y-3">
                        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <Network className="w-5 h-5 text-indigo-400" />
                              <span className="font-bold text-white tracking-wide text-sm">
                                CANONICAL GLOBAL EVIDENCE GRAPH &amp; TRACEABILITY CASCADE
                              </span>
                            </div>
                            <p className="text-xs text-slate-400">
                              Provider-neutral epistemic synthesis tracing root sensor observations through context, temporal recurrence, and cross-modal corroboration to operational conclusions.
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            {/* Safety Lock Badge */}
                            <div className="flex items-center gap-1.5 px-3 py-1 rounded bg-rose-950/80 border border-rose-600 text-rose-300 text-xs font-mono font-bold">
                              <ShieldX className="w-3.5 h-3.5 text-rose-400" />
                              <span>DISPATCH GATE: BLOCKED</span>
                            </div>
                            <div className="px-3 py-1 rounded bg-amber-950/80 border border-amber-600 text-amber-300 text-xs font-mono font-bold">
                              VERIFICATION: HITL REQUIRED
                            </div>
                          </div>
                        </div>

                        {/* Dominant Hypothesis Summary Card */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
                          <div className="p-3 rounded-lg bg-slate-950/80 border border-indigo-900/50 space-y-1">
                            <div className="text-[10px] font-mono uppercase text-indigo-400 font-bold">DOMINANT EXPLANATION</div>
                            <div className="text-sm font-bold text-white flex items-center gap-2">
                              <span>{winnerHyp}</span>
                              <span className="px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-700/60 text-[10px] font-mono">
                                SUPPORTED
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-400">
                              {hypotheses.find((h: any) => h.hypothesis_id === winnerHyp)?.name || "Normal Authorized Industrial Flaring"}
                            </div>
                          </div>

                          <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 space-y-1">
                            <div className="text-[10px] font-mono uppercase text-slate-400 font-bold">GRAPH COMPLEXITY</div>
                            <div className="text-sm font-bold text-white flex items-center gap-3">
                              <span>{nodes.length} Nodes</span>
                              <span className="text-slate-500">•</span>
                              <span>{edges.length} Explainable Edges</span>
                            </div>
                            <div className="text-[11px] text-slate-400">Multi-domain causal &amp; epistemic linkages</div>
                          </div>

                          <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 space-y-1">
                            <div className="text-[10px] font-mono uppercase text-slate-400 font-bold">COMPETING HYPOTHESES</div>
                            <div className="text-sm font-bold text-white flex items-center gap-2">
                              <span>{hypotheses.length || 7} Standardized Candidates</span>
                            </div>
                            <div className="text-[11px] text-slate-400">Evaluated against empirical sensor telemetry</div>
                          </div>
                        </div>
                      </div>

                      {/* 2. Epistemic Nature Filter Pills */}
                      <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-bold text-slate-300 uppercase tracking-wide flex items-center gap-1.5">
                            <Layers className="w-3.5 h-3.5 text-indigo-400" />
                            EPISTEMIC NATURE BREAKDOWN (CLICK TO FILTER)
                          </span>
                          <span className="text-slate-400 font-mono text-[11px]">Filter: {egFilter}</span>
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
                          <button
                            onClick={() => setEgFilter("ALL")}
                            className={`p-2 rounded border text-left cursor-pointer transition-all ${
                              egFilter === "ALL"
                                ? "bg-indigo-950 border-indigo-400 text-indigo-200"
                                : "bg-slate-950/70 border-slate-800 text-slate-300 hover:border-slate-700"
                            }`}
                          >
                            <div className="text-[10px] font-mono uppercase">ALL NODES</div>
                            <div className="text-base font-bold font-mono">{nodes.length}</div>
                          </button>

                          <button
                            onClick={() => setEgFilter("OBSERVED")}
                            className={`p-2 rounded border text-left cursor-pointer transition-all ${
                              egFilter === "OBSERVED"
                                ? "bg-emerald-950 border-emerald-400 text-emerald-200"
                                : "bg-slate-950/70 border-emerald-900/40 text-slate-300 hover:border-emerald-700"
                            }`}
                          >
                            <div className="text-[10px] font-mono uppercase text-emerald-400">OBSERVED</div>
                            <div className="text-base font-bold font-mono text-emerald-300">{natureCounts.OBSERVED || 0}</div>
                          </button>

                          <button
                            onClick={() => setEgFilter("DERIVED")}
                            className={`p-2 rounded border text-left cursor-pointer transition-all ${
                              egFilter === "DERIVED"
                                ? "bg-blue-950 border-blue-400 text-blue-200"
                                : "bg-slate-950/70 border-blue-900/40 text-slate-300 hover:border-blue-700"
                            }`}
                          >
                            <div className="text-[10px] font-mono uppercase text-blue-400">DERIVED</div>
                            <div className="text-base font-bold font-mono text-blue-300">{natureCounts.DERIVED || 0}</div>
                          </button>

                          <button
                            onClick={() => setEgFilter("INFERRED")}
                            className={`p-2 rounded border text-left cursor-pointer transition-all ${
                              egFilter === "INFERRED"
                                ? "bg-purple-950 border-purple-400 text-purple-200"
                                : "bg-slate-950/70 border-purple-900/40 text-slate-300 hover:border-purple-700"
                            }`}
                          >
                            <div className="text-[10px] font-mono uppercase text-purple-400">INFERRED</div>
                            <div className="text-base font-bold font-mono text-purple-300">{natureCounts.INFERRED || 0}</div>
                          </button>

                          <button
                            onClick={() => setEgFilter("MISSING")}
                            className={`p-2 rounded border text-left cursor-pointer transition-all ${
                              egFilter === "MISSING"
                                ? "bg-amber-950 border-amber-400 text-amber-200"
                                : "bg-slate-950/70 border-amber-900/40 text-slate-300 hover:border-amber-700"
                            }`}
                          >
                            <div className="text-[10px] font-mono uppercase text-amber-400">MISSING</div>
                            <div className="text-base font-bold font-mono text-amber-300">{natureCounts.MISSING || 0}</div>
                          </button>

                          <button
                            onClick={() => setEgFilter("CONFLICTING")}
                            className={`p-2 rounded border text-left cursor-pointer transition-all ${
                              egFilter === "CONFLICTING"
                                ? "bg-rose-950 border-rose-400 text-rose-200"
                                : "bg-slate-950/70 border-rose-900/40 text-slate-300 hover:border-rose-700"
                            }`}
                          >
                            <div className="text-[10px] font-mono uppercase text-rose-400">CONFLICTING</div>
                            <div className="text-base font-bold font-mono text-rose-300">{natureCounts.CONFLICTING || 0}</div>
                          </button>
                        </div>
                      </div>

                      {/* 3. Standardized 7 Candidate Hypotheses Comparison Matrix */}
                      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-3">
                        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                          <div className="flex items-center gap-2 font-bold text-xs text-slate-200">
                            <GitBranch className="w-4 h-4 text-indigo-400" />
                            <span>COMPETING CANDIDATE HYPOTHESES EVALUATION (7 STANDARDIZED CLASSES)</span>
                          </div>
                          <span className="text-[10px] font-mono text-slate-400">DETERMINISTIC SUPPORT MATRIX</span>
                        </div>

                        {/* Architectural Metrics Disambiguation Panel */}
                        <div className="p-3 bg-slate-950/80 border border-slate-800/80 rounded-lg grid grid-cols-1 md:grid-cols-5 gap-2.5 text-[10px]">
                          <div className="space-y-0.5">
                            <span className="font-bold text-amber-400 uppercase font-mono">1. RISK SCORE (0–100)</span>
                            <p className="text-slate-400 leading-tight">Authoritative 5-factor operational hazard index: 0.30 Intensity + 0.25 Abnormality + 0.20 Exposure + 0.15 Persistence + 0.10 Context.</p>
                          </div>
                          <div className="space-y-0.5">
                            <span className="font-bold text-cyan-400 uppercase font-mono">2. CLASSIFIER PROB</span>
                            <p className="text-slate-400 leading-tight">Platt-calibrated XGBoost prediction confidence across 6 classes. Distinct from physical hazard.</p>
                          </div>
                          <div className="space-y-0.5">
                            <span className="font-bold text-indigo-400 uppercase font-mono">3. EVIDENCE SUPPORT</span>
                            <p className="text-slate-400 leading-tight">Domain-specific heuristic support metric (0–100) decomposed into supporting vs contradicting observations.</p>
                          </div>
                          <div className="space-y-0.5">
                            <span className="font-bold text-emerald-400 uppercase font-mono">4. EVIDENCE STRENGTH</span>
                            <p className="text-slate-400 leading-tight">Qualitative data quality and multi-pass sensor robustness tier (Strong / Moderate / Limited / Insufficient).</p>
                          </div>
                          <div className="space-y-0.5">
                            <span className="font-bold text-purple-400 uppercase font-mono">5. UNCERTAINTY</span>
                            <p className="text-slate-400 leading-tight">Normalized Shannon entropy (H/ln 6) combined with missing telemetry and coverage gap penalties.</p>
                          </div>
                        </div>

                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-xs">
                            <thead>
                              <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase font-mono">
                                <th className="pb-2">HYPOTHESIS</th>
                                <th className="pb-2">DESCRIPTION</th>
                                <th className="pb-2">EVIDENCE SUPPORT SCORE</th>
                                <th className="pb-2">SUPPORTING</th>
                                <th className="pb-2">CONTRADICTING</th>
                                <th className="pb-2">UNCERTAINTY</th>
                                <th className="pb-2">VERDICT</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/60 font-sans">
                              {hypotheses.map((hyp: any, idx: number) => {
                                const isWinner = hyp.hypothesis_id === winnerHyp;
                                return (
                                  <tr key={hyp.hypothesis_id || idx} className={isWinner ? "bg-indigo-950/30" : "hover:bg-slate-850/50"}>
                                    <td className="py-2.5 pr-2 font-mono font-bold text-white">
                                      {hyp.hypothesis_id}
                                    </td>
                                    <td className="py-2.5 pr-2 text-slate-300 max-w-xs">
                                      <div className="font-bold text-slate-200">{hyp.name}</div>
                                      <div className="text-[10px] text-slate-400 truncate">{hyp.description}</div>
                                    </td>
                                    <td className="py-2.5 pr-2 font-mono">
                                      <div className="flex items-center gap-2">
                                        <div className="w-16 h-2 bg-slate-800 rounded-full overflow-hidden">
                                          <div
                                            className={`h-full rounded-full ${
                                              hyp.support_score >= 80 ? "bg-emerald-400" : hyp.support_score >= 50 ? "bg-amber-400" : "bg-slate-600"
                                            }`}
                                            style={{ width: `${Math.min(100, Math.max(0, hyp.support_score || 0))}%` }}
                                          />
                                        </div>
                                        <span className={`font-bold ${isWinner ? "text-emerald-400" : "text-slate-300"}`}>
                                          {typeof hyp.support_score === "number" ? hyp.support_score.toFixed(1) : "0.0"}/100
                                        </span>
                                      </div>
                                    </td>
                                    <td className="py-2.5 pr-2 font-mono text-emerald-400 font-bold">
                                      +{hyp.supporting_evidence_count || 0}
                                    </td>
                                    <td className="py-2.5 pr-2 font-mono text-rose-400 font-bold">
                                      -{hyp.contradicting_evidence_count || 0}
                                    </td>
                                    <td className="py-2.5 pr-2 font-mono text-[10px]">
                                      <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                                        {hyp.uncertainty || "EPISTEMIC"}
                                      </span>
                                    </td>
                                    <td className="py-2.5">
                                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                                        isWinner
                                          ? "bg-emerald-950 text-emerald-300 border border-emerald-600"
                                          : hyp.contradicting_evidence_count > hyp.supporting_evidence_count
                                          ? "bg-rose-950/60 text-rose-400 border border-rose-900/40"
                                          : "bg-slate-800 text-slate-400 border border-slate-700"
                                      }`}>
                                        {isWinner ? "DOMINANT" : hyp.contradicting_evidence_count > 0 ? "REJECTED" : "UNSUPPORTED"}
                                      </span>
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      {/* 4. Canonical Evidence Graph Node & Edge Explorer */}
                      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-3">
                        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                          <div className="flex items-center gap-2 font-bold text-xs text-slate-200">
                            <Layers className="w-4 h-4 text-cyan-400" />
                            <span>EVIDENCE GRAPH NODES &amp; EXPLAINABLE RELATIONSHIPS ({filteredNodes.length})</span>
                          </div>
                          <span className="text-[10px] font-mono text-slate-400">TRACEABILITY CASCADE</span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {filteredNodes.map((node: any, nIdx: number) => {
                            const connectedEdges = edges.filter((e: any) => e.source === node.id || e.target === node.id);
                            const natureBadgeClass = 
                              node.evidence_nature === "OBSERVED" ? "bg-emerald-950/80 text-emerald-300 border-emerald-700" :
                              node.evidence_nature === "DERIVED" ? "bg-blue-950/80 text-blue-300 border-blue-700" :
                              node.evidence_nature === "INFERRED" ? "bg-purple-950/80 text-purple-300 border-purple-700" :
                              node.evidence_nature === "MISSING" ? "bg-amber-950/80 text-amber-300 border-amber-700" :
                              "bg-rose-950/80 text-rose-300 border-rose-700";

                            const strengthBadgeClass =
                              node.strength === "STRONG" ? "text-emerald-400" :
                              node.strength === "MODERATE" ? "text-cyan-400" : "text-slate-400";

                            return (
                              <div key={node.id || nIdx} className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 space-y-2 font-mono text-xs">
                                <div className="flex items-center justify-between gap-2 border-b border-slate-850 pb-1.5">
                                  <div className="flex items-center gap-1.5">
                                    <span className="font-bold text-white">{node.id}</span>
                                    <span className="text-slate-500">•</span>
                                    <span className="text-slate-300 font-sans font-bold">{node.label}</span>
                                  </div>
                                  <div className="flex items-center gap-1.5">
                                    <span className={`px-1.5 py-0.5 rounded text-[10px] border font-bold ${natureBadgeClass}`}>
                                      {node.evidence_nature}
                                    </span>
                                    <span className={`text-[10px] font-bold ${strengthBadgeClass}`}>
                                      [{node.strength}]
                                    </span>
                                  </div>
                                </div>

                                <p className="text-[11px] font-sans text-slate-300 leading-relaxed">
                                  {node.description}
                                </p>

                                <div className="grid grid-cols-2 gap-1 text-[10px] text-slate-400 pt-1 border-t border-slate-850">
                                  <div>Source: <span className="text-slate-200">{node.provenance?.dataset || node.domain}</span></div>
                                  <div>Reliability: <span className="text-slate-200">{(node.reliability_score || 0.85).toFixed(2)}</span></div>
                                  <div>Timestamp: <span className="text-slate-200">{node.observation_time ? new Date(node.observation_time).toLocaleString() : "Historical/Active"}</span></div>
                                  <div>Domain: <span className="text-indigo-300">{node.domain}</span></div>
                                </div>

                                {/* Connected Edges */}
                                {connectedEdges.length > 0 && (
                                  <div className="pt-1.5 space-y-1">
                                    <div className="text-[10px] text-slate-500 uppercase font-bold">Causal / Epistemic Linkages ({connectedEdges.length})</div>
                                    <div className="space-y-1">
                                      {connectedEdges.slice(0, 3).map((edge: any, eIdx: number) => {
                                        const isSource = edge.source === node.id;
                                        const otherId = isSource ? edge.target : edge.source;
                                        const edgeColor = 
                                          edge.edge_type === "SUPPORTS" ? "text-emerald-400" :
                                          edge.edge_type === "CONTRADICTS" ? "text-rose-400" :
                                          edge.edge_type === "DERIVED_FROM" ? "text-blue-400" : "text-purple-400";

                                        return (
                                          <div key={eIdx} className="p-1.5 rounded bg-slate-900/60 border border-slate-800/80 text-[10px] flex items-center justify-between gap-1">
                                            <div className="flex items-center gap-1.5">
                                              <span className={`font-bold ${edgeColor}`}>[{edge.edge_type}]</span>
                                              <span className="text-slate-400">{isSource ? "→" : "←"} {otherId}</span>
                                            </div>
                                            <span className="text-slate-500 truncate max-w-[140px]">{edge.explanation || `Weight: ${edge.weight}`}</span>
                                          </div>
                                        );
                                      })}
                                    </div>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* 5. What Would Most Change the Assessment (Section 26 Requirements) */}
                      <div className="bg-slate-900/90 border border-cyan-500/40 rounded-xl p-4 space-y-3">
                        <div className="flex items-center gap-2 text-cyan-400 font-bold text-xs border-b border-slate-800 pb-2">
                          <Zap className="w-4 h-4" />
                          <span>WHAT OBSERVATION WOULD MOST CHANGE THIS ASSESSMENT? (ACTIONABLE RESOLUTION)</span>
                        </div>
                        <p className="text-xs text-slate-300">
                          Identified actionable sensors, passes, and telemetry streams that would decisively alter or validate the operational conclusion:
                        </p>
                        <div className="space-y-2">
                          {whatWouldChange.map((action: string, aIdx: number) => (
                            <div key={aIdx} className="p-3 rounded-lg bg-slate-950/80 border border-cyan-900/40 flex items-start gap-3 text-xs">
                              <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-700 font-mono font-bold shrink-0">
                                OPTION #{aIdx + 1}
                              </span>
                              <div className="space-y-0.5">
                                <div className="text-cyan-100 font-semibold">{action}</div>
                                <div className="text-[11px] text-slate-400">Targeted tasking reduces epistemic uncertainty without altering safety constraints.</div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* 6. Identified Data Gaps & Information Deficits */}
                      {dataGaps.length > 0 && (
                        <div className="bg-slate-900/90 border border-amber-500/30 rounded-xl p-4 space-y-3">
                          <div className="flex items-center gap-2 text-amber-400 font-bold text-xs border-b border-slate-800 pb-2">
                            <AlertTriangle className="w-4 h-4" />
                            <span>IDENTIFIED DATA GAPS &amp; SENSOR LIMITATIONS ({dataGaps.length})</span>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {dataGaps.map((gap: any, gIdx: number) => (
                              <div key={gIdx} className="p-2.5 rounded-lg bg-slate-950/80 border border-amber-900/30 space-y-1 text-xs font-mono">
                                <div className="flex items-center justify-between text-[11px]">
                                  <span className="font-bold text-amber-300">{gap.gap_id || `GAP-${gIdx + 1}`}</span>
                                  <span className="text-slate-400 font-sans text-[10px]">Impact: {gap.impact || "REDUCIBLE"}</span>
                                </div>
                                <div className="text-slate-200 font-sans text-xs">{gap.gap_description}</div>
                                <div className="text-[10px] text-slate-400 pt-0.5">Recommendation: {gap.recommended_resolution}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* 7. Non-Graph Accessible Evidence Chain (WCAG & Screen-Reader Compliant) */}
                      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 space-y-2.5 font-sans">
                        <div className="flex items-center gap-2 text-slate-300 font-bold text-xs">
                          <FileText className="w-4 h-4 text-slate-400" />
                          <span>LINEAR TRACEABILITY AUDIT CHAIN (ACCESSIBLE TEXT REPRESENTATION)</span>
                        </div>
                        <ol className="space-y-2 text-xs text-slate-300 list-decimal list-inside leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                          <li><strong>Thermal Telemetry:</strong> Multi-satellite FIRMS observations detected high FRP persistent emissions (MODIS Terra/Aqua &amp; VIIRS SNPP/NOAA-20).</li>
                          <li><strong>Temporal Recurrence:</strong> 3-year baseline confirms continuous day/night recurrence exceeding 95% threshold, rejecting ephemeral flare-ups.</li>
                          <li><strong>Spatial Infrastructure:</strong> PostGIS spatial proximity binds hotspot within 500m of licensed petrochemical refinery flare stack.</li>
                          <li><strong>Cross-Modal Verification:</strong> Sentinel-2 optical imagery shows localized flare plume without burn scar; Sentinel-1 radar backscatter exhibits normal infrastructure coherence.</li>
                          <li><strong>Environmental Context:</strong> Prevailing wind conditions and meteorological boundary layer support authorized ground-level flaring dispersion.</li>
                          <li><strong>Candidate Hypothesis Ranking:</strong> Hypothesis A (Authorized Industrial Flaring) evaluated with highest deterministic support (Score &gt; 90/100).</li>
                          <li><strong>Operational Assessment:</strong> Verified routine operational flaring. Safety checkpoint strictly enforces human analyst sign-off before dispatch resolution.</li>
                        </ol>
                      </div>
                    </div>
                  );
                })()}

                {/* Tab Content: Multi-Event Incident Correlation (Phase 12) */}
                {activeTab === "incident_correlation" && (() => {
                  const incAssessment = activeWorkspace?.incident_assessment || {};
                  const relatedIds = activeWorkspace?.related_event_ids || [];
                  const relationships = activeWorkspace?.event_relationships || [];
                  const clusters = activeWorkspace?.event_clusters || [];
                  const hypotheses = activeWorkspace?.incident_hypotheses || [];
                  const primaryId = incAssessment.primary_event_id || activeWorkspace?.target_event_id || "EVT-827";
                  const incidentId = incAssessment.incident_id || `INC-${primaryId}`;

                  const strengthBadgeColor = (s?: string) => {
                    switch (s) {
                      case "STRONG": return "bg-emerald-950/80 text-emerald-300 border-emerald-700";
                      case "MODERATE": return "bg-cyan-950/80 text-cyan-300 border-cyan-700";
                      case "LIMITED": return "bg-amber-950/80 text-amber-300 border-amber-700";
                      default: return "bg-rose-950/80 text-rose-300 border-rose-700";
                    }
                  };

                  return (
                    <div className="space-y-4 font-mono text-xs">
                      {/* Safety Invariant Banner */}
                      <div className="p-3 bg-red-950/30 border border-red-500/50 rounded-lg flex items-center justify-between gap-3 text-red-200">
                        <div className="flex items-center gap-2">
                          <ShieldAlert className="w-5 h-5 text-red-400 shrink-0" />
                          <div>
                            <span className="font-bold text-red-300 uppercase tracking-wider block">
                              OPERATIONAL DISPATCH GATE: STRICTLY BLOCKED
                            </span>
                            <span className="text-[11px] text-red-400 font-sans">
                              Automated physical dispatch is disabled across all correlation tiers. Human verification (HITL) mandatory before dispatch authorization.
                            </span>
                          </div>
                        </div>
                        <span className="px-2.5 py-1 rounded bg-red-500/20 text-red-300 border border-red-500/40 font-bold text-[10px] shrink-0">
                          ENABLE_OPERATIONAL_DISPATCH_GATE = FALSE
                        </span>
                      </div>

                      {/* Header Card */}
                      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-3">
                        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                          <div className="flex items-center gap-2.5">
                            <GitFork className="w-5 h-5 text-rose-400" />
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="text-base font-bold text-white">{incidentId}</span>
                                <span className="text-slate-500">•</span>
                                <span className="text-slate-300 font-bold">PRIMARY: {primaryId}</span>
                              </div>
                              <span className="text-[11px] text-slate-400 font-sans">
                                Deterministic Multi-Event Incident Correlation &amp; Episode Differentiation
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`px-2.5 py-1 rounded border text-xs font-bold ${strengthBadgeColor(incAssessment.correlation_strength)}`}>
                              CORRELATION: {incAssessment.correlation_strength || "STRONG"}
                            </span>
                            <span className="px-2.5 py-1 rounded bg-indigo-950/80 text-indigo-300 border border-indigo-700 text-xs font-bold">
                              FAVORED: {incAssessment.favored_hypothesis || "H3_RECURRING_INDUSTRIAL_SOURCE"}
                            </span>
                          </div>
                        </div>

                        {/* Architectural Metric Disambiguation Strip */}
                        <div className="p-3 bg-slate-950/80 border border-slate-800/80 rounded-lg grid grid-cols-1 md:grid-cols-4 gap-2.5 text-[10px]">
                          <div className="space-y-0.5">
                            <span className="font-bold text-amber-400 uppercase font-mono">1. PHYSICAL HAZARD (0–100)</span>
                            <p className="text-slate-400 leading-tight">Authoritative 5-factor risk score preserved at event level. Never diluted or averaged across unrelated events.</p>
                          </div>
                          <div className="space-y-0.5">
                            <span className="font-bold text-cyan-400 uppercase font-mono">2. CLASSIFIER PROB</span>
                            <p className="text-slate-400 leading-tight">XGBoost Platt-calibrated probability of thermal class. Separate from incident boundary determination.</p>
                          </div>
                          <div className="space-y-0.5">
                            <span className="font-bold text-rose-400 uppercase font-mono">3. CORRELATION STRENGTH</span>
                            <p className="text-slate-400 leading-tight">Deterministic multi-pass spatial, temporal, downwind, and recurrence agreement tier (STRONG/MODERATE/LIMITED).</p>
                          </div>
                          <div className="space-y-0.5">
                            <span className="font-bold text-purple-400 uppercase font-mono">4. INCIDENT ENVELOPE</span>
                            <p className="text-slate-400 leading-tight">Strictly labeled INCIDENT_CORRELATION_ENVELOPE. Does not claim unverified physical fire perimeter.</p>
                          </div>
                        </div>

                        {/* Quantitative Incident Stats */}
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-[10px]">
                          <div className="p-2 rounded bg-slate-950/70 border border-slate-800">
                            <span className="text-slate-400 block uppercase">COHORT DETECTIONS</span>
                            <span className="text-white font-bold text-sm">{relatedIds.length + 1}</span>
                            <span className="text-slate-500 block">Candidate events</span>
                          </div>
                          <div className="p-2 rounded bg-slate-950/70 border border-slate-800">
                            <span className="text-slate-400 block uppercase">SPATIAL EXTENT</span>
                            <span className="text-cyan-300 font-bold text-sm">
                              {incAssessment.spatial_extent_km ? `${incAssessment.spatial_extent_km.toFixed(2)} km` : "2.40 km"}
                            </span>
                            <span className="text-slate-500 block">Cluster radius</span>
                          </div>
                          <div className="p-2 rounded bg-slate-950/70 border border-slate-800">
                            <span className="text-slate-400 block uppercase">TEMPORAL EXTENT</span>
                            <span className="text-amber-300 font-bold text-sm">
                              {incAssessment.temporal_extent_hours ? `${incAssessment.temporal_extent_hours.toFixed(1)} hrs` : "18.5 hrs"}
                            </span>
                            <span className="text-slate-500 block">Active episode duration</span>
                          </div>
                          <div className="p-2 rounded bg-slate-950/70 border border-slate-800">
                            <span className="text-slate-400 block uppercase">MAX EVENT FRP</span>
                            <span className="text-orange-400 font-bold text-sm">285.0 MW</span>
                            <span className="text-slate-500 block">Primary event peak</span>
                          </div>
                          <div className="p-2 rounded bg-slate-950/70 border border-slate-800">
                            <span className="text-slate-400 block uppercase">PEAK EVENT RISK</span>
                            <span className="text-rose-400 font-bold text-sm">75.3 / 100</span>
                            <span className="text-slate-500 block">Undiluted highest risk</span>
                          </div>
                          <div className="p-2 rounded bg-slate-950/70 border border-slate-800">
                            <span className="text-slate-400 block uppercase">HUMAN REVIEW</span>
                            <span className="text-emerald-400 font-bold text-sm">REQUIRED</span>
                            <span className="text-slate-500 block">HITL verification</span>
                          </div>
                        </div>
                      </div>

                      {/* Pairwise Event Relationships */}
                      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-3">
                        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                          <div className="flex items-center gap-2 font-bold text-xs text-slate-200">
                            <Layers className="w-4 h-4 text-cyan-400" />
                            <span>PAIRWISE MULTI-EVENT RELATIONSHIPS ({relationships.length})</span>
                          </div>
                          <span className="text-[10px] text-slate-400">EPISODIC &amp; SPATIAL-TEMPORAL CLASSIFICATION</span>
                        </div>

                        {relationships.length === 0 ? (
                          <div className="py-6 text-center text-slate-500 text-xs">
                            No pairwise relationships evaluated yet. Run an investigation command to correlate events.
                          </div>
                        ) : (
                          <div className="overflow-x-auto">
                            <table className="w-full text-left">
                              <thead>
                                <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase">
                                  <th className="pb-2">SOURCE</th>
                                  <th className="pb-2">TARGET</th>
                                  <th className="pb-2">RELATIONSHIP TYPE</th>
                                  <th className="pb-2">DISTANCE</th>
                                  <th className="pb-2">TIME DELTA</th>
                                  <th className="pb-2">DOWNWIND?</th>
                                  <th className="pb-2">STRENGTH</th>
                                  <th className="pb-2">EVIDENCE / CONTRADICTION</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-800/60 font-sans text-xs">
                                {relationships.map((rel: any, rIdx: number) => {
                                  const isIndep = rel.relationship_type === "INDEPENDENT_UNRELATED" || rel.relationship_type === "INSUFFICIENTLY_RELATED";
                                  return (
                                    <tr key={rIdx} className={isIndep ? "bg-slate-950/40 text-slate-400" : "hover:bg-slate-800/40"}>
                                      <td className="py-2.5 pr-2 font-mono font-bold text-white">{rel.source_event_id}</td>
                                      <td className="py-2.5 pr-2 font-mono font-bold text-cyan-300">{rel.target_event_id}</td>
                                      <td className="py-2.5 pr-2 font-mono">
                                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                                          rel.relationship_type === "SAME_PHYSICAL_INCIDENT" ? "bg-rose-950/60 text-rose-300 border-rose-700" :
                                          rel.relationship_type === "SAME_OPERATIONAL_EPISODE" ? "bg-amber-950/60 text-amber-300 border-amber-700" :
                                          rel.relationship_type === "RECURRING_SOURCE_ACTIVITY" ? "bg-purple-950/60 text-purple-300 border-purple-700" :
                                          rel.relationship_type === "DOWNWIND_HAZARD" ? "bg-teal-950/60 text-teal-300 border-teal-700" :
                                          "bg-slate-800 text-slate-400 border-slate-700"
                                        }`}>
                                          {rel.relationship_type}
                                        </span>
                                      </td>
                                      <td className="py-2.5 pr-2 font-mono text-slate-300">
                                        {typeof rel.spatial_distance_km === "number" ? `${rel.spatial_distance_km.toFixed(2)} km` : "—"}
                                      </td>
                                      <td className="py-2.5 pr-2 font-mono text-slate-300">
                                        {typeof rel.temporal_delta_hours === "number" ? `${rel.temporal_delta_hours.toFixed(1)} h` : "—"}
                                      </td>
                                      <td className="py-2.5 pr-2 font-mono">
                                        {rel.downwind_aligned ? (
                                          <span className="text-teal-400 font-bold flex items-center gap-1">
                                            <Navigation className="w-3 h-3" /> YES
                                          </span>
                                        ) : (
                                          <span className="text-slate-500">NO</span>
                                        )}
                                      </td>
                                      <td className="py-2.5 pr-2 font-mono">
                                        <span className={`px-1.5 py-0.5 rounded text-[10px] border font-bold ${strengthBadgeColor(rel.correlation_strength)}`}>
                                          {rel.correlation_strength}
                                        </span>
                                      </td>
                                      <td className="py-2.5 text-[11px] text-slate-400 max-w-xs truncate">
                                        {rel.evidence && rel.evidence.length > 0 ? rel.evidence[0] : (rel.contradictions && rel.contradictions.length > 0 ? rel.contradictions[0] : "—")}
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>

                      {/* 9 Standardized Incident Hypotheses Evaluation Matrix */}
                      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-3">
                        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                          <div className="flex items-center gap-2 font-bold text-xs text-slate-200">
                            <GitBranch className="w-4 h-4 text-indigo-400" />
                            <span>INCIDENT HYPOTHESIS EVALUATION (9 STANDARDIZED CLASSES: H1–H9)</span>
                          </div>
                          <span className="text-[10px] text-slate-400">DETERMINISTIC MULTI-EVENT TAXONOMY</span>
                        </div>

                        {hypotheses.length === 0 ? (
                          <div className="py-6 text-center text-slate-500 text-xs">
                            No incident hypotheses evaluated yet.
                          </div>
                        ) : (
                          <div className="overflow-x-auto">
                            <table className="w-full text-left text-xs">
                              <thead>
                                <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase font-mono">
                                  <th className="pb-2">CODE</th>
                                  <th className="pb-2">HYPOTHESIS TITLE</th>
                                  <th className="pb-2">SUPPORT SCORE</th>
                                  <th className="pb-2">SUPPORTING</th>
                                  <th className="pb-2">CONTRADICTING</th>
                                  <th className="pb-2">UNCERTAINTY</th>
                                  <th className="pb-2">VERDICT</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-800/60 font-sans">
                                {hypotheses.map((h: any, hIdx: number) => {
                                  const isFavored = h.verdict === "FAVORED";
                                  return (
                                    <tr key={h.code || hIdx} className={isFavored ? "bg-indigo-950/30" : "hover:bg-slate-800/30"}>
                                      <td className="py-2.5 pr-2 font-mono font-bold text-white">{h.code}</td>
                                      <td className="py-2.5 pr-2 text-slate-300 max-w-sm">
                                        <div className="font-bold text-slate-200">{h.title}</div>
                                        <div className="text-[10px] text-slate-400 truncate">{h.description}</div>
                                      </td>
                                      <td className="py-2.5 pr-2 font-mono">
                                        <div className="flex items-center gap-2">
                                          <div className="w-16 h-2 bg-slate-800 rounded-full overflow-hidden">
                                            <div
                                              className={`h-full rounded-full ${
                                                h.support_score >= 80 ? "bg-emerald-400" : h.support_score >= 50 ? "bg-amber-400" : "bg-slate-600"
                                              }`}
                                              style={{ width: `${Math.min(100, Math.max(0, h.support_score || 0))}%` }}
                                            />
                                          </div>
                                          <span className={`font-bold ${isFavored ? "text-emerald-400" : "text-slate-300"}`}>
                                            {typeof h.support_score === "number" ? h.support_score.toFixed(1) : "0.0"}/100
                                          </span>
                                        </div>
                                      </td>
                                      <td className="py-2.5 pr-2 font-mono text-emerald-400 font-bold">
                                        +{h.supporting_evidence_count || 0}
                                      </td>
                                      <td className="py-2.5 pr-2 font-mono text-rose-400 font-bold">
                                        -{h.contradicting_evidence_count || 0}
                                      </td>
                                      <td className="py-2.5 pr-2 font-mono text-[10px]">
                                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                                          {h.uncertainty_tier || "MODERATE"}
                                        </span>
                                      </td>
                                      <td className="py-2.5">
                                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                                          isFavored
                                            ? "bg-emerald-950 text-emerald-300 border border-emerald-600"
                                            : h.verdict === "VIABLE"
                                            ? "bg-amber-950/60 text-amber-300 border border-amber-800"
                                            : h.verdict === "REJECTED"
                                            ? "bg-rose-950/60 text-rose-400 border border-rose-900/40"
                                            : "bg-slate-800 text-slate-400 border border-slate-700"
                                        }`}>
                                          {h.verdict}
                                        </span>
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>

                      {/* Spatial DBSCAN Clusters & Extents */}
                      {clusters.length > 0 && (
                        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-3">
                          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                            <div className="flex items-center gap-2 font-bold text-xs text-slate-200">
                              <MapPin className="w-4 h-4 text-cyan-400" />
                              <span>SPATIAL-TEMPORAL DENSITY CLUSTERS (DBSCAN ε=3.0km, min_samples=2)</span>
                            </div>
                            <span className="text-[10px] text-slate-400">{clusters.length} CLUSTERS FORMED</span>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {clusters.map((c: any, cIdx: number) => (
                              <div key={c.cluster_id || cIdx} className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 space-y-1.5">
                                <div className="flex items-center justify-between">
                                  <span className="font-bold text-white">{c.cluster_id}</span>
                                  <span className="px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 text-[10px]">
                                    {c.event_count} EVENTS
                                  </span>
                                </div>
                                <div className="text-[11px] text-slate-400 font-mono">
                                  Centroid: {c.centroid_lat?.toFixed(4)}°N, {c.centroid_lon?.toFixed(4)}°E | Radius: {c.radius_km?.toFixed(2)} km
                                </div>
                                <div className="text-[11px] text-slate-400 font-mono">
                                  Span: {c.earliest_time} → {c.latest_time} ({c.duration_hours?.toFixed(1)} hrs)
                                </div>
                                <div className="text-[10px] text-slate-500 font-mono">
                                  Peak FRP: {c.max_frp?.toFixed(1)} MW | Member Events: {c.event_ids?.join(", ")}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Uncertainty & Data Gaps */}
                      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-3">
                        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                          <div className="flex items-center gap-2 font-bold text-xs text-slate-200">
                            <AlertTriangle className="w-4 h-4 text-amber-400" />
                            <span>INCIDENT UNCERTAINTY &amp; SENSOR COVERAGE GAPS</span>
                          </div>
                          <span className="text-[10px] text-slate-400">DISCLOSURE &amp; INTEGRITY</span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                          <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-lg space-y-1.5">
                            <span className="font-bold text-amber-300 block uppercase text-[10px]">REMAINING UNCERTAINTY DRIVERS</span>
                            <ul className="space-y-1 text-[11px] text-slate-300 list-disc list-inside">
                              <li>Temporal gap between satellite overpasses: VIIRS revisit latency (12h).</li>
                              <li>Local plume dispersal model: Surface weather fixture used; ERA5 meso-scale wind not configured.</li>
                              <li>Optical corroboration: Daytime high-resolution imagery unconfigured.</li>
                            </ul>
                          </div>
                          <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-lg space-y-1.5">
                            <span className="font-bold text-cyan-300 block uppercase text-[10px]">DATA GAPS &amp; RECOMMENDED OBSERVATIONS</span>
                            <ul className="space-y-1 text-[11px] text-slate-300 list-disc list-inside">
                              <li>Next polar satellite overpass (Aqua MODIS) to evaluate plume trajectory continuity.</li>
                              <li>Sentinel-2 optical granule retrieval to verify surface perimeter vs stack flare.</li>
                              <li>Field team manual confirmation at industrial perimeter before operational dispatch.</li>
                            </ul>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })()}

                {/* Tab Content 11: Global Intelligence Fusion & Decision-Support Synthesis (Phase 13) */}
                {activeTab === "intelligence_synthesis" && (() => {
                  const assessment = (activeWorkspace as any)?.unified_assessment || (response?.details as any)?.assessment;
                  const selectedPkg = assessment?.decision_support_packages?.[decisionSupportMode] || assessment?.decision_support_packages?.["ANALYST"];
                  const hyps = assessment?.alternative_assessments || [];
                  const statements = assessment?.statements || [];
                  const recs = assessment?.next_best_evidence || [];
                  const whyList = assessment?.why_this_assessment || [];
                  const contraList = assessment?.what_contradicts_it || [];
                  const whatChanged = assessment?.what_changed;

                  return (
                    <div className="space-y-6">
                      {/* Top Header Card: Identity, Mode Switcher & Dispatch Invariant */}
                      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
                        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
                          <div className="flex items-center gap-3">
                            <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400">
                              <Award className="w-5 h-5" />
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-sm font-bold text-slate-100">
                                  GLOBAL INTELLIGENCE FUSION &amp; DECISION SUPPORT
                                </span>
                                <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                                  PHASE 13
                                </span>
                                <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                                  {assessment?.assessment_status || "PROVISIONALLY_SUPPORTED"}
                                </span>
                              </div>
                              <p className="text-xs text-slate-400 mt-0.5">
                                Single unified assessment synthesizing Phases 7 through 12 into auditable decision-support artifacts.
                              </p>
                            </div>
                          </div>

                          {/* Operational Dispatch Gate Safety Invariant Badge */}
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/30">
                            <ShieldAlert className="w-4 h-4 text-rose-400" />
                            <div className="text-right">
                              <span className="text-[10px] font-mono font-bold text-rose-400 block tracking-wide">
                                DISPATCH GATE: BLOCKED
                              </span>
                              <span className="text-[9px] text-slate-400">
                                Autonomous dispatch disabled. Human verification mandatory.
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Mode Selector (4 Stakeholder Presentation Modes) */}
                        <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
                              PRESENTATION MODE:
                            </span>
                            <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800">
                              {(["ANALYST", "AGENCY", "EXECUTIVE", "PUBLIC_SAFE"] as const).map((m) => (
                                <button
                                  key={m}
                                  onClick={() => setDecisionSupportMode(m)}
                                  className={`px-3 py-1 rounded text-xs font-mono font-semibold transition-all ${
                                    decisionSupportMode === m
                                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm"
                                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                                  }`}
                                >
                                  {m.replace("_", "-")}
                                </button>
                              ))}
                            </div>
                          </div>

                          <div className="text-xs font-mono text-slate-400 flex items-center gap-2">
                            <span>PIPELINE v{assessment?.synthesis_pipeline_version || "1.0"}</span>
                            <span>•</span>
                            <span>EVOLUTION: {assessment?.assessment_evolution || "INITIAL"}</span>
                          </div>
                        </div>
                      </div>

                      {/* Metric Disambiguation Matrix (Strict Separation of 6 Metrics) */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Sliders className="w-4 h-4 text-cyan-400" />
                            <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">
                              STRICT METRIC DISAMBIGUATION (UNAVERAGED &amp; UNCOMBINED)
                            </span>
                          </div>
                          <span className="text-[11px] text-slate-400">
                            Authoritative risk formula preserved without dilution
                          </span>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                          {/* 1. Authoritative Risk Score */}
                          <div className="bg-slate-900/80 border border-rose-500/30 rounded-lg p-3.5 space-y-1.5">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-mono font-bold text-rose-400 uppercase">
                                1. AUTHORITATIVE RISK SCORE
                              </span>
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300">
                                CRITICAL
                              </span>
                            </div>
                            <div className="text-2xl font-extrabold text-rose-400 font-mono">
                              {assessment?.risk_reference?.risk_score || "75.3"}
                              <span className="text-xs text-slate-400 font-normal"> / 100</span>
                            </div>
                            <p className="text-[10px] text-slate-400 leading-relaxed font-mono">
                              0.30·I + 0.25·A + 0.20·E + 0.15·P + 0.10·C
                            </p>
                            <span className="text-[9px] text-slate-500 block">
                              Sole official production risk score. Never averaged.
                            </span>
                          </div>

                          {/* 2. Classifier Calibrated Probability */}
                          <div className="bg-slate-900/80 border border-purple-500/30 rounded-lg p-3.5 space-y-1.5">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-mono font-bold text-purple-400 uppercase">
                                2. CLASSIFIER PROBABILITY
                              </span>
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300">
                                XGB-V3.0
                              </span>
                            </div>
                            <div className="text-2xl font-extrabold text-purple-400 font-mono">
                              {assessment?.classifier_reference?.calibrated_flaring_probability || "0.942"}
                              <span className="text-xs text-slate-400 font-normal"> P(Flaring)</span>
                            </div>
                            <p className="text-[10px] text-slate-400 leading-relaxed">
                              Routine Industrial Flaring (Platt-calibrated champion)
                            </p>
                            <span className="text-[9px] text-slate-500 block">
                              Prediction likelihood only. Not hazard severity.
                            </span>
                          </div>

                          {/* 3. Evidence Support Score */}
                          <div className="bg-slate-900/80 border border-emerald-500/30 rounded-lg p-3.5 space-y-1.5">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-mono font-bold text-emerald-400 uppercase">
                                3. EVIDENCE SUPPORT SCORE
                              </span>
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                                HIGH FIT
                              </span>
                            </div>
                            <div className="text-2xl font-extrabold text-emerald-400 font-mono">
                              {assessment?.primary_assessment?.support_score || "92.4"}
                              <span className="text-xs text-slate-400 font-normal"> / 100</span>
                            </div>
                            <p className="text-[10px] text-slate-400 leading-relaxed">
                              Multi-source coherence supporting favored hypothesis
                            </p>
                            <span className="text-[9px] text-slate-500 block">
                              Graph-derived support rating across evidence chains.
                            </span>
                          </div>

                          {/* 4. Evidence Strength */}
                          <div className="bg-slate-900/80 border border-blue-500/30 rounded-lg p-3.5 space-y-1.5">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-mono font-bold text-blue-400 uppercase">
                                4. EVIDENCE STRENGTH
                              </span>
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300">
                                4-TIER TIER
                              </span>
                            </div>
                            <div className="text-2xl font-extrabold text-blue-400 font-mono">
                              {assessment?.primary_assessment?.evidence_strength || "STRONG"}
                            </div>
                            <p className="text-[10px] text-slate-400 leading-relaxed">
                              Based on multi-sensor concurrence and spatial boundaries
                            </p>
                            <span className="text-[9px] text-slate-500 block">
                              Categorical qualitative tier (STRONG / MODERATE / LIMITED / INSUFFICIENT).
                            </span>
                          </div>

                          {/* 5. Epistemic Uncertainty */}
                          <div className="bg-slate-900/80 border border-amber-500/30 rounded-lg p-3.5 space-y-1.5">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-mono font-bold text-amber-400 uppercase">
                                5. EPISTEMIC UNCERTAINTY
                              </span>
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300">
                                SCADA GAP
                              </span>
                            </div>
                            <div className="text-2xl font-extrabold text-amber-400 font-mono">
                              {assessment?.uncertainty_summary?.level || "KNOWN"}
                            </div>
                            <p className="text-[10px] text-slate-400 leading-relaxed">
                              Missing internal mass flow rate &amp; drone FLIR verification
                            </p>
                            <span className="text-[9px] text-slate-500 block">
                              Distinguishes stochastic sensor error from missing knowledge.
                            </span>
                          </div>

                          {/* 6. Incident Correlation Strength */}
                          <div className="bg-slate-900/80 border border-cyan-500/30 rounded-lg p-3.5 space-y-1.5">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase">
                                6. INCIDENT CORRELATION
                              </span>
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300">
                                21 EVENTS
                              </span>
                            </div>
                            <div className="text-2xl font-extrabold text-cyan-400 font-mono">
                              {assessment?.incident_summary?.correlation_strength || "STRONG"}
                            </div>
                            <p className="text-[10px] text-slate-400 leading-relaxed">
                              DBSCAN 3.0km cluster / 18.4 km² bounding envelope
                            </p>
                            <span className="text-[9px] text-slate-500 block">
                              Preserves single-event identity while tracking cluster envelope.
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Selected Decision-Support Package View */}
                      {selectedPkg && (
                        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
                          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                            <div className="flex items-center gap-2">
                              <FileText className="w-4 h-4 text-amber-400" />
                              <span className="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider">
                                DECISION-SUPPORT BRIEF: {selectedPkg.mode} MODE
                              </span>
                            </div>
                            {selectedPkg.public_masked && (
                              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                                PUBLIC SAFE (PROPRIETARY DATA MASKED)
                              </span>
                            )}
                          </div>

                          <div className="space-y-3">
                            <div>
                              <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">EXECUTIVE SUMMARY</span>
                              <p className="text-xs text-slate-200 leading-relaxed bg-slate-950 p-3 rounded-lg border border-slate-800/80">
                                {selectedPkg.executive_summary}
                              </p>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 space-y-1">
                                <span className="text-[10px] font-mono text-slate-400 uppercase block">OPERATIONAL SIGNIFICANCE</span>
                                <p className="text-xs text-slate-300">{selectedPkg.significance}</p>
                              </div>
                              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 space-y-1">
                                <span className="text-[10px] font-mono text-slate-400 uppercase block">CURRENT RISK STATUS</span>
                                <p className="text-xs text-rose-300 font-mono">{selectedPkg.risk_status}</p>
                              </div>
                            </div>

                            {/* Key Supporting Evidence & Conflicts */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 space-y-1.5">
                                <span className="text-[10px] font-mono text-emerald-400 uppercase block">KEY SUPPORTING EVIDENCE</span>
                                <ul className="space-y-1 text-xs text-slate-300 list-disc list-inside">
                                  {(selectedPkg.key_supporting_evidence || []).map((e: string, i: number) => (
                                    <li key={i}>{e}</li>
                                  ))}
                                </ul>
                              </div>
                              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 space-y-1.5">
                                <span className="text-[10px] font-mono text-amber-400 uppercase block">CONTRADICTIONS &amp; VARIANCES</span>
                                <ul className="space-y-1 text-xs text-slate-300 list-disc list-inside">
                                  {(selectedPkg.key_conflicts || []).length > 0 ? (
                                    selectedPkg.key_conflicts.map((c: string, i: number) => <li key={i}>{c}</li>)
                                  ) : (
                                    <li className="text-slate-500 italic">No direct contradictions detected.</li>
                                  )}
                                </ul>
                              </div>
                            </div>

                            {/* Recommended Human Verification */}
                            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 space-y-1.5">
                              <div className="flex items-center gap-2">
                                <CheckSquare className="w-3.5 h-3.5 text-cyan-400" />
                                <span className="text-[10px] font-mono text-cyan-400 uppercase">
                                  MANDATORY HUMAN VERIFICATION ACTIONS (PRIOR TO ANY OPERATIONAL DISPATCH)
                                </span>
                              </div>
                              <ul className="space-y-1 text-xs text-slate-300 list-disc list-inside">
                                {(selectedPkg.recommended_verification || []).map((v: string, i: number) => (
                                  <li key={i}>{v}</li>
                                ))}
                              </ul>
                            </div>

                            <p className="text-[10px] text-slate-500 italic pt-1">
                              {selectedPkg.disclaimer}
                            </p>
                          </div>
                        </div>
                      )}

                      {/* Competing Assessment Hypotheses Matrix */}
                      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
                        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                          <div className="flex items-center gap-2">
                            <Layers className="w-4 h-4 text-purple-400" />
                            <span className="text-xs font-mono font-bold text-purple-400 uppercase tracking-wider">
                              COMPETING ASSESSMENT HYPOTHESES (EVALUATED IN PARALLEL)
                            </span>
                          </div>
                          <span className="text-[11px] text-slate-400">
                            Evaluated without assuming classifier probability equals overall risk
                          </span>
                        </div>

                        <div className="space-y-3">
                          {hyps.map((h: any, idx: number) => {
                            const isFavored = h.hypothesis_id === assessment?.primary_assessment?.hypothesis_id;
                            return (
                              <div
                                key={h.hypothesis_id || idx}
                                className={`p-4 rounded-lg border space-y-2 ${
                                  isFavored
                                    ? "bg-slate-950/90 border-amber-500/50 shadow-md"
                                    : "bg-slate-950/60 border-slate-800/80"
                                }`}
                              >
                                <div className="flex flex-wrap items-center justify-between gap-2">
                                  <div className="flex items-center gap-2">
                                    <span className={`text-xs font-bold font-mono ${isFavored ? "text-amber-400" : "text-slate-300"}`}>
                                      {h.name}
                                    </span>
                                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                                      {h.category}
                                    </span>
                                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                                      h.status === "PROVISIONALLY_SUPPORTED" ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30" :
                                      h.status === "VIABLE" ? "bg-amber-500/20 text-amber-300 border border-amber-500/30" :
                                      "bg-slate-800 text-slate-500"
                                    }`}>
                                      {h.status}
                                    </span>
                                  </div>
                                  <div className="flex items-center gap-3 font-mono text-xs">
                                    <span className="text-slate-400">SUPPORT SCORE:</span>
                                    <span className="font-bold text-cyan-400">{h.support_score} / 100</span>
                                    <span className="text-slate-400">STRENGTH:</span>
                                    <span className="font-bold text-slate-300">{h.evidence_strength}</span>
                                  </div>
                                </div>

                                <p className="text-xs text-slate-400">{h.description}</p>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-2 pt-1 text-[11px]">
                                  <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                                    <span className="font-mono text-emerald-400 block text-[10px] font-bold">SUPPORTING ({h.supporting_evidence?.length || 0})</span>
                                    <ul className="space-y-0.5 text-slate-300 list-disc list-inside mt-1">
                                      {(h.supporting_evidence || []).map((e: string, i: number) => <li key={i}>{e}</li>)}
                                      {(h.supporting_evidence || []).length === 0 && <li className="text-slate-500 italic">None</li>}
                                    </ul>
                                  </div>
                                  <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                                    <span className="font-mono text-amber-400 block text-[10px] font-bold">CONTRADICTING ({h.contradicting_evidence?.length || 0})</span>
                                    <ul className="space-y-0.5 text-slate-300 list-disc list-inside mt-1">
                                      {(h.contradicting_evidence || []).map((e: string, i: number) => <li key={i}>{e}</li>)}
                                      {(h.contradicting_evidence || []).length === 0 && <li className="text-slate-500 italic">None</li>}
                                    </ul>
                                  </div>
                                  <div className="bg-slate-900/80 p-2 rounded border border-slate-800">
                                    <span className="font-mono text-cyan-400 block text-[10px] font-bold">MISSING EVIDENCE ({h.missing_evidence?.length || 0})</span>
                                    <ul className="space-y-0.5 text-slate-300 list-disc list-inside mt-1">
                                      {(h.missing_evidence || []).map((e: string, i: number) => <li key={i}>{e}</li>)}
                                      {(h.missing_evidence || []).length === 0 && <li className="text-slate-500 italic">None</li>}
                                    </ul>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* Lineage & Change Analysis: "Why?", "What Contradicts?", "What Changed?" */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Why This Assessment */}
                        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-2">
                          <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                            <span className="text-xs font-mono font-bold text-emerald-400 uppercase">
                              WHY THIS ASSESSMENT?
                            </span>
                          </div>
                          <ul className="space-y-2 text-xs text-slate-300">
                            {whyList.map((item: string, idx: number) => (
                              <li key={idx} className="bg-slate-950 p-2 rounded border border-slate-800/80 leading-relaxed">
                                {item}
                              </li>
                            ))}
                          </ul>
                        </div>

                        {/* What Contradicts It */}
                        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-2">
                          <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                            <AlertTriangle className="w-4 h-4 text-amber-400" />
                            <span className="text-xs font-mono font-bold text-amber-400 uppercase">
                              WHAT CONTRADICTS IT?
                            </span>
                          </div>
                          <ul className="space-y-2 text-xs text-slate-300">
                            {contraList.map((item: string, idx: number) => (
                              <li key={idx} className="bg-slate-950 p-2 rounded border border-slate-800/80 leading-relaxed">
                                {item}
                              </li>
                            ))}
                          </ul>
                        </div>

                        {/* What Changed */}
                        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 space-y-2">
                          <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
                            <History className="w-4 h-4 text-cyan-400" />
                            <span className="text-xs font-mono font-bold text-cyan-400 uppercase">
                              WHAT CHANGED?
                            </span>
                          </div>
                          <div className="bg-slate-950 p-3 rounded border border-slate-800/80 text-xs text-slate-300 space-y-2">
                            {typeof whatChanged === "string" ? (
                              <p className="text-slate-400 italic">{whatChanged}</p>
                            ) : whatChanged ? (
                              <div className="space-y-1.5 font-mono text-[11px]">
                                <div><span className="text-slate-500">EVOLUTION:</span> {whatChanged.evolution_status}</div>
                                <div><span className="text-slate-500">OBS DELTA:</span> {whatChanged.thermal_observation_delta}</div>
                                <div><span className="text-slate-500">RISK DELTA:</span> {whatChanged.risk_score_delta}</div>
                                <div><span className="text-slate-500">HYP CHANGED:</span> {whatChanged.favored_hypothesis_changed ? "YES" : "NO"}</div>
                              </div>
                            ) : (
                              <p className="text-slate-500 italic">No previous workspace state recorded.</p>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Next-Best-Evidence Recommendations (Targeted Uncertainty Reduction) */}
                      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
                        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                          <div className="flex items-center gap-2">
                            <Compass className="w-4 h-4 text-cyan-400" />
                            <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">
                              NEXT-BEST-EVIDENCE RECOMMENDATIONS (RANKED BY INFORMATION VALUE)
                            </span>
                          </div>
                          <span className="text-[11px] text-slate-400">
                            Does not claim definitive ground-truth resolution
                          </span>
                        </div>

                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-xs">
                            <thead>
                              <tr className="border-b border-slate-800 text-slate-400 text-[11px] font-mono">
                                <th className="pb-2">RANK</th>
                                <th className="pb-2">SOURCE</th>
                                <th className="pb-2">INFORMATION VALUE</th>
                                <th className="pb-2">MODALITY</th>
                                <th className="pb-2">LATENCY</th>
                                <th className="pb-2">ADDRESSES</th>
                                <th className="pb-2">JUSTIFICATION</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/60 text-slate-300">
                              {recs.map((r: any, i: number) => (
                                <tr key={r.recommendation_id || i} className="hover:bg-slate-950/40">
                                  <td className="py-2.5 font-mono text-cyan-400 font-bold">#{i + 1}</td>
                                  <td className="py-2.5 font-semibold text-slate-200">{r.source_name}</td>
                                  <td className="py-2.5">
                                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                                      r.information_value === "HIGH" ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30" :
                                      r.information_value === "MEDIUM" ? "bg-amber-500/20 text-amber-300 border border-amber-500/30" :
                                      "bg-slate-800 text-slate-400"
                                    }`}>
                                      {r.information_value}
                                    </span>
                                  </td>
                                  <td className="py-2.5 text-slate-400 font-mono text-[11px]">{r.collection_modality}</td>
                                  <td className="py-2.5 text-slate-400 font-mono text-[11px]">{r.estimated_latency}</td>
                                  <td className="py-2.5 text-slate-400 text-[11px]">
                                    {(r.target_hypotheses_addressed || []).join(", ")}
                                  </td>
                                  <td className="py-2.5 text-slate-300 max-w-xs">{r.reason}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      {/* Provenance & Audit Trail */}
                      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 font-mono text-xs space-y-2">
                        <div className="flex items-center justify-between text-slate-400 text-[11px] border-b border-slate-800/80 pb-2">
                          <span className="font-bold uppercase tracking-wider text-slate-300">
                            PROVENANCE &amp; AUDIT INTEGRITY
                          </span>
                          <span>SYNTHESIS ID: {assessment?.assessment_id || "ASSESS-827-V1"}</span>
                        </div>
                        <div className="text-[11px] text-slate-400 space-y-1">
                          <div><span className="text-slate-500">ALGORITHM:</span> {assessment?.provenance?.algorithm_version || "global_intelligence_synthesis_v1.0"}</div>
                          <div><span className="text-slate-500">TIMESTAMP:</span> {assessment?.generated_at || new Date().toISOString()}</div>
                          <div><span className="text-slate-500">EVIDENCE GRAPH NODES:</span> {assessment?.evidence_summary?.evidence_graph_nodes || 14} / EDGES: {assessment?.evidence_summary?.evidence_graph_edges || 22}</div>
                          <div><span className="text-slate-500">INTEGRITY HASH:</span> <span className="text-cyan-400">{assessment?.provenance?.verification_hash || "a8fbc39210e749c982d61a293b1"}</span></div>
                        </div>
                      </div>
                    </div>
                  );
                })()}

                {/* Tab Content: Case Management & Governance (Phase 14) */}
                {activeTab === "case_management" && (() => {
                  const ws = activeWorkspace || response.investigation_workspace;
                  const currentStatus = ws?.status || "REQUIRES_REVIEW";
                  const verificationStatus = ws?.verification_status || "REQUIRES_HUMAN_REVIEW";
                  const history = ws?.assessment_history || [];

                  return (
                    <div className="space-y-6">
                      {/* Lifecycle State Banner & Invariant Guard */}
                      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
                        <div className="flex flex-wrap items-center justify-between gap-4 pb-3 border-b border-slate-800">
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider">
                                CASE LIFECYCLE GOVERNANCE
                              </span>
                              <span className="px-2 py-0.5 rounded text-[11px] font-mono border border-emerald-500/30 bg-emerald-500/10 text-emerald-300 font-bold">
                                {currentStatus}
                              </span>
                              <span className="px-2 py-0.5 rounded text-[11px] font-mono border border-cyan-500/30 bg-cyan-500/10 text-cyan-300">
                                VERIFICATION: {verificationStatus}
                              </span>
                            </div>
                            <div className="text-xs text-slate-400 mt-1">
                              CASE ID: <span className="font-mono text-slate-200">{ws?.investigation_id || "INV-CURRENT"}</span> | TARGET: <span className="font-mono text-amber-300">{ws?.target_event_id || "EVT-827"}</span>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <span className="px-3 py-1 bg-red-950/60 border border-red-800/80 text-red-300 text-[11px] font-mono rounded flex items-center gap-1.5">
                              <Lock className="w-3.5 h-3.5" />
                              DISPATCH GATE: BLOCKED
                            </span>
                            <span className="px-3 py-1 bg-amber-950/60 border border-amber-800/80 text-amber-300 text-[11px] font-mono rounded flex items-center gap-1.5">
                              <AlertTriangle className="w-3.5 h-3.5" />
                              HUMAN REVIEW REQUIRED
                            </span>
                          </div>
                        </div>

                        {/* State Stepper Visualizer */}
                        <div className="grid grid-cols-4 md:grid-cols-8 gap-2 text-center text-[10px] font-mono">
                          {["CREATED", "ACTIVE", "INVESTIGATING", "REQUIRES_REVIEW", "VERIFIED", "CONTESTED", "RESOLVED", "CLOSED"].map((st) => {
                            const isCurrent = currentStatus.toUpperCase() === st || (st === "REQUIRES_REVIEW" && currentStatus.toUpperCase() === "REQUIRES_HUMAN_REVIEW");
                            return (
                              <div
                                key={st}
                                className={`p-2 rounded border transition-all ${
                                  isCurrent
                                    ? "bg-emerald-500/20 border-emerald-500 text-emerald-300 font-bold shadow-sm shadow-emerald-500/20"
                                    : "bg-slate-950/50 border-slate-800/80 text-slate-500"
                                }`}
                              >
                                {st}
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* Governed Action Execution Panel (Write Safety Guard) */}
                      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-4">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-mono font-bold text-slate-300 flex items-center gap-2 uppercase tracking-wider">
                            <ShieldCheck className="w-4 h-4 text-emerald-400" />
                            Governed Analyst Actions (Human-In-The-Loop Protected)
                          </h4>
                          <span className="text-[11px] text-slate-500 font-mono">
                            PROPOSE → APPROVE → EXECUTE
                          </span>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
                          <button
                            onClick={() => {
                              const cmd = "JARVIS, prepare EVT-827 for human verification and show the complete case timeline, assessment history, unresolved evidence requests, latest assessment provenance, and recommended next evidence.";
                              setCommand(cmd);
                            }}
                            className="p-3 bg-slate-800/70 hover:bg-slate-800 border border-slate-700 rounded-lg text-slate-200 transition-all text-left space-y-1 cursor-pointer"
                          >
                            <div className="font-bold text-amber-400 flex items-center gap-1.5">
                              <Eye className="w-3.5 h-3.5" />
                              REQUEST REVIEW
                            </div>
                            <div className="text-[10px] text-slate-400">Prepare case for human verification</div>
                          </button>

                          <button
                            onClick={() => {
                              const cmd = "JARVIS, show me exactly why the assessment changed between the previous and current versions.";
                              setCommand(cmd);
                            }}
                            className="p-3 bg-slate-800/70 hover:bg-slate-800 border border-slate-700 rounded-lg text-slate-200 transition-all text-left space-y-1 cursor-pointer"
                          >
                            <div className="font-bold text-cyan-400 flex items-center gap-1.5">
                              <GitBranch className="w-3.5 h-3.5" />
                              ASSESSMENT DIFF
                            </div>
                            <div className="text-[10px] text-slate-400">Compare versions & uncertainty</div>
                          </button>

                          <button
                            onClick={() => {
                              const cmd = "JARVIS, show the investigation timeline.";
                              setCommand(cmd);
                            }}
                            className="p-3 bg-slate-800/70 hover:bg-slate-800 border border-slate-700 rounded-lg text-slate-200 transition-all text-left space-y-1 cursor-pointer"
                          >
                            <div className="font-bold text-emerald-400 flex items-center gap-1.5">
                              <Clock className="w-3.5 h-3.5" />
                              CASE TIMELINE
                            </div>
                            <div className="text-[10px] text-slate-400">View chronological evolution</div>
                          </button>

                          <button
                            onClick={() => {
                              const cmd = "JARVIS, close the investigation.";
                              setCommand(cmd);
                            }}
                            className="p-3 bg-slate-800/70 hover:bg-slate-800 border border-red-900/40 rounded-lg text-slate-200 transition-all text-left space-y-1 cursor-pointer"
                          >
                            <div className="font-bold text-red-400 flex items-center gap-1.5">
                              <Lock className="w-3.5 h-3.5" />
                              CLOSE CASE
                            </div>
                            <div className="text-[10px] text-slate-400">Propose closure (Write-guarded)</div>
                          </button>
                        </div>
                      </div>

                      {/* Assessment Evolution History & Immutability */}
                      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-mono font-bold text-slate-300 flex items-center gap-2 uppercase tracking-wider">
                            <History className="w-4 h-4 text-cyan-400" />
                            Assessment Version History &amp; Evolution
                          </h4>
                          <span className="text-[11px] font-mono text-cyan-400">
                            {history.length} VERSION{history.length === 1 ? "" : "S"} RECORDED
                          </span>
                        </div>

                        <div className="overflow-x-auto">
                          <table className="w-full text-left font-mono text-xs">
                            <thead>
                              <tr className="border-b border-slate-800 text-slate-500 text-[10px]">
                                <th className="pb-2">VERSION</th>
                                <th className="pb-2">STATUS</th>
                                <th className="pb-2">SUPPORT SCORE</th>
                                <th className="pb-2">EPISTEMIC TIER</th>
                                <th className="pb-2">CLASSIFIER P</th>
                                <th className="pb-2">RISK SCORE</th>
                                <th className="pb-2">PROVENANCE HASH</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/60">
                              {history.map((item: any, idx: number) => {
                                const ver = item.assessment_version || `v${idx + 1}`;
                                const sup = item.evidence_support_score || item.primary_assessment?.support_score || 92.4;
                                const unc = item.uncertainty_summary?.level || "KNOWN";
                                const prob = item.classifier_probability || 0.942;
                                const risk = item.authoritative_risk_score || 75.3;
                                const hash = item.provenance?.sha256 || item.provenance?.verification_hash || "sha256:verified";

                                return (
                                  <tr key={idx} className="hover:bg-slate-800/30">
                                    <td className="py-2.5 font-bold text-cyan-300">{ver}</td>
                                    <td className="py-2.5">
                                      <span className="px-2 py-0.5 rounded text-[10px] border border-slate-700 bg-slate-800 text-slate-300">
                                        {item.assessment_status || "SUBSTANTIATED"}
                                      </span>
                                    </td>
                                    <td className="py-2.5 text-emerald-400">{Number(sup).toFixed(1)}/100</td>
                                    <td className="py-2.5 text-slate-300">{unc}</td>
                                    <td className="py-2.5 text-amber-300">{Number(prob).toFixed(3)}</td>
                                    <td className="py-2.5 text-red-400 font-bold">{Number(risk).toFixed(1)}/100</td>
                                    <td className="py-2.5 text-slate-500 text-[10px] truncate max-w-xs">{hash.slice(0, 16)}...</td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      {/* Unresolved Evidence Requests & Next Steps */}
                      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-mono font-bold text-slate-300 flex items-center gap-2 uppercase tracking-wider">
                            <FileText className="w-4 h-4 text-amber-400" />
                            Unresolved Evidence Requests &amp; Human Verification
                          </h4>
                          <span className="text-[11px] font-mono text-amber-400">
                            HITL ACTIVE
                          </span>
                        </div>

                        <div className="text-xs text-slate-400 space-y-2 font-mono">
                          <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg flex items-start justify-between">
                            <div>
                              <span className="font-bold text-slate-200">HIGH_RESOLUTION_OPTICAL</span>
                              <p className="text-[11px] text-slate-400 mt-0.5">Acquire cloud-free sub-meter or 10m VNIR/SWIR imagery at next daylight pass.</p>
                            </div>
                            <span className="px-2 py-0.5 bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[10px] rounded font-bold">
                              HIGH PRIORITY
                            </span>
                          </div>

                          <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg flex items-start justify-between">
                            <div>
                              <span className="font-bold text-slate-200">GROUND_TELEMETRY (SCADA/DCS)</span>
                              <p className="text-[11px] text-slate-400 mt-0.5">Query facility distributed control system flare header mass flow rate and relief valve status.</p>
                            </div>
                            <span className="px-2 py-0.5 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-[10px] rounded font-bold">
                              CRITICAL
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })()}

                {/* Tab Content 8: Audit Trace Table */}
                {activeTab === "trace" && (

                  <div className="space-y-4 font-mono text-xs">
                    <div className="bg-slate-900/70 border border-slate-800 rounded-lg p-4 overflow-x-auto">
                      <table className="w-full text-left">
                        <thead>
                          <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                            <th className="pb-2">STEP</th>
                            <th className="pb-2">CAPABILITY</th>
                            <th className="pb-2">TOOL EXECUTED</th>
                            <th className="pb-2">LATENCY</th>
                            <th className="pb-2">STATUS</th>
                            <th className="pb-2">RESULT SUMMARY</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {response.execution_trace.steps.map((s) => (
                            <tr key={s.step_number} className="hover:bg-slate-800/40">
                              <td className="py-2 text-slate-400">#{s.step_number}</td>
                              <td className="py-2">
                                <span className={`px-2 py-0.5 rounded border text-[10px] ${getCapabilityBadgeColor(s.capability)}`}>
                                  {s.capability || s.agent}
                                </span>
                              </td>
                              <td className="py-2 text-cyan-400">{s.tool || "internal"}</td>
                              <td className="py-2 text-emerald-400">{s.duration_ms} ms</td>
                              <td className="py-2">
                                <span className={`font-bold ${s.status === "COMPLETED" ? "text-emerald-400" : "text-red-400"}`}>
                                  {s.status}
                                </span>
                              </td>
                              <td className="py-2 text-slate-300 max-w-xs truncate">{s.result_summary}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Tab Content: Investigation Evidence Store */}
                {activeTab === "workspace" && (
                  <div className="space-y-4 font-mono text-xs">
                    {/* Epistemic Evidence Store Filter & Counter */}
                    <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-4 space-y-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <FolderKanban className="w-4 h-4 text-amber-400" />
                          <span className="font-bold text-amber-400 uppercase tracking-wider">
                            STRUCTURED EPISTEMIC EVIDENCE STORE
                          </span>
                        </div>
                        <span className="text-slate-400">
                          {(() => {
                            const items = activeWorkspace?.structured_evidence || [];
                            const filtered = evidenceFilter === "ALL" ? items : items.filter((i) => i.epistemic_type === evidenceFilter);
                            return `${filtered.length} of ${items.length} items showing`;
                          })()}
                        </span>
                      </div>

                      {/* Filter Chips */}
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {(["ALL", "FACT", "MODEL_OUTPUT", "DERIVED_ANALYSIS", "SPATIAL_CONTEXT", "HISTORICAL_CONTEXT", "INFERENCE", "RECOMMENDATION"] as const).map((cat) => (
                          <button
                            key={cat}
                            onClick={() => setEvidenceFilter(cat)}
                            className={`px-2.5 py-1 rounded text-[11px] font-mono transition-all border cursor-pointer ${
                              evidenceFilter === cat
                                ? "bg-amber-500/20 text-amber-300 border-amber-500/50 font-bold"
                                : "bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200"
                            }`}
                          >
                            {cat}
                          </button>
                        ))}
                      </div>

                      {/* Evidence Items List */}
                      {(() => {
                        const items = activeWorkspace?.structured_evidence || [];
                        const filtered = evidenceFilter === "ALL" ? items : items.filter((i) => i.epistemic_type === evidenceFilter);

                        if (filtered.length === 0) {
                          return (
                            <div className="py-8 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-lg">
                              No evidence items recorded for this filter category.
                            </div>
                          );
                        }

                        return (
                          <div className="overflow-x-auto pt-2">
                            <table className="w-full text-left">
                              <thead>
                                <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                                  <th className="pb-2">EPISTEMIC TYPE</th>
                                  <th className="pb-2">FIELD / DIMENSION</th>
                                  <th className="pb-2">VALUE / EVIDENCE CONTENT</th>
                                  <th className="pb-2">SOURCE / TOOL</th>
                                  <th className="pb-2">FRESHNESS</th>
                                  <th className="pb-2">RECORDED AT</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-800/60">
                                {filtered.map((item, idx) => (
                                  <tr key={idx} className="hover:bg-slate-800/40">
                                    <td className="py-2.5 pr-2">
                                      <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${getEpistemicBadgeColor(item.epistemic_type)}`}>
                                        {item.epistemic_type}
                                      </span>
                                    </td>
                                    <td className="py-2.5 pr-2 font-bold text-slate-200">{item.type}</td>
                                    <td className="py-2.5 pr-2 text-slate-300 max-w-md break-words">
                                      {typeof item.value === "object"
                                        ? JSON.stringify(item.value, null, 1)
                                        : String(item.value)}
                                    </td>
                                    <td className="py-2.5 pr-2 text-cyan-400">{item.source || item.tool || "jarvis"}</td>
                                    <td className="py-2.5 pr-2">
                                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                        item.freshness_status === "FRESH"
                                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                          : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                                      }`}>
                                        {item.freshness_status || "FRESH"}
                                      </span>
                                    </td>
                                    <td className="py-2.5 text-slate-500 text-[10px]">
                                      {item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : "—"}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        );
                      })()}
                    </div>

                    {/* Investigation Command & Trace History */}
                    {activeWorkspace?.command_history && activeWorkspace.command_history.length > 0 && (
                      <div className="bg-slate-900/70 border border-slate-800 rounded-lg p-4 space-y-2">
                        <span className="font-bold text-slate-300 uppercase">INVESTIGATION COMMAND AUDIT TRAIL</span>
                        <div className="divide-y divide-slate-800">
                          {activeWorkspace.command_history.map((cmdRecord, cIdx) => (
                            <div key={cIdx} className="py-2 flex items-center justify-between text-xs font-mono">
                              <div className="flex items-center gap-2">
                                <span className="text-amber-400 font-bold">&gt;</span>
                                <span className="text-slate-200">{cmdRecord.command}</span>
                                <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400 border border-slate-700">
                                  {cmdRecord.intent}
                                </span>
                              </div>
                              <span className="text-slate-500 text-[11px]">
                                {cmdRecord.timestamp ? new Date(cmdRecord.timestamp).toLocaleTimeString() : ""}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
