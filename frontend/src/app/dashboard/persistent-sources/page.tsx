"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import RiskBadge from "@/components/intelligence/RiskBadge";
import { ThermalEvent } from "@/types";
import { fetchApi } from "@/lib/api";
import { 
  Activity, MapPin, Calendar, Clock, 
  ChevronRight, ArrowRight, ShieldAlert, Sparkles
} from "lucide-react";

export default function PersistentSourcesPage() {
  const [events, setEvents] = useState<ThermalEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadEvents = async () => {
      try {
        const data = await fetchApi<ThermalEvent[]>("/events");
        // Filter persistent sources (persistence score >= 3.0 or detection count >= 5)
        const persistent = data.filter(
          (e) => (e.features?.persistence_score && e.features.persistence_score >= 3.0) || e.detection_count >= 5
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
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-6xl mx-auto">
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-agni-border pb-4">
            <div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5">
                <Activity className="w-6 h-6 text-emerald-400" />
                Persistent Thermal Sources & Recurrence Analytics
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Tracking multi-temporal thermal persistence, 24x7 day/night emission continuity, and recurrence rates.
              </p>
            </div>

            <span className="text-xs font-mono px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              {events.length} Persistent Emitters
            </span>
          </div>

          {/* Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {events.map((evt) => {
              const pScore = evt.features?.persistence_score || 7.0;
              const dnRatio = evt.features?.day_night_ratio || 1.2;
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
                          {evt.state}
                        </span>
                      </div>
                      <h3 className="text-base font-bold text-white mt-1">
                        {evt.prediction?.predicted_class || "Industrial Fire"}
                      </h3>
                    </div>
                    <RiskBadge level={evt.risk?.risk_level || "LOW"} score={evt.risk?.risk_score} />
                  </div>

                  <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 grid grid-cols-3 gap-2 text-xs font-mono text-center">
                    <div>
                      <div className="text-[10px] text-slate-500">PERSISTENCE</div>
                      <div className="font-bold text-emerald-400">{pScore.toFixed(1)} / 10.0</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500">OBSERVATIONS</div>
                      <div className="font-bold text-white">{evt.detection_count} Passes</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500">DAY/NIGHT</div>
                      <div className="font-bold text-cyan-400">{dnRatio.toFixed(2)}x</div>
                    </div>
                  </div>

                  <div className="text-xs text-slate-400 flex items-center justify-between pt-1">
                    <span>Peak FRP: <strong className="text-white font-mono">{evt.max_frp.toFixed(1)} MW</strong></span>
                    <Link
                      href={`/dashboard/events/${evt.id}`}
                      className="text-amber-400 hover:text-amber-300 font-semibold flex items-center gap-1"
                    >
                      <span>View Dossier</span>
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
