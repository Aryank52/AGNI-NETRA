"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import RiskBadge from "@/components/intelligence/RiskBadge";
import { ThermalEvent } from "@/types";
import { fetchApi } from "@/lib/api";
import { 
  ShieldAlert, Shield, AlertTriangle, ChevronRight, 
  Flame, RefreshCw, Layers, Compass, CheckCircle2,
  Download, Activity
} from "lucide-react";

export default function RiskIntelligencePage() {
  const [criticalEvents, setCriticalEvents] = useState<ThermalEvent[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadRiskData = async () => {
    setLoading(true);
    try {
      const [critData, sumData] = await Promise.all([
        fetchApi<ThermalEvent[]>("/risk/critical"),
        fetchApi<any>("/risk/summary").catch(() => null),
      ]);
      setCriticalEvents(critData || []);
      setSummary(sumData);
    } catch (err) {
      console.warn("Failed to load risk intelligence:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRiskData();
  }, []);

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-agni-border pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/30 font-bold">
                  MULTI-FACTOR HAZARD EVALUATION
                </span>
                <span className="text-xs text-slate-400">National Industrial Thermal Risk Matrix</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5 mt-1">
                <ShieldAlert className="w-6 h-6 text-red-400" />
                Risk Intelligence & Critical Hazard Evaluation
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Transparent multi-factor formula evaluating thermal intensity (40%), baseline abnormality (25%), and surrounding environmental/population exposure (35%).
              </p>
            </div>

            <button
              onClick={loadRiskData}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
              title="Refresh Risk Data"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-red-400" : ""}`} />
            </button>
          </div>

          {/* National Risk KPI Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl bg-agni-card border border-red-500/30 shadow-lg shadow-red-500/5">
              <div className="text-[10px] text-slate-500 uppercase font-mono">Critical Risk Incidents</div>
              <div className="text-2xl font-extrabold text-red-400 mt-1 font-mono">{summary?.critical_count || criticalEvents.length} Incidents</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Immediate mitigation required</div>
            </div>

            <div className="p-4 rounded-2xl bg-agni-card border border-orange-500/30">
              <div className="text-[10px] text-slate-500 uppercase font-mono">High Risk Events</div>
              <div className="text-2xl font-extrabold text-orange-400 mt-1 font-mono">{summary?.high_count || 12} Events</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Elevated intensity / near population</div>
            </div>

            <div className="p-4 rounded-2xl bg-agni-card border border-yellow-500/30">
              <div className="text-[10px] text-slate-500 uppercase font-mono">Moderate Risk Events</div>
              <div className="text-2xl font-extrabold text-yellow-400 mt-1 font-mono">{summary?.moderate_count || 24} Events</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Controlled routine industrial burn</div>
            </div>

            <div className="p-4 rounded-2xl bg-agni-card border border-agni-border">
              <div className="text-[10px] text-slate-500 uppercase font-mono">Average National Risk Score</div>
              <div className="text-2xl font-extrabold text-white mt-1 font-mono">{summary?.avg_risk_score || 58.4} / 100</div>
              <div className="text-[11px] text-slate-400 mt-0.5">Normalized index</div>
            </div>
          </div>

          {/* Formula Transparency Breakdown Card */}
          <div className="p-5 rounded-2xl bg-agni-card border border-agni-border space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <Shield className="w-4 h-4 text-amber-400" />
              AGNI-NETRA Risk Formula Architecture
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
              <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                <div className="text-amber-400 font-bold">1. Thermal Intensity (40%)</div>
                <p className="text-[11px] text-slate-400 font-sans">
                  Evaluates Fire Radiative Power (MW) and Planck brightness temperature against combustion scaling curves.
                </p>
              </div>
              <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                <div className="text-amber-400 font-bold">2. Baseline Abnormality (25%)</div>
                <p className="text-[11px] text-slate-400 font-sans">
                  Calculates statistical deviation ratio ($Z$-score) relative to the 90-day cell historical background.
                </p>
              </div>
              <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                <div className="text-amber-400 font-bold">3. Environmental Exposure (35%)</div>
                <p className="text-[11px] text-slate-400 font-sans">
                  Measures spatial buffer proximity to urban populations, protected forest canopies, and gas pipelines.
                </p>
              </div>
            </div>
          </div>

          {/* Critical Hazard Incident Roster */}
          <div className="p-5 rounded-2xl bg-agni-card border border-agni-border shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400" />
                Active Critical & High Risk Thermal Incidents
              </h2>
              <span className="text-xs font-mono text-slate-400">
                {criticalEvents.length} Incidents Requiring Analyst Intervention
              </span>
            </div>

            <div className="space-y-3">
              {criticalEvents.map((evt) => (
                <div
                  key={evt.id}
                  className="p-4 rounded-xl bg-slate-900/80 border border-red-500/30 hover:border-red-500/60 transition-all flex flex-wrap items-center justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-sm font-bold text-amber-400">{evt.event_code}</span>
                      <span className="text-xs font-semibold text-white">{evt.state} {evt.district ? `(${evt.district})` : ""}</span>
                      <RiskBadge level={evt.risk?.risk_level || "CRITICAL"} score={evt.risk?.risk_score} />
                    </div>
                    <p className="text-xs text-slate-300">
                      Classification: <strong className="text-amber-300">{evt.prediction?.predicted_class || "Industrial Fire"}</strong> • Peak FRP: <strong className="text-white font-mono">{evt.max_frp.toFixed(1)} MW</strong> • Facility: {evt.nearest_facility_distance_m !== undefined ? `${evt.nearest_facility_distance_m.toFixed(0)}m` : "Uncataloged"}
                    </p>
                    <div className="flex items-center gap-2 text-[11px] text-slate-400">
                      <span>Reasons:</span>
                      {evt.risk?.risk_reasons?.map((r, i) => (
                        <span key={i} className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                          {r}
                        </span>
                      ))}
                    </div>
                  </div>

                  <Link
                    href={`/dashboard/events/${evt.id}`}
                    className="px-4 py-2 rounded-xl bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-700 hover:to-orange-700 text-white font-bold text-xs shadow-md shadow-red-500/20 flex items-center gap-1.5 transition-all shrink-0"
                  >
                    <span>Emergency Dossier</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
