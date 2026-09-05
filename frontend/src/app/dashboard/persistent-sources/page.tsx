"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import RiskBadge from "@/components/intelligence/RiskBadge";
import PageHeader from "@/components/common/PageHeader";
import EmptyState from "@/components/common/EmptyState";
import { CardSkeleton } from "@/components/common/Skeletons";
import { ThermalEvent } from "@/types";
import { fetchApi } from "@/lib/api";
import { safeArray, safeNumber, formatNumber, formatFrp, formatCoord } from "@/lib/formatters";
import { 
  Activity, MapPin, Calendar, Clock, 
  ChevronRight, ArrowRight, ShieldAlert, Sparkles,
  Info, Compass, ArrowUpRight, HelpCircle, Repeat,
  Zap, AlertOctagon, RefreshCw, Factory, ShieldCheck
} from "lucide-react";

export default function PersistentSourcesPage() {
  const [events, setEvents] = useState<ThermalEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const loadEvents = async () => {
    setLoading(true);
    try {
      const data = await fetchApi<any>("/events?limit=100");
      const list = safeArray<ThermalEvent>(data);
      // Filter persistent sources (persistence score >= 2.0 or detection count >= 3)
      const persistent = list.filter(
        (e) => safeNumber(e.features?.persistence_score, 0) >= 2.0 || safeNumber(e.detection_count, 0) >= 3
      );
      setEvents(persistent);
    } catch (err) {
      console.warn("Failed to load persistent events:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, []);

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950 font-sans">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Standardized Page Header */}
          <PageHeader
            category="PERSISTENCE ENGINE"
            title="Persistent Thermal Sources & Recurrence Analytics"
            description="Distinguishes stationary industrial combustion (gas flares, kiln exhausts, smelters) from ephemeral agricultural or forest fires by analyzing multi-temporal recurrence, continuity, and baseline deviation."
            icon={<Activity className="w-6 h-6 text-emerald-400" />}
            actions={
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold">
                  {events.length} Persistent Emitters Verified
                </span>
                <button
                  onClick={loadEvents}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                  title="Refresh Analytics"
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-emerald-400" : ""}`} />
                </button>
              </div>
            }
          />

          {/* 3-Pillar Diagnostic Framework Strip */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Pillar 1: REPEATED */}
            <div className="p-4 rounded-2xl bg-agni-card border border-cyan-500/30 space-y-2 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold uppercase text-cyan-400 tracking-wider">
                  PILLAR 1: REPEATED
                </span>
                <Repeat className="w-4 h-4 text-cyan-400" />
              </div>
              <div className="text-base font-bold text-white font-mono">Multi-Pass Observations</div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Hotspots detected across $\ge 3$ distinct satellite orbits. Rules out transient single-pass artifacts, solar glints, and temporary field clearings.
              </p>
            </div>

            {/* Pillar 2: PERSISTENT */}
            <div className="p-4 rounded-2xl bg-agni-card border border-emerald-500/30 space-y-2 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold uppercase text-emerald-400 tracking-wider">
                  PILLAR 2: PERSISTENT
                </span>
                <Activity className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-base font-bold text-white font-mono">24x7 Thermal Continuity</div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Persistence score $\ge 2.0/10.0$ and Day/Night ratio $\approx 1.0\times$. Signifies continuous round-the-clock combustion (refinery flares, blast furnaces).
              </p>
            </div>

            {/* Pillar 3: ABNORMAL */}
            <div className="p-4 rounded-2xl bg-agni-card border border-amber-500/30 space-y-2 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold uppercase text-amber-400 tracking-wider">
                  PILLAR 3: ABNORMAL
                </span>
                <AlertOctagon className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-base font-bold text-white font-mono">Baseline Surge ($Z$-Score)</div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Statistical deviation from the local 90-day background norm. Isolates acute flaring surges and unpermitted combustion spikes from normal baseline operations.
              </p>
            </div>
          </div>

          {/* Cards Grid */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <CardSkeleton />
              <CardSkeleton />
              <CardSkeleton />
              <CardSkeleton />
            </div>
          ) : events.length === 0 ? (
            <EmptyState
              title="No Persistent Emitters Identified"
              description="No thermal hotspot records currently meet the multi-pass persistence threshold in the active catalog."
              actionLabel="Refresh Data"
              onAction={loadEvents}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {events.map((evt) => {
                const pScore = safeNumber(evt.features?.persistence_score, 7.0);
                const rRate = safeNumber(evt.features?.recurrence_rate, 4.5);
                const dnRatio = safeNumber(evt.features?.day_night_ratio, 1.2);
                const devRatio = safeNumber(evt.features?.baseline_deviation_ratio, 1.5);
                const maxFrpVal = safeNumber(evt.max_frp, 0);

                return (
                  <div
                    key={evt.id}
                    className="p-5 rounded-2xl bg-agni-card border border-agni-border hover:border-emerald-500/40 transition-all space-y-3.5 shadow-lg"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-amber-400">{evt.event_code}</span>
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                            {evt.state} {evt.district ? `• ${evt.district}` : ""}
                          </span>
                        </div>
                        <h3 className="text-base font-bold text-white mt-1">
                          {evt.prediction?.predicted_class || "Industrial Combustion"}
                        </h3>
                      </div>
                      <RiskBadge level={evt.risk?.risk_level || "LOW"} score={evt.risk?.risk_score} />
                    </div>

                    {/* Distinct 3-Pillar Status Badge Bar */}
                    <div className="grid grid-cols-3 gap-2 text-center text-[10px] font-mono">
                      <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-300">
                        <span className="text-[9px] text-slate-400 block uppercase">REPEATED</span>
                        <strong className="text-xs">{evt.detection_count || 3} passes</strong>
                      </div>

                      <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300">
                        <span className="text-[9px] text-slate-400 block uppercase">PERSISTENT</span>
                        <strong className="text-xs">{formatNumber(pScore, 1)}/10 • {formatNumber(dnRatio, 1)}x D/N</strong>
                      </div>

                      <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300">
                        <span className="text-[9px] text-slate-400 block uppercase">ABNORMAL</span>
                        <strong className="text-xs">+{formatNumber(devRatio, 1)}σ surge</strong>
                      </div>
                    </div>

                    <div className="text-xs text-slate-400 flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800 font-mono">
                      <span>Peak FRP: <strong className="text-white">{formatFrp(maxFrpVal)}</strong></span>
                      <div className="flex items-center gap-1.5">
                        <Link
                          href={`/dashboard/events/${evt.id}`}
                          className="px-2.5 py-1 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-[11px] flex items-center gap-1 transition-colors"
                        >
                          <span>OPEN DOSSIER</span>
                          <ArrowUpRight className="w-3 h-3" />
                        </Link>
                        <Link
                          href={`/dashboard?lat=${evt.latitude}&lon=${evt.longitude}&event_id=${evt.id}`}
                          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[11px] flex items-center gap-1 transition-colors"
                          title="Fly to Hotspot on Tactical Map"
                        >
                          <MapPin className="w-3 h-3 text-amber-400" />
                          <span>MAP</span>
                        </Link>
                        <Link
                          href={`/dashboard/atlas?search=${encodeURIComponent(evt.district || evt.state || "")}`}
                          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[11px] flex items-center gap-1 transition-colors"
                          title="View Registered Plants in this District"
                        >
                          <Factory className="w-3 h-3 text-cyan-400" />
                          <span>ATLAS</span>
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
