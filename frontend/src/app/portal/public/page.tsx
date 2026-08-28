"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { 
  Eye, AlertTriangle, ShieldCheck, Wind, 
  MapPin, Clock, ExternalLink, RefreshCw,
  Flame, HeartHandshake, CheckCircle2
} from "lucide-react";

export default function PublicPortalPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const loadPublicData = async () => {
    setLoading(true);
    try {
      const res = await fetchApi<any>("/portals/public/advisories");
      setData(res);
    } catch (err) {
      console.warn("Failed to load public portal data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPublicData();
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
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold">
                  TRANSPARENT CITIZEN ADVISORY
                </span>
                <span className="text-xs text-slate-400">National Public Health & Thermal Safety Feed</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5 mt-1">
                <Eye className="w-6 h-6 text-emerald-400" />
                Public Thermal Awareness & Transparency Portal
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Real-time citizen-facing alerts for industrial fire events, major gas flare operations, and crop burning. Provides downwind smoke advisories and precautionary health guidelines.
              </p>
            </div>

            <button
              onClick={loadPublicData}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
              title="Refresh Public Advisories"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-emerald-400" : ""}`} />
            </button>
          </div>

          {/* National Air & Thermal Status Banner */}
          <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-agni-card to-slate-900 border border-agni-border shadow-xl grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-1">
              <div className="text-[10px] text-slate-500 font-mono uppercase">National Fire Status</div>
              <div className="text-xl font-extrabold text-emerald-400 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5" />
                <span>{data?.national_status || "MONITORING ACTIVE"}</span>
              </div>
              <p className="text-xs text-slate-400">Continuous 15-minute NASA satellite refresh</p>
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data?.public_advisories?.map((adv: any) => (
                <div
                  key={adv.id}
                  className="p-5 rounded-2xl bg-agni-card border border-agni-border hover:border-emerald-500/40 transition-all space-y-3 shadow-lg"
                >
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <span className="text-xs font-bold text-amber-300 font-sans">{adv.title}</span>
                    <span className="text-[9px] uppercase font-mono px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/30 font-bold">
                      {adv.severity}
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
                    <span className="text-white font-bold">{adv.frp_mw.toFixed(1)} MW</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
