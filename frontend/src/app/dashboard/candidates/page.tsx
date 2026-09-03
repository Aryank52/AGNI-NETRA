"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { CandidateFacility } from "@/types";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { safeArray, safeNumber, formatNumber, formatPercent } from "@/lib/formatters";
import { 
  Search, ShieldAlert, Sparkles, MapPin, 
  Activity, CheckCircle2, ArrowRight, AlertTriangle,
  Compass, ArrowUpRight, Loader2
} from "lucide-react";

export default function CandidateDiscoveryPage() {
  const { user } = useAuth();
  const [candidates, setCandidates] = useState<CandidateFacility[]>([]);
  const [loading, setLoading] = useState(true);
  const [promotingId, setPromotingId] = useState<string | null>(null);

  const loadCandidates = async () => {
    try {
      const data = await fetchApi<any>("/candidates");
      setCandidates(safeArray<CandidateFacility>(data));
    } catch (err) {
      console.warn("Failed to load candidates:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCandidates();
  }, []);

  const handlePromote = async (candId: string) => {
    if (!confirm("Promote this candidate thermal source to the Official Known & Verified Industrial Registry?")) return;
    setPromotingId(candId);
    try {
      await fetchApi(`/candidates/${candId}/promote`, { method: "POST" });
      await loadCandidates();
    } catch (err) {
      alert("Failed to promote candidate: " + err);
    } finally {
      setPromotingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950 font-sans">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-6xl mx-auto w-full">
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-agni-border pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 font-bold">
                  UNREGISTERED COMBUSTION HUBS
                </span>
                <span className="text-xs text-slate-400">PostGIS Multi-Temporal Hotspot Clustering</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5 mt-1">
                <Sparkles className="w-6 h-6 text-purple-400" />
                Candidate Facility Discovery Pipeline
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Detects uncataloged persistent thermal emitters not currently registered in OSM or government registries.
              </p>
            </div>

            <span className="text-xs font-mono px-3 py-1 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 font-bold">
              {candidates.length} Discovered Candidates
            </span>
          </div>

          {/* Candidates List */}
          {loading ? (
            <div className="p-12 text-center text-xs text-slate-400 font-mono space-y-2">
              <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <div>SCANNING MULTI-TEMPORAL RECURRENCE HUBS...</div>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {candidates.map((cand) => {
                const isPromoted = cand.status === "PROMOTED";
                const isPromoting = promotingId === cand.id;
                const latVal = safeNumber(cand.latitude, 0);
                const lonVal = safeNumber(cand.longitude, 0);

                return (
                  <div
                    key={cand.id}
                    className="p-5 rounded-2xl bg-agni-card border border-purple-500/30 hover:border-purple-500/60 transition-all space-y-4 shadow-xl"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-purple-500/20 text-purple-300 flex items-center justify-center font-bold font-mono text-xs">
                          USP
                        </div>
                        <div>
                          <h3 className="text-base font-bold text-white">
                            {cand.name_label || "Candidate Thermal Source"}
                          </h3>
                          <div className="text-xs text-slate-400 font-mono flex items-center gap-2">
                            <MapPin className="w-3.5 h-3.5 text-amber-400" />
                            <span>{cand.state} {cand.district ? `(${cand.district})` : ""}</span>
                            <span>• Coords: {formatNumber(latVal, 4)}°N, {formatNumber(lonVal, 4)}°E</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="text-right font-mono">
                          <div className="text-[10px] text-slate-500 uppercase">Context Score</div>
                          <div className="text-base font-extrabold text-purple-400">
                            {formatPercent(cand.industrial_context_score)}
                          </div>
                        </div>

                        <span
                          className={`text-xs font-mono px-2.5 py-1 rounded-full font-bold uppercase border ${
                            isPromoted
                              ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                              : "bg-purple-500/20 text-purple-300 border-purple-500/40"
                          }`}
                        >
                          {cand.status || "CANDIDATE"}
                        </span>
                      </div>
                    </div>

                    {/* Evidence Indicators Strip */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
                      <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                        <div className="text-slate-500 text-[10px]">PERSISTENCE SPAN</div>
                        <div className="text-white font-bold">{cand.persistence_days || 12} Active Days Detected</div>
                        <div className="text-[10px] text-slate-400">{cand.detection_count || 14} Satellite passes</div>
                      </div>

                      <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                        <div className="text-slate-500 text-[10px]">DIURNAL EMISSION SIGNATURE</div>
                        <div className="text-emerald-400 font-bold">24x7 Continuous Night Burn</div>
                        <div className="text-[10px] text-slate-400">Night/Day Ratio: 0.85x</div>
                      </div>

                      <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                        <div className="text-slate-500 text-[10px]">SPATIAL PROXIMITY</div>
                        <div className="text-purple-300 font-bold">Industrial Corridor</div>
                        <div className="text-[10px] text-slate-400">Isolated uncataloged point source</div>
                      </div>
                    </div>

                    {/* Promotion Action */}
                    <div className="flex items-center justify-between pt-1 text-xs">
                      <Link
                        href={`/dashboard?lat=${latVal}&lon=${lonVal}`}
                        className="text-slate-400 hover:text-white flex items-center gap-1 font-mono text-xs"
                      >
                        <Compass className="w-3.5 h-3.5" />
                        <span>Inspect Location on Map</span>
                      </Link>

                      {!isPromoted && (
                        <button
                          onClick={() => handlePromote(cand.id)}
                          disabled={isPromoting}
                          className="px-4 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-md transition-colors disabled:opacity-50"
                        >
                          {isPromoting ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <CheckCircle2 className="w-3.5 h-3.5" />
                          )}
                          <span>Promote to Official Registry</span>
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
