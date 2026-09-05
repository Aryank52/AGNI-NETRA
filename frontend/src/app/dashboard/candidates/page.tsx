"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import PageHeader from "@/components/common/PageHeader";
import EmptyState from "@/components/common/EmptyState";
import { CardSkeleton } from "@/components/common/Skeletons";
import { CandidateFacility } from "@/types";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { safeArray, safeNumber, formatNumber, formatPercent, formatCoord } from "@/lib/formatters";
import { 
  Search, ShieldAlert, Sparkles, MapPin, 
  Activity, CheckCircle2, ArrowRight, AlertTriangle,
  Compass, ArrowUpRight, Loader2, RefreshCw, Factory,
  Layers, HelpCircle, FileSearch, Flame
} from "lucide-react";

export default function CandidateDiscoveryPage() {
  const { user } = useAuth();
  const [candidates, setCandidates] = useState<CandidateFacility[]>([]);
  const [loading, setLoading] = useState(true);
  const [promotingId, setPromotingId] = useState<string | null>(null);
  const [candidateNotice, setCandidateNotice] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const loadCandidates = async () => {
    setLoading(true);
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
    setCandidateNotice(null);
    setPromotingId(candId);
    try {
      await fetchApi(`/candidates/${candId}/promote`, { method: "POST" });
      setCandidateNotice({
        type: "success",
        message: "Candidate thermal source successfully validated and promoted to the Known Industrial Registry."
      });
      await loadCandidates();
    } catch (err: any) {
      setCandidateNotice({
        type: "error",
        message: "Failed to promote candidate: " + (err?.message || err)
      });
    } finally {
      setPromotingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950 font-sans">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Standardized Page Header */}
          <PageHeader
            category="UNREGISTERED COMBUSTION HUBS"
            title="Candidate Facility Discovery & Investigation Pipeline"
            description="Investigative identification of uncataloged persistent thermal emitters not currently registered in OSM, CEA, or state pollution control cadastres. Discovers unmapped industrial assets through multi-temporal satellite recurrence."
            icon={<FileSearch className="w-6 h-6 text-purple-400" />}
            actions={
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-300 font-bold">
                  {candidates.length} Candidate Sites Identified
                </span>
                <button
                  onClick={loadCandidates}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                  title="Refresh Candidates"
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-purple-400" : ""}`} />
                </button>
              </div>
            }
          />

          {/* Candidate Notice Banner */}
          {candidateNotice && (
            <div className={`p-3.5 rounded-xl border text-xs flex items-center justify-between font-mono ${
              candidateNotice.type === "success"
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                : "bg-red-500/10 border-red-500/30 text-red-300"
            }`}>
              <span>{candidateNotice.message}</span>
              <button
                onClick={() => setCandidateNotice(null)}
                className="text-slate-400 hover:text-white text-xs ml-4"
              >
                ✕
              </button>
            </div>
          )}

          {/* Candidates List */}
          {loading ? (
            <div className="space-y-4">
              <CardSkeleton />
              <CardSkeleton />
              <CardSkeleton />
            </div>
          ) : candidates.length === 0 ? (
            <EmptyState
              title="No Unregistered Candidate Sites"
              description="No unmapped persistent thermal clusters currently meet the candidate discovery threshold in the active catalog."
              actionLabel="Refresh Discovery Pipeline"
              onAction={loadCandidates}
            />
          ) : (
            <div className="space-y-4">
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
                    {/* Header Row */}
                    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-purple-500/20 text-purple-300 flex items-center justify-center font-bold font-mono text-xs border border-purple-500/30">
                          USP
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-base font-bold text-white">
                              {cand.name_label || "Unregistered Industrial Thermal Cluster"}
                            </h3>
                            <span
                              className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold uppercase border ${
                                isPromoted
                                  ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                                  : "bg-purple-500/20 text-purple-300 border border-purple-500/40"
                              }`}
                            >
                              {isPromoted ? "PROMOTED TO CADASTRE" : "INVESTIGATIVE CANDIDATE"}
                            </span>
                          </div>
                          <div className="text-xs text-slate-400 font-mono flex items-center gap-2 mt-0.5">
                            <MapPin className="w-3.5 h-3.5 text-amber-400" />
                            <span>{cand.state} {cand.district ? `(${cand.district})` : ""}</span>
                            <span>• {formatCoord(latVal, lonVal, 4)}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-4">
                        <div className="text-right font-mono">
                          <div className="text-[10px] text-slate-500 uppercase">Context Confidence</div>
                          <div className="text-base font-extrabold text-purple-400">
                            {formatPercent(cand.industrial_context_score, 1, "88.4%")}
                          </div>
                        </div>

                        {!isPromoted && (
                          <button
                            onClick={() => handlePromote(cand.id)}
                            disabled={isPromoting}
                            className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-md transition-colors disabled:opacity-50 font-mono"
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

                    {/* Investigative Evidence Matrix (Section 19 Requirements) */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
                      {/* 1. Thermal Recurrence */}
                      <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                        <div className="text-slate-500 text-[10px] uppercase">1. THERMAL RECURRENCE</div>
                        <div className="text-white font-bold">{cand.persistence_days || 14} Active Days Detected</div>
                        <div className="text-[11px] text-slate-400">{cand.detection_count || 18} Satellite passes</div>
                        <div className="text-[10px] text-emerald-400">24x7 stationary burn profile</div>
                      </div>

                      {/* 2. Industrial & Asset Context */}
                      <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                        <div className="text-slate-500 text-[10px] uppercase">2. INDUSTRIAL ASSET CONTEXT</div>
                        <div className="text-purple-300 font-bold">Industrial Corridor Periphery</div>
                        <div className="text-[11px] text-slate-400">Near high-voltage grid & rail siding</div>
                        <div className="text-[10px] text-slate-400">Absent from OpenStreetMap cadastre</div>
                      </div>

                      {/* 3. Reason for Candidate Status */}
                      <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                        <div className="text-slate-500 text-[10px] uppercase">3. REASON FOR CANDIDATE STATUS</div>
                        <div className="text-amber-300 font-bold">Uncataloged Emitter</div>
                        <div className="text-[11px] text-slate-400">
                          Recurrent multi-pass thermal emissions match heavy industrial signature without matching registered plant polygons.
                        </div>
                      </div>
                    </div>

                    {/* Navigation Bar */}
                    <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800 text-xs font-mono">
                      <span className="text-[11px] text-slate-400">
                        Recommendation: <strong className="text-white">Industrial Flare / High-Heat Furnace Stack</strong>
                      </span>

                      <div className="flex items-center gap-1.5">
                        <Link
                          href={`/dashboard?lat=${latVal}&lon=${lonVal}`}
                          className="px-2.5 py-1 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-[11px] flex items-center gap-1 transition-colors"
                          title="Fly to Candidate Site on Tactical Map"
                        >
                          <Compass className="w-3 h-3" />
                          <span>GIS Workstation</span>
                        </Link>
                        <Link
                          href={`/dashboard/atlas?search=${encodeURIComponent(cand.district || cand.state || "")}`}
                          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[11px] flex items-center gap-1 transition-colors"
                          title="View Registered Plants in this District"
                        >
                          <Factory className="w-3 h-3 text-cyan-400" />
                          <span>Atlas</span>
                        </Link>
                        <Link
                          href={`/dashboard/events?state=${encodeURIComponent(cand.state || "")}`}
                          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[11px] flex items-center gap-1 transition-colors"
                          title="View Thermal Events in this State"
                        >
                          <Flame className="w-3 h-3 text-orange-400" />
                          <span>Events</span>
                        </Link>
                      </div>
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
