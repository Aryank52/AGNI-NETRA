"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import RiskBadge from "@/components/intelligence/RiskBadge";
import { ThermalEvent } from "@/types";
import { fetchApi } from "@/lib/api";
import { formatFrp } from "@/lib/formatters";
import { 
  FileText, Download, Shield, Calendar, 
  MapPin, CheckCircle2, ChevronRight, Eye
} from "lucide-react";

export default function ReportsPage() {
  const [events, setEvents] = useState<ThermalEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadReports = async () => {
      try {
        const data = await fetchApi<ThermalEvent[]>("/events");
        setEvents(data);
      } catch (err) {
        console.warn("Failed to load events for reports archive:", err);
      } finally {
        setLoading(false);
      }
    };
    loadReports();
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
                <FileText className="w-6 h-6 text-amber-400" />
                Automated Intelligence Dossiers & PDF Reports
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Generates formal AGNI-NETRA decision support reports complete with SHAP attributions, baseline comparisons, and risk matrices.
              </p>
            </div>

            <span className="text-xs font-mono px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 font-bold">
              {events.length} Available Dossiers
            </span>
          </div>

          {/* Reports Table / List */}
          <div className="space-y-3">
            {events.map((evt) => (
              <div
                key={evt.id}
                className="p-4 rounded-2xl bg-agni-card border border-agni-border hover:border-amber-500/40 transition-all flex flex-wrap items-center justify-between gap-4 shadow-lg"
              >
                <div className="flex items-center gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-amber-400 shrink-0">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold text-white">
                        AGNI_NETRA_Report_{evt.event_code}.pdf
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                        {evt.state}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {evt.prediction?.predicted_class || "Industrial Fire"} • Peak FRP: {formatFrp(evt.max_frp)} • {evt.detection_count} Observations
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <RiskBadge level={evt.risk?.risk_level || "LOW"} score={evt.risk?.risk_score} />

                  <div className="flex items-center gap-2">
                    <Link
                      href={`/dashboard/events/${evt.id}`}
                      className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                      title="Inspect Event Dossier"
                    >
                      <Eye className="w-4 h-4" />
                    </Link>

                    <a
                      href={`http://localhost:8000/api/v1/reports/event/${evt.id}/download`}
                      target="_blank"
                      rel="noreferrer"
                      className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs shadow-md flex items-center gap-1.5 transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download PDF</span>
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}
