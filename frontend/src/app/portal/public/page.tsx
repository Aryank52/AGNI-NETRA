"use client";

import React, { useState, useEffect } from "react";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { safeArray, safeNumber, formatFrp } from "@/lib/formatters";
import { 
  ShieldCheck, AlertTriangle, Wind, 
  MapPin, CheckCircle2, Info, Eye, Shield, Lock
} from "lucide-react";

export default function PublicPortalPage() {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApi<any>("/portals/public/overview")
      .then((res) => setData(res))
      .catch((err) => console.warn("Failed to load public portal:", err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950 font-sans">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-5xl mx-auto w-full">
          {/* Header */}
          <div className="border-b border-agni-border pb-4 space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold">
                PUBLIC SAFETY INFORMATION
              </span>
              <span className="text-xs text-slate-400">Citizen Awareness & Regional Advisories</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-white flex items-center gap-2.5">
              <ShieldCheck className="w-6 h-6 text-emerald-400" />
              National Thermal Safety & Public Advisory Portal
            </h1>
            <p className="text-xs text-slate-400">
              Aggregated thermal activity summaries and regional precautionary alerts derived from satellite earth observations.
            </p>
          </div>

          {/* Strict Role Isolation & Public Disclaimer */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-start gap-3 text-xs text-slate-300">
            <Shield className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <div className="font-bold text-amber-300 text-xs uppercase flex items-center gap-2">
                <span>Public Portal Safety Notice</span>
                <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  Secured Boundary
                </span>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                This public dashboard provides high-level district advisories. For statutory security and privacy, internal industrial facility layouts, exact proprietary coordinates, ML SHAP attribution internals, and analyst audit trails are restricted to authorized regulatory personnel.
              </p>
            </div>
          </div>

          {/* Regional Summary Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-5 rounded-2xl bg-agni-card border border-agni-border">
            <div className="space-y-1">
              <div className="text-[10px] text-slate-500 font-mono uppercase">Monitored Regions</div>
              <div className="text-xl font-extrabold text-white font-mono">
                36 States & UTs
              </div>
              <p className="text-xs text-slate-400">Continuous 15-min satellite observation</p>
            </div>

            <div className="space-y-1">
              <div className="text-[10px] text-slate-500 font-mono uppercase">Active Public Hazards</div>
              <div className="text-xl font-extrabold text-amber-400 font-mono">
                {data?.total_active_hazards || 0} Monitored Zones
              </div>
              <p className="text-xs text-slate-400">Exceeding 80 MW threshold</p>
            </div>

            <div className="space-y-1">
              <div className="text-[10px] text-slate-500 font-mono uppercase">Precautionary Guidance</div>
              <div className="text-xl font-extrabold text-white">CPCB Level 2</div>
              <p className="text-xs text-slate-400">Wear N95 masks near downwind zones</p>
            </div>
          </div>

          {/* Public Advisories List */}
          <div className="space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <Wind className="w-4 h-4 text-cyan-400" />
              Active Regional Thermal Advisories
            </h2>

            {loading ? (
              <div className="p-8 text-center text-xs text-slate-400 font-mono space-y-2">
                <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto" />
                <div>LOADING PUBLIC SAFETY ADVISORIES...</div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {safeArray(data?.public_advisories).map((adv: any, idx: number) => (
                  <div
                    key={adv.id || idx}
                    className="p-5 rounded-2xl bg-agni-card border border-agni-border hover:border-emerald-500/40 transition-all space-y-3 shadow-lg"
                  >
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                      <span className="text-xs font-bold text-amber-300 font-sans">{adv.title}</span>
                      <span className="text-[9px] uppercase font-mono px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/30 font-bold">
                        {adv.severity || "MODERATE"}
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">
                      {adv.advisory_text}
                    </p>

                    <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-[11px] text-slate-400 font-mono">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-slate-500" />
                        {adv.location}
                      </span>
                      <span className="text-white font-bold">{formatFrp(adv.frp_mw)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
