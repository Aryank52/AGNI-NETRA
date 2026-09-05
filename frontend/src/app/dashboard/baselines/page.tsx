"use client";

import React, { useState, useEffect } from "react";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { formatNumber, formatFrp, formatCoord, safeArray } from "@/lib/formatters";
import { 
  Sliders, Activity, MapPin, AlertTriangle, 
  CheckCircle2, RefreshCw, BarChart2, Shield,
  ArrowUpRight, Compass, Layers
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

export default function BaselinesPage() {
  const [cells, setCells] = useState<BaselineCell[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedState, setSelectedState] = useState("ALL");

  const loadBaselines = async () => {
    setLoading(true);
    try {
      const data = await fetchApi<BaselineCell[]>("/baselines/grid-cells");
      setCells(data);
    } catch (err) {
      console.warn("Failed to load baseline grid cells:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBaselines();
  }, []);

  const filteredCells = cells.filter((c) => {
    if (selectedState === "ALL") return true;
    return c.state.toLowerCase() === selectedState.toLowerCase();
  });

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-7xl mx-auto">
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
              description="No grid cells match your active filter."
              actionLabel="Refresh Baselines"
              onAction={loadBaselines}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {filteredCells.map((cell) => {
              const isSpike = cell.status === "CRITICAL_SPIKE";
              const isElevated = cell.status === "ELEVATED";

              return (
                <div
                  key={cell.grid_id}
                  className={`p-5 rounded-2xl bg-agni-card border transition-all space-y-3 ${
                    isSpike
                      ? "border-red-500/50 shadow-lg shadow-red-500/10"
                      : isElevated
                      ? "border-amber-500/40"
                      : "border-agni-border"
                  }`}
                >
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
              );
            })}
          </div>
          )}
        </main>
      </div>
    </div>
  );
}
