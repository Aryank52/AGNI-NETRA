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
  HelpCircle, RotateCcw, FileDown, Tag, Compass, Award, FileCode, Globe
} from "lucide-react";

export default function JarvisCommandConsolePage() {
  const { user } = useAuth();
  const [command, setCommand] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<JarvisResponse | null>(null);
  const [activeWorkspace, setActiveWorkspace] = useState<InvestigationWorkspace | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<string | null>(null);
  const [evidenceFilter, setEvidenceFilter] = useState<EpistemicType | "ALL">("ALL");
  const [sessionId, setSessionId] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"overview" | "workspace" | "geospatial" | "ml_shap" | "anomaly" | "risk" | "satellite" | "trace">("overview");
  const [toolsCatalog, setToolsCatalog] = useState<JarvisToolInfo[]>([]);
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Suggested high-value commands as specified in product taxonomy
  const suggestedCommands = [
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
    "what thermal coverage is available for this region?"
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
                  <div className="space-y-4">
                    <div className="bg-slate-900/70 border border-slate-800 rounded-lg p-4 font-mono text-xs space-y-3">
                      <span className="font-bold text-amber-400 uppercase">LONGITUDINAL BASELINE ANALYSIS</span>
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

                {/* Tab Content 7: Audit Trace Table */}
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
