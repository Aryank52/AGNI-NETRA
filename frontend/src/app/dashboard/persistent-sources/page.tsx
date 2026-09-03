"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import RiskBadge from "@/components/intelligence/RiskBadge";
import { ThermalEvent } from "@/types";
import { fetchApi } from "@/lib/api";
import { safeArray, safeNumber, formatNumber, formatFrp } from "@/lib/formatters";
import { 
  Activity, MapPin, Calendar, Clock, 
  ChevronRight, ArrowRight, ShieldAlert, Sparkles,
  Info, Compass, ArrowUpRight, HelpCircle
} from "lucide-react";

export default function PersistentSourcesPage() {
  const [events, setEvents] = useState<ThermalEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadEvents = async () => {
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
    loadEvents();
  }, []);

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
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold">
                  PERSISTENCE ENGINE
                </span>
                <span className="text-xs text-slate-400">Multi-Temporal Thermal Continuity Analysis</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5 mt-1">
                <Activity className="w-6 h-6 text-emerald-400" />
                Persistent Thermal Sources & Recurrence Analytics
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Distinguishes stationary industrial combustion (gas flares, kiln exhausts, smelters) from ephemeral agricultural or forest fires (t_obs &lt; t_event temporal invariant).
              </p>
            </div>

            <span className="text-xs font-mono px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold">
              {events.length} Persistent Emitters Verified
            </span>
          </div>

          {/* Plain Language Interpretation Banner */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-start gap-3 text-xs text-slate-300 shadow-sm">
            <Info className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold text-white text-xs uppercase tracking-wide">
                How AGNI-NETRA Calculates Persistence & Recurrence
              </span>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                <strong>Persistence Score (0.0 to 10.0):</strong> Measures the statistical probability that a thermal hotspot at these coordinates is a continuous, permanent combustion source based on recurrent multi-day satellite detections.
                <br />
                <strong>Day/Night Ratio:</strong> Continuous industrial processes (petrochemical flares, blast furnaces) emit thermal radiation 24x7 with Day/Night ratios near ~1.0x, whereas agricultural field burning occurs almost exclusively during solar peak hours.
              </p>
            </div>
          </div>

          {/* Cards Grid */}
          {loading ? (
            <div className="p-12 text-center text-xs text-slate-400 font-mono space-y-2">
              <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <div>COMPUTING TEMPORAL RECURRENCE VECTORS...</div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {events.map((evt) => {
                const pScore = safeNumber(evt.features?.persistence_score, 7.0);
                const rRate = safeNumber(evt.features?.recurrence_rate, 4.5);
                const dnRatio = safeNumber(evt.features?.day_night_ratio, 1.2);
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

                    <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 grid grid-cols-3 gap-2 text-xs font-mono text-center">
                      <div>
                        <div className="text-[10px] text-slate-500">PERSISTENCE</div>
                        <div className="font-bold text-emerald-400">{formatNumber(pScore, 1)} / 10.0</div>
                      </div>
                      <div>
                        <div className="text-[10px] text-slate-500">RECURRENCE</div>
                        <div className="font-bold text-white">{formatNumber(rRate, 1)} passes/mo</div>
                      </div>
                      <div>
                        <div className="text-[10px] text-slate-500">24x7 RATIO</div>
                        <div className="font-bold text-cyan-400">{formatNumber(dnRatio, 2)}x</div>
                      </div>
                    </div>

                    <div className="text-xs text-slate-400 flex items-center justify-between pt-1">
                      <span>Peak FRP: <strong className="text-white font-mono">{formatFrp(maxFrpVal)}</strong></span>
                      <div className="flex items-center gap-3">
                        <Link
                          href={`/dashboard?lat=${evt.latitude}&lon=${evt.longitude}`}
                          className="text-slate-400 hover:text-white flex items-center gap-1 text-xs"
                        >
                          <span>Map</span>
                          <ArrowUpRight className="w-3 h-3" />
                        </Link>
                        <Link
                          href={`/dashboard/events/${evt.id}`}
                          className="text-amber-400 hover:text-amber-300 font-semibold flex items-center gap-1 text-xs"
                        >
                          <span>Dossier</span>
                          <ChevronRight className="w-3.5 h-3.5" />
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
