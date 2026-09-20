"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { 
  ShieldAlert, Flame, Activity, CheckCircle2, 
  Search, RefreshCw, AlertTriangle, ChevronRight, Layers,
  Zap, Info, Clock, MapPin
} from "lucide-react";

interface PreventionCaseSummary {
  id: string;
  case_number: string;
  event_id: string;
  event_code: string;
  title: string;
  prevention_priority: "CRITICAL" | "HIGH" | "MODERATE" | "LOW";
  status: string;
  state: string;
  district: string;
  latitude: number;
  longitude: number;
  recurrence_score: number;
  persistence_score: number;
  baseline_deviation_ratio: number;
  evidence_strength_score: number;
  dominant_hypothesis?: string;
  recommendations_count?: number;
  created_at: string;
}

function PreventionDashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialEventId = searchParams.get("eventId") || "";

  const [cases, setCases] = useState<PreventionCaseSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedPriority, setSelectedPriority] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Trigger modal state
  const [showTriggerModal, setShowTriggerModal] = useState<boolean>(!!initialEventId);
  const [targetEventCode, setTargetEventCode] = useState<string>(initialEventId || "EVT-GUJ-20260916-150D");
  const [lookbackYears, setLookbackYears] = useState<number>(3);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  const loadCases = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchApi<any>("/prevention/cases");
      const caseList = Array.isArray(data)
        ? data
        : Array.isArray(data?.items)
        ? data.items
        : Array.isArray(data?.cases)
        ? data.cases
        : [];
      setCases(caseList);
    } catch (err: any) {
      console.error("Failed to load prevention cases:", err);
      setError(err?.message || "Failed to load prevention intelligence cases.");
      setCases([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, []);

  const handleTriggerAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetEventCode.trim()) return;

    setAnalyzing(true);
    setAnalyzeError(null);

    try {
      const res = await fetchApi<any>("/prevention/analyze", {
        method: "POST",
        body: JSON.stringify({
          event_code: targetEventCode.trim(),
          lookback_years: lookbackYears
        })
      });

      if (res && res.id) {
        setShowTriggerModal(false);
        router.push(`/dashboard/prevention/${res.id}`);
      } else {
        await loadCases();
        setShowTriggerModal(false);
      }
    } catch (err: any) {
      console.error("Analysis execution failed:", err);
      setAnalyzeError(err?.message || "Analysis generation failed. Verify event code.");
    } finally {
      setAnalyzing(false);
    }
  };

  // Safe cases array fallback
  const safeCases = Array.isArray(cases) ? cases : [];

  // Filtered cases
  const filteredCases = safeCases.filter((c) => {
    if (selectedPriority !== "ALL" && c.prevention_priority !== selectedPriority) return false;
    if (selectedStatus !== "ALL" && c.status !== selectedStatus) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchNum = c.case_number?.toLowerCase().includes(q);
      const matchCode = c.event_code?.toLowerCase().includes(q);
      const matchTitle = c.title?.toLowerCase().includes(q);
      const matchLoc = `${c.district} ${c.state}`.toLowerCase().includes(q);
      if (!matchNum && !matchCode && !matchTitle && !matchLoc) return false;
    }
    return true;
  });

  // KPI calculations
  const totalCases = safeCases.length;
  const criticalCases = safeCases.filter(c => c.prevention_priority === "CRITICAL").length;
  const avgRecurrence = safeCases.length > 0 
    ? (safeCases.reduce((acc, c) => acc + (c.recurrence_score || 0), 0) / safeCases.length).toFixed(1)
    : "0.0";
  const avgEvidence = safeCases.length > 0
    ? Math.round((safeCases.reduce((acc, c) => acc + (c.evidence_strength_score || 0), 0) / safeCases.length) * 100)
    : 0;

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header />

        <main className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
          {/* Breadcrumb & Title */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-1">
                <span>AGNI-NETRA</span>
                <span>/</span>
                <span>INTELLIGENCE</span>
                <span>/</span>
                <span className="text-amber-400 font-semibold">PREVENTION & ROOT-CAUSE</span>
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
                <ShieldAlert className="w-6 h-6 text-rose-500" />
                Proactive Fire Prevention & Root-Cause Intelligence
              </h1>
              <p className="text-xs text-slate-400 mt-1 max-w-3xl">
                Longitudinal multi-source thermal recurrence analysis, deterministic root-cause hypothesis generation, 
                and verified regulatory prevention recommendations. Powered by Master JARVIS Orchestration.
              </p>
            </div>

            <div className="flex items-center gap-2.5">
              <button
                onClick={() => loadCases()}
                className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
                title="Refresh Cases"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-amber-400' : ''}`} />
              </button>
              <button
                onClick={() => setShowTriggerModal(true)}
                className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-lg shadow-rose-600/20 transition-all cursor-pointer"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>Investigate Root-Cause</span>
              </button>
            </div>
          </div>

          {/* Epistemic Anti-Fabrication Notice */}
          <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
            <Info className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-200/90 leading-relaxed space-y-1">
              <p className="font-bold tracking-wide text-amber-300">
                EPISTEMIC SAFETY INVARIANT: HISTORICAL CORRELATION DOES NOT IMPLY CAUSATION.
              </p>
              <p className="text-[11px] text-amber-200/80">
                Root-cause hypotheses and prevention vectors are transparently computed from verified NASA FIRMS VIIRS telemetry, 
                PostGIS industrial footprints, and historical spatial baselines. Recommendations state they <em>&ldquo;MAY REDUCE RECURRENCE RISK&rdquo;</em>. 
                External delivery strictly requires authenticated human analyst approval.
              </p>
            </div>
          </div>

          {/* KPI Cards Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-semibold uppercase tracking-wider">Active Prevention Cases</span>
                <Layers className="w-4 h-4 text-slate-400" />
              </div>
              <div className="text-2xl font-bold font-mono text-white">{totalCases}</div>
              <div className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
                <span>Longitudinal Hotspot Registry</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-rose-400">
                <span className="text-xs font-semibold uppercase tracking-wider">Critical Priority</span>
                <Flame className="w-4 h-4 text-rose-500" />
              </div>
              <div className="text-2xl font-bold font-mono text-rose-400">{criticalCases}</div>
              <div className="text-[11px] text-rose-400/80 flex items-center gap-1 font-mono">
                <span>Recurrence &ge; 3.0 episodes/yr</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-amber-400">
                <span className="text-xs font-semibold uppercase tracking-wider">Avg Recurrence Rate</span>
                <Activity className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold font-mono text-amber-300">{avgRecurrence} <span className="text-xs text-slate-400 font-sans">episodes/yr</span></div>
              <div className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
                <span>Multi-Year Temporal Drift</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-emerald-400">
                <span className="text-xs font-semibold uppercase tracking-wider">Avg Evidence Strength</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold font-mono text-emerald-400">{avgEvidence}%</div>
              <div className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
                <span>Observable Ground Telemetry</span>
              </div>
            </div>
          </div>

          {/* Filters & Search Bar */}
          <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by Case # (PREV-...), Event Code (EVT-...), District, State..."
                className="w-full pl-9 pr-4 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-amber-500 font-mono"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {/* Priority Filter */}
              <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 rounded-lg p-1 text-[11px]">
                {["ALL", "CRITICAL", "HIGH", "MODERATE", "LOW"].map((p) => (
                  <button
                    key={p}
                    onClick={() => setSelectedPriority(p)}
                    className={`px-2 py-0.5 rounded font-semibold transition-colors ${
                      selectedPriority === p
                        ? p === "CRITICAL" ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                          : p === "HIGH" ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                          : "bg-slate-800 text-white"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>

              {/* Status Filter */}
              <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 rounded-lg p-1 text-[11px]">
                {["ALL", "OPEN", "UNDER_INVESTIGATION", "RESOLVED"].map((s) => (
                  <button
                    key={s}
                    onClick={() => setSelectedStatus(s)}
                    className={`px-2 py-0.5 rounded font-semibold transition-colors ${
                      selectedStatus === s
                        ? "bg-slate-800 text-white"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {s.replace("_", " ")}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Cases List */}
          {loading ? (
            <div className="space-y-3 p-6 text-center text-slate-400">
              <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              <p className="text-xs font-mono">Loading proactive prevention cases...</p>
            </div>
          ) : error ? (
            <div className="p-6 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          ) : filteredCases.length === 0 ? (
            <div className="p-12 rounded-xl bg-slate-900/40 border border-slate-800 text-center space-y-4">
              <ShieldAlert className="w-12 h-12 text-slate-600 mx-auto stroke-1" />
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-slate-300">No Prevention Cases Found</h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto">
                  No cases match the current filter. Launch Master JARVIS Root-Cause Synthesis on any thermal event to generate a proactive prevention dossier.
                </p>
              </div>
              <button
                onClick={() => setShowTriggerModal(true)}
                className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-lg shadow-rose-600/20 transition-all cursor-pointer"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>Investigate Root-Cause</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredCases.map((c) => (
                <Link
                  key={c.id}
                  href={`/dashboard/prevention/${c.id}`}
                  className="group block p-4 rounded-xl bg-slate-900/80 hover:bg-slate-900 border border-slate-800 hover:border-amber-500/50 transition-all duration-200 shadow-sm hover:shadow-lg hover:shadow-amber-500/5"
                >
                  <div className="space-y-3">
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono font-bold text-amber-400 group-hover:text-amber-300">
                            {c.case_number}
                          </span>
                          <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase border ${
                            c.prevention_priority === "CRITICAL"
                              ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                              : c.prevention_priority === "HIGH"
                              ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                              : "bg-slate-800 text-slate-300 border-slate-700"
                          }`}>
                            {c.prevention_priority} PRIORITY
                          </span>
                        </div>
                        <p className="text-xs font-medium text-slate-300 mt-1 line-clamp-1">
                          {c.title}
                        </p>
                      </div>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-400 border border-slate-700/60 shrink-0">
                        {c.status}
                      </span>
                    </div>

                    {/* Geography & Target Event */}
                    <div className="flex items-center justify-between text-xs text-slate-400 pt-1 border-t border-slate-800/60">
                      <div className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        <span>{c.district}, {c.state}</span>
                      </div>
                      <div className="font-mono text-[11px] text-slate-400">
                        Event: <span className="text-slate-300">{c.event_code}</span>
                      </div>
                    </div>

                    {/* Recurrence & Anomaly Indicators */}
                    <div className="grid grid-cols-2 gap-2 p-2 rounded-lg bg-slate-950/70 border border-slate-800/80 text-[11px] font-mono">
                      <div>
                        <span className="text-slate-400 text-[10px] block">Recurrence Rate</span>
                        <span className="font-bold text-amber-400">{c.recurrence_score?.toFixed(1)} / yr</span>
                      </div>
                      <div>
                        <span className="text-slate-400 text-[10px] block">Baseline Deviation</span>
                        <span className="font-bold text-rose-400">{c.baseline_deviation_ratio?.toFixed(1)}x Normal</span>
                      </div>
                    </div>

                    {/* Evidence Strength Meter */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-[10px] text-slate-400">
                        <span>Evidence Strength</span>
                        <span className="font-mono text-slate-300">{Math.round((c.evidence_strength_score || 0) * 100)}%</span>
                      </div>
                      <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            (c.evidence_strength_score || 0) >= 0.7
                              ? "bg-emerald-500"
                              : (c.evidence_strength_score || 0) >= 0.4
                              ? "bg-amber-500"
                              : "bg-rose-500"
                          }`}
                          style={{ width: `${Math.round((c.evidence_strength_score || 0) * 100)}%` }}
                        />
                      </div>
                    </div>

                    {/* Footer */}
                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/60">
                      <span className="flex items-center gap-1 text-[10px]">
                        <Clock className="w-3 h-3 text-slate-400" />
                        {new Date(c.created_at).toLocaleDateString()}
                      </span>
                      <span className="text-amber-400 group-hover:translate-x-1 transition-transform flex items-center gap-1 font-semibold text-xs">
                        Open Workspace <ChevronRight className="w-3.5 h-3.5" />
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </main>
      </div>

      {/* Trigger Root-Cause Analysis Modal */}
      {showTriggerModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-rose-500" />
                <h2 className="text-base font-bold text-white">Investigate Root-Cause & Prevention</h2>
              </div>
              <button
                onClick={() => setShowTriggerModal(false)}
                className="text-slate-400 hover:text-slate-200 text-sm font-mono"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Launch Master JARVIS Root-Cause Synthesis on any active or historical thermal event. 
              Correlates multi-year FIRMS telemetry, industrial footprint baselines, 13 hypothesis categories, 
              and verified regulatory jurisdiction authorities.
            </p>

            <form onSubmit={handleTriggerAnalysis} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-mono font-semibold text-slate-300">
                  Target Event Code or UUID
                </label>
                <input
                  type="text"
                  required
                  value={targetEventCode}
                  onChange={(e) => setTargetEventCode(e.target.value)}
                  placeholder="e.g. EVT-GUJ-20260916-150D"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-white placeholder-slate-400 focus:outline-none focus:border-amber-500"
                />
                <span className="text-[10px] text-slate-400">
                  Tested Target: <code className="text-amber-400">EVT-GUJ-20260916-150D</code> (Reliance Jamnagar)
                </span>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-300 font-semibold">Historical Lookback Window</span>
                  <span className="text-amber-400 font-bold">{lookbackYears} Years</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="5"
                  step="1"
                  value={lookbackYears}
                  onChange={(e) => setLookbackYears(parseInt(e.target.value, 10))}
                  className="w-full accent-amber-500 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                  <span>1 Year</span>
                  <span>3 Years (Default)</span>
                  <span>5 Years (Max)</span>
                </div>
              </div>

              {analyzeError && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
                  {analyzeError}
                </div>
              )}

              <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowTriggerModal(false)}
                  disabled={analyzing}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={analyzing}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-rose-600/20 transition-all cursor-pointer"
                >
                  {analyzing ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Synthesizing Hypotheses...</span>
                    </>
                  ) : (
                    <>
                      <Zap className="w-3.5 h-3.5" />
                      <span>Run Prevention Synthesis</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function PreventionPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <PreventionDashboardContent />
    </Suspense>
  );
}
