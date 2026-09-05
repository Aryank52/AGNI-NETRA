"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { formatNumber, formatFrp, formatCoord, safeArray } from "@/lib/formatters";
import { 
  Sliders, Activity, MapPin, AlertTriangle, 
  CheckCircle2, RefreshCw, BarChart2, Shield,
  ArrowUpRight, Compass, Layers, Filter, X,
  ExternalLink, Factory
} from "lucide-react";
import PageHeader from "@/components/common/PageHeader";
import EmptyState from "@/components/common/EmptyState";
import { CardSkeleton } from "@/components/common/Skeletons";

interface BaselineCell {
  grid_id: string;
  state: string;
  latitude_bin: number;
  longitude_bin: number;
  mean_frp: number;
  std_frp: number;
  max_frp: number;
  observation_count: number;
  current_active_frp: number;
  deviation_ratio: number;
  status: string;
}

function BaselinesContent() {
  const searchParams = useSearchParams();
  const initialState = searchParams.get("state") || "ALL";

  const [cells, setCells] = useState<BaselineCell[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedState, setSelectedState] = useState(initialState);

  const loadBaselines = async () => {
    setLoading(true);
    try {
      const data = await fetchApi<BaselineCell[]>("/baselines/grid-cells");
      setCells(data || []);
    } catch (err) {
      console.warn("Failed to load baseline grid cells:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBaselines();
  }, []);

  useEffect(() => {
    const s = searchParams.get("state");
    if (s) {
      setSelectedState(s);
    }
  }, [searchParams]);

  // Derived available states
  const availableStates = Array.from(new Set(cells.map((c) => c.state))).filter(Boolean).sort();

  const filteredCells = cells.filter((c) => {
    if (selectedState === "ALL") return true;
    return c.state.toLowerCase() === selectedState.toLowerCase();
  });

  return (
    <main className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-7xl mx-auto w-full">
      {/* Standardized Page Header */}
      <PageHeader
        category="90-DAY CELL BASELINE ENGINE"
        title="Thermal Baseline Grid & Deviation Tracker"
        description="Seasonal mean FRP baselines across 0.1° × 0.1° industrial grid cells. Compares live satellite passes against normal background to isolate industrial plant breaches."
        icon={<Sliders className="w-6 h-6 text-emerald-400" />}
        actions={
          <button
            onClick={loadBaselines}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
            title="Refresh Baselines"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-emerald-400" : ""}`} />
          </button>
        }
      />

      {/* Key Baseline Metrics Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-agni-card border border-agni-border">
          <div className="text-[10px] text-slate-500 uppercase font-mono">Monitored Clusters</div>
          <div className="text-2xl font-extrabold text-white mt-1 font-mono">{cells.length} Industrial Belts</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Continuous 90-day tracking</div>
        </div>

        <div className="p-4 rounded-2xl bg-agni-card border border-agni-border">
          <div className="text-[10px] text-slate-500 uppercase font-mono">National Average Baseline</div>
          <div className="text-2xl font-extrabold text-emerald-400 mt-1 font-mono">107.0 MW</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Mean background emissions</div>
        </div>

        <div className="p-4 rounded-2xl bg-agni-card border border-agni-border">
          <div className="text-[10px] text-slate-500 uppercase font-mono">Spike Threshold</div>
          <div className="text-2xl font-extrabold text-amber-400 mt-1 font-mono">&gt; 2.0x Mean</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Triggers anomaly alert</div>
        </div>

        <div className="p-4 rounded-2xl bg-agni-card border border-agni-border">
          <div className="text-[10px] text-slate-500 uppercase font-mono">Spatial Cell Grid</div>
          <div className="text-2xl font-extrabold text-cyan-400 mt-1 font-mono">0.1° × 0.1°</div>
          <div className="text-[11px] text-slate-400 mt-0.5">~11km × 11km resolution</div>
        </div>
      </div>

      {/* State Filter Pills & Active Filter Bar */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-1.5">
            <button
              onClick={() => setSelectedState("ALL")}
              className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition-all ${
                selectedState === "ALL"
                  ? "bg-emerald-500 text-slate-950 shadow-md"
                  : "bg-slate-900/60 hover:bg-slate-800 text-slate-400 border border-slate-800"
              }`}
            >
              All States ({cells.length})
            </button>
            {availableStates.map((st) => (
              <button
                key={st}
                onClick={() => setSelectedState(st)}
                className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition-all ${
                  selectedState.toLowerCase() === st.toLowerCase()
                    ? "bg-emerald-500 text-slate-950 shadow-md"
                    : "bg-slate-900/60 hover:bg-slate-800 text-slate-400 border border-slate-800"
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          <div className="text-xs text-slate-400 font-mono">
            Showing {filteredCells.length} of {cells.length} cells
          </div>
        </div>

        {selectedState !== "ALL" && (
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-slate-500">Active Filter:</span>
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
              State: {selectedState}
              <button
                onClick={() => setSelectedState("ALL")}
                className="hover:text-white"
                title="Clear State Filter"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
            <button
              onClick={() => setSelectedState("ALL")}
              className="text-slate-400 hover:text-white underline text-[11px] ml-1"
            >
              Clear All
            </button>
          </div>
        )}
      </div>

      {/* Grid Cells Cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : filteredCells.length === 0 ? (
        <EmptyState
          title="No Baseline Cells Available"
          description={selectedState !== "ALL" ? `No grid cells found in ${selectedState}.` : "No grid cells match your active filter."}
          actionLabel="Reset to All States"
          onAction={() => setSelectedState("ALL")}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {filteredCells.map((cell) => {
            const isSpike = cell.status === "CRITICAL_SPIKE";
            const isElevated = cell.status === "ELEVATED";

            return (
              <div
                key={cell.grid_id}
                className={`p-5 rounded-2xl bg-agni-card border transition-all flex flex-col justify-between space-y-3 ${
                  isSpike
                    ? "border-red-500/50 shadow-lg shadow-red-500/10"
                    : isElevated
                    ? "border-amber-500/40"
                    : "border-agni-border"
                }`}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <span className="font-mono text-xs font-bold text-white">{cell.grid_id}</span>
                    <span className={`text-[9px] uppercase font-mono px-2 py-0.5 rounded font-bold ${
                      isSpike
                        ? "bg-red-500/20 text-red-300 border border-red-500/30 animate-pulse"
                        : isElevated
                        ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                        : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    }`}>
                      {cell.status}
                    </span>
                  </div>

                  <div>
                    <div className="text-xs font-bold text-slate-200">{cell.state} Industrial Belt</div>
                    <div className="text-[11px] text-slate-400 font-mono">
                      {formatCoord(cell.latitude_bin, cell.longitude_bin, 3)}
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2 text-xs font-mono">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Historical Mean:</span>
                      <span className="text-white font-bold">{formatFrp(cell.mean_frp)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Std Deviation:</span>
                      <span className="text-slate-300">±{formatNumber(cell.std_frp, 1)} MW</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Current Observed:</span>
                      <span className={`font-bold ${isSpike ? "text-red-400" : isElevated ? "text-amber-400" : "text-emerald-400"}`}>
                        {formatFrp(cell.current_active_frp)}
                      </span>
                    </div>
                    <div className="flex justify-between pt-1 border-t border-slate-800">
                      <span className="text-slate-400 font-bold">Deviation Ratio:</span>
                      <span className={`font-bold ${isSpike ? "text-red-400" : "text-slate-200"}`}>
                        {formatNumber(cell.deviation_ratio, 2, "1.00")}x
                      </span>
                    </div>
                  </div>

                  <div className="text-[10px] text-slate-500 flex justify-between">
                    <span>{cell.observation_count} Historical Passes</span>
                    <span>Max: {formatFrp(cell.max_frp)}</span>
                  </div>
                </div>

                {/* Cross-Navigation Actions */}
                <div className="pt-2 border-t border-slate-800 flex items-center justify-between gap-1 text-[11px] font-mono">
                  <Link
                    href={`/dashboard?lat=${cell.latitude_bin}&lon=${cell.longitude_bin}&zoom=11`}
                    className="px-2 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 flex items-center gap-1 transition-colors"
                    title="Focus on Map"
                  >
                    <MapPin className="w-3 h-3 text-amber-400" />
                    <span>Map</span>
                  </Link>

                  <Link
                    href={`/dashboard/events?state=${encodeURIComponent(cell.state)}`}
                    className="px-2 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 flex items-center gap-1 transition-colors"
                    title="View Events in this State"
                  >
                    <Activity className="w-3 h-3 text-cyan-400" />
                    <span>Events</span>
                  </Link>

                  <Link
                    href={`/dashboard/atlas?state=${encodeURIComponent(cell.state)}`}
                    className="px-2 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 flex items-center gap-1 transition-colors"
                    title="Open Industrial Atlas for State"
                  >
                    <Factory className="w-3 h-3 text-emerald-400" />
                    <span>Atlas</span>
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </main>
  );
}

export default function BaselinesPage() {
  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <Suspense fallback={<div className="flex-1 p-6 text-slate-400 font-mono text-xs">Loading baseline intelligence...</div>}>
          <BaselinesContent />
        </Suspense>
      </div>
    </div>
  );
}
