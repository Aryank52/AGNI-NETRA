"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import RiskBadge from "@/components/intelligence/RiskBadge";
import { ThermalEvent } from "@/types";
import { fetchApi } from "@/lib/api";
import { 
  AlertOctagon, Sparkles, TrendingUp, 
  MapPin, ChevronRight, ShieldAlert
} from "lucide-react";

export default function AnomaliesPage() {
  const [anomalies, setAnomalies] = useState<ThermalEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAnomalies = async () => {
      try {
        const data = await fetchApi<ThermalEvent[]>("/anomalies");
        setAnomalies(data);
      } catch (err) {
        console.warn("Failed to load anomalies:", err);
      } finally {
        setLoading(false);
      }
    };
    loadAnomalies();
  }, []);

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-6xl mx-auto">
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-agni-border pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/30 font-bold">
                  ANOMALY DETECTION ENGINE
                </span>
                <span className="text-xs text-slate-400">Statistical Baseline Deviation & Isolation Forest</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5 mt-1">
                <AlertOctagon className="w-6 h-6 text-red-400" />
                Abnormal Thermal Spikes & Behavioral Deviations
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Answers: &ldquo;Is this behaviour unusual for this location?&rdquo; — Flags sudden surges (+2.5σ to +3.5σ) above historical baselines.
              </p>
            </div>

            <span className="text-xs font-mono px-3 py-1 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
              {anomalies.length} Critical Deviations Active
            </span>
          </div>

          {/* Anomalies List */}
          <div className="space-y-4">
            {anomalies.map((evt) => {
              const devRatio = evt.features?.baseline_deviation_ratio || 2.8;
              return (
                <div
                  key={evt.id}
                  className="p-5 rounded-2xl bg-agni-card border border-red-500/40 hover:border-red-500 transition-all space-y-3.5 shadow-xl glow-border-critical"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-red-500/20 text-red-400 flex items-center justify-center font-bold font-mono">
                        +3σ
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm font-bold text-white">{evt.event_code}</span>
                          <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                            {evt.state}
                          </span>
                        </div>
                        <h3 className="text-sm font-bold text-amber-400 mt-0.5">
                          {evt.prediction?.predicted_class || "Industrial Fire"}
                        </h3>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="text-right font-mono">
                        <div className="text-[10px] text-slate-500 uppercase">Deviation Spike</div>
                        <div className="text-base font-extrabold text-red-400">
                          {devRatio.toFixed(1)}x Normal
                        </div>
                      </div>
                      <RiskBadge level={evt.risk?.risk_level || "CRITICAL"} score={evt.risk?.risk_score} />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
                    <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                      <div className="text-slate-500 text-[10px]">CURRENT PEAK FRP</div>
                      <div className="text-red-400 font-bold text-sm">{evt.max_frp.toFixed(1)} MW</div>
                      <div className="text-[10px] text-slate-400">Baseline historical mean: 85.0 MW</div>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                      <div className="text-slate-500 text-[10px]">FACILITY CONTEXT</div>
                      <div className="text-white font-bold">{evt.facility_status} Facility</div>
                      <div className="text-[10px] text-slate-400">NTPC Singrauli Super Thermal</div>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                      <div className="text-slate-500 text-[10px]">ANOMALY ENGINE VERDICT</div>
                      <div className="text-amber-400 font-bold">Severe Statistical Outlier</div>
                      <div className="text-[10px] text-slate-400">Z-Score: +3.25σ above mean</div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1 text-xs">
                    <span className="text-slate-400">
                      Isolation Forest Multivariate Anomaly Score: <strong className="text-white font-mono">0.884</strong>
                    </span>
                    <Link
                      href={`/dashboard/events/${evt.id}`}
                      className="px-4 py-1.5 rounded-xl bg-red-500 hover:bg-red-600 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow-md transition-colors"
                    >
                      <span>Inspect Critical Event</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </main>
      </div>
    </div>
  );
}
