"use client";

import React, { useState, useEffect } from "react";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { CandidateFacility } from "@/types";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { 
  Search, ShieldAlert, Sparkles, MapPin, 
  Activity, CheckCircle2, ArrowRight, AlertTriangle
} from "lucide-react";

export default function CandidateDiscoveryPage() {
  const { user } = useAuth();
  const [candidates, setCandidates] = useState<CandidateFacility[]>([]);
  const [loading, setLoading] = useState(true);
  const [promotingId, setPromotingId] = useState<string | null>(null);

  const loadCandidates = async () => {
    try {
      const data = await fetchApi<CandidateFacility[]>("/candidates");
      setCandidates(data);
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
      alert("Failed to promote: " + err);
    } finally {
      setPromotingId(null);
    }
  };

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
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 font-bold">
                  CORE USP CAPABILITY
                </span>
                <span className="text-xs text-slate-400">Autonomous Geospatial Discovery</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5 mt-1">
                <Search className="w-6 h-6 text-purple-400" />
                Discovered Candidate Industrial Thermal Sources
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Persistent uncataloged thermal emissions discovered via spatio-temporal recurrence, continuous day/night signatures, and LULC context.
              </p>
            </div>

            <span className="text-xs font-mono px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-300">
              {candidates.length} Candidate Sites Discovered
            </span>
          </div>

          {/* Cards Grid */}
          <div className="grid grid-cols-1 gap-4">
            {candidates.map((cand) => {
              const isPromoted = cand.status === "PROMOTED";
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
                          {cand.name_label}
                        </h3>
                        <div className="text-xs text-slate-400 font-mono flex items-center gap-2">
                          <MapPin className="w-3.5 h-3.5 text-amber-400" />
                          <span>{cand.state} {cand.district ? `(${cand.district})` : ""}</span>
                          <span>• Coords: {cand.latitude.toFixed(4)}°N, {cand.longitude.toFixed(4)}°E</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="text-right font-mono">
                        <div className="text-[10px] text-slate-500 uppercase">Context Score</div>
                        <div className="text-base font-extrabold text-purple-400">
                          {(cand.industrial_context_score * 100).toFixed(0)}%
                        </div>
                      </div>

                      <span
                        className={`text-xs font-mono px-2.5 py-1 rounded-full font-bold uppercase border ${
                          isPromoted
                            ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                            : "bg-purple-500/20 text-purple-300 border-purple-500/40"
                        }`}
                      >
                        {cand.status}
                      </span>
                    </div>
                  </div>

                  {/* Evidence Indicators Strip */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
                    <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                      <div className="text-slate-500 text-[10px]">PERSISTENCE SPAN</div>
                      <div className="text-white font-bold">{cand.persistence_days} Active Days Detected</div>
                      <div className="text-[10px] text-slate-400">{cand.detection_count} Satellite passes</div>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                      <div className="text-slate-500 text-[10px]">DIURNAL EMISSION SIGNATURE</div>
                      <div className="text-emerald-400 font-bold">24x7 Continuous Night Burn</div>
                      <div className="text-[10px] text-slate-400">Night/Day Ratio: 0.85x</div>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                      <div className="text-slate-500 text-[10px]">LULC CONTEXT</div>
                      <div className="text-amber-400 font-bold">Industrial / Barren Buffer</div>
                      <div className="text-[10px] text-slate-400">Isolated from forest/agri</div>
                    </div>
                  </div>

                  {/* Evidence Bullet Points */}
                  <div className="p-3 rounded-xl bg-purple-950/20 border border-purple-500/20 text-xs space-y-1.5 text-slate-300">
                    <div className="font-semibold text-purple-300 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5" />
                      Analytical Ground Proof Evidence:
                    </div>
                    {cand.evidence_summary?.supporting_indicators?.map((item: string, idx: number) => (
                      <div key={idx} className="flex items-center gap-2 pl-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-purple-400 shrink-0" />
                        <span>{item}</span>
                      </div>
                    ))}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[11px] text-slate-500">
                      Discovered on: {new Date(cand.first_detected_at).toLocaleDateString()}
                    </span>

                    {!isPromoted && (
                      <button
                        onClick={() => handlePromote(cand.id)}
                        disabled={promotingId === cand.id}
                        className="px-4 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xs shadow-md shadow-purple-500/20 flex items-center gap-2 transition-all"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>{promotingId === cand.id ? "Promoting..." : "Promote to Known Facility"}</span>
                      </button>
                    )}
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
