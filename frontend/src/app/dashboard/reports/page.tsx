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
import { fetchApi, API_BASE_URL } from "@/lib/api";
import { formatFrp } from "@/lib/formatters";
import { 
  FileText, Download, Shield, Calendar, 
  MapPin, CheckCircle2, ChevronRight, Eye,
  BarChart3, Database, FileCode, Layers, RefreshCw
} from "lucide-react";

export default function ReportsPage() {
  const [events, setEvents] = useState<ThermalEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState<"EVENT" | "ANALYTICAL" | "DATA_EXPORT">("EVENT");

  const loadReports = async () => {
    setLoading(true);
    try {
      const data = await fetchApi<ThermalEvent[]>("/events?limit=25");
      setEvents(data || []);
    } catch (err) {
      console.warn("Failed to load events for reports archive:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950 font-sans">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Standardized Page Header */}
          <PageHeader
            category="OFFICIAL DOCUMENTATION & EXPORTS"
            title="Intelligence Dossiers, Analytical Reports & Data Exports"
            description="Institutional decision support reporting repository. Distinguishes single-incident event dossiers, state/national analytical compliance summaries, and raw PostGIS data exports."
            icon={<FileText className="w-6 h-6 text-amber-400" />}
            actions={
              <button
                onClick={loadReports}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                title="Refresh Documents"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-amber-400" : ""}`} />
              </button>
            }
          />

          {/* 3-Category Report Hierarchy Tabs */}
          <div className="flex flex-wrap items-center gap-2 border-b border-agni-border pb-2">
            <button
              onClick={() => setActiveCategory("EVENT")}
              className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition-all flex items-center gap-2 ${
                activeCategory === "EVENT"
                  ? "bg-amber-500 text-slate-950 shadow-md"
                  : "bg-slate-900/60 hover:bg-slate-800 text-slate-300 border border-slate-800"
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>1. Event Dossiers (PDF)</span>
              <span className="px-1.5 py-0.2 rounded-full bg-slate-950/30 text-[10px]">
                {events.length}
              </span>
            </button>

            <button
              onClick={() => setActiveCategory("ANALYTICAL")}
              className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition-all flex items-center gap-2 ${
                activeCategory === "ANALYTICAL"
                  ? "bg-cyan-500 text-slate-950 shadow-md"
                  : "bg-slate-900/60 hover:bg-slate-800 text-slate-300 border border-slate-800"
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>2. Analytical Compliance Reports</span>
            </button>

            <button
              onClick={() => setActiveCategory("DATA_EXPORT")}
              className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition-all flex items-center gap-2 ${
                activeCategory === "DATA_EXPORT"
                  ? "bg-emerald-600 text-white shadow-md"
                  : "bg-slate-900/60 hover:bg-slate-800 text-slate-300 border border-slate-800"
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              <span>3. Data Pipelines & Schema Exports</span>
            </button>
          </div>

          {/* TIER 1: EVENT DOSSIERS */}
          {activeCategory === "EVENT" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Formal individual incident investigation dossiers with SHAP explanations and spatial buffer assets.</span>
                <span className="font-mono">{events.length} Available Event Dossiers</span>
              </div>

              {loading ? (
                <div className="space-y-3">
                  <CardSkeleton />
                  <CardSkeleton />
                  <CardSkeleton />
                </div>
              ) : events.length === 0 ? (
                <EmptyState
                  title="No Event Dossiers Available"
                  description="No thermal events match active criteria for dossier generation."
                  actionLabel="Refresh List"
                  onAction={loadReports}
                />
              ) : (
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
                            href={`${API_BASE_URL}/reports/event/${evt.id}/download`}
                            target="_blank"
                            rel="noreferrer"
                            className="px-3.5 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow-sm transition-all font-mono"
                          >
                            <Download className="w-3.5 h-3.5" />
                            <span>Download PDF</span>
                          </a>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TIER 2: ANALYTICAL COMPLIANCE REPORTS */}
          {activeCategory === "ANALYTICAL" && (
            <div className="space-y-4">
              <div className="text-xs text-slate-400">
                Macro-level multi-horizon compliance reports across states, industrial sectors, and air quality basins.
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-5 rounded-2xl bg-agni-card border border-cyan-500/30 space-y-3 shadow-md">
                  <div className="w-9 h-9 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
                    <BarChart3 className="w-5 h-5" />
                  </div>
                  <h3 className="text-base font-bold text-white">National Thermal Audit (2026)</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Comprehensive cross-sector analysis of 1,773,228 operational observations against the 6.45M historical baseline.
                  </p>
                  <div className="pt-2">
                    <a
                      href={`${API_BASE_URL}/reports/export/csv`}
                      target="_blank"
                      rel="noreferrer"
                      className="w-full py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 font-mono shadow-sm transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download Summary Brief</span>
                    </a>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-agni-card border border-cyan-500/30 space-y-3 shadow-md">
                  <div className="w-9 h-9 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
                    <Shield className="w-5 h-5" />
                  </div>
                  <h3 className="text-base font-bold text-white">State PCB Industrial Compliance</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    State Pollution Control Board compliance scorecard comparing reported maintenance flaring with satellite observations.
                  </p>
                  <div className="pt-2">
                    <a
                      href={`${API_BASE_URL}/reports/export/csv`}
                      target="_blank"
                      rel="noreferrer"
                      className="w-full py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 font-mono shadow-sm transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download PCB Ledger</span>
                    </a>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-agni-card border border-cyan-500/30 space-y-3 shadow-md">
                  <div className="w-9 h-9 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
                    <Layers className="w-5 h-5" />
                  </div>
                  <h3 className="text-base font-bold text-white">Baseline Shift & Climate Risk</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    90-day cell historical baseline shift tracking across 35,684 industrial facilities and mining lease boundaries.
                  </p>
                  <div className="pt-2">
                    <a
                      href={`${API_BASE_URL}/reports/export/csv`}
                      target="_blank"
                      rel="noreferrer"
                      className="w-full py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 font-mono shadow-sm transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download Baseline Report</span>
                    </a>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TIER 3: DATA EXPORT */}
          {activeCategory === "DATA_EXPORT" && (
            <div className="space-y-4">
              <div className="text-xs text-slate-400">
                Authoritative raw datasets and geospatial formats for GIS software (QGIS, ArcGIS) and data science pipelines.
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-5 rounded-2xl bg-agni-card border border-emerald-500/30 space-y-3 shadow-md">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <FileCode className="w-5 h-5 text-emerald-400" />
                      <h3 className="text-base font-bold text-white">GeoJSON FeatureCollection</h3>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold">
                      SPATIAL GIS
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Standard RFC 7946 GeoJSON containing all verified thermal clusters with point coordinates, 18-D feature properties, and risk assessments.
                  </p>
                  <div className="pt-2">
                    <a
                      href={`${API_BASE_URL}/portals/research/geojson-export`}
                      target="_blank"
                      rel="noreferrer"
                      className="w-full py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 font-mono shadow-sm transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Export GeoJSON Dataset</span>
                    </a>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-agni-card border border-emerald-500/30 space-y-3 shadow-md">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <Database className="w-5 h-5 text-emerald-400" />
                      <h3 className="text-base font-bold text-white">Tabular CSV Records Dump</h3>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold">
                      TABULAR CSV
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Full CSV export including event code, latitude, longitude, state, district, peak FRP, mean FRP, ML classification, and risk tier.
                  </p>
                  <div className="pt-2">
                    <a
                      href={`${API_BASE_URL}/reports/export/csv`}
                      target="_blank"
                      rel="noreferrer"
                      className="w-full py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 font-mono shadow-sm transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Export CSV Dump</span>
                    </a>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
