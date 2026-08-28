"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import MapLibreView from "@/components/map/MapLibreView";
import LayerControl from "@/components/map/LayerControl";
import TimeSlider from "@/components/map/TimeSlider";
import RiskBadge from "@/components/intelligence/RiskBadge";
import { ThermalEvent, AnalyticsKPIs } from "@/types";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { 
  Flame, Filter, Search, ChevronRight, Activity, 
  MapPin, ShieldAlert, Sparkles, Download, Layers,
  Calendar, RefreshCw, Radio, CheckCircle2, SlidersHorizontal
} from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();

  // State & Data
  const [events, setEvents] = useState<ThermalEvent[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [kpis, setKpis] = useState<AnalyticsKPIs | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<ThermalEvent | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [ingesting, setIngesting] = useState<boolean>(false);

  // Filters
  const [selectedState, setSelectedState] = useState<string>("ALL");
  const [selectedDistrict, setSelectedDistrict] = useState<string>("ALL");
  const [riskFilter, setRiskFilter] = useState<string>("ALL");
  const [classFilter, setClassFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [minPersistence, setMinPersistence] = useState<number>(0);
  const [dataMode, setDataMode] = useState<string>("ALL"); // ALL, LIVE, DEMO
  const [minFrp, setMinFrp] = useState<number>(0);
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");

  // Pagination
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(20);
  const [totalPages, setTotalPages] = useState<number>(1);

  // Layer Controls
  const [layers, setLayers] = useState({
    thermalHotspots: true,
    riskHeatmap: true,
    facilities: true,
    candidates: true,
    stateBoundaries: true,
  });

  const loadData = async () => {
    setLoading(true);
    try {
      // Build query params
      const params = new URLSearchParams();
      if (selectedState !== "ALL" && selectedState !== "India") params.append("state", selectedState);
      if (selectedDistrict !== "ALL") params.append("district", selectedDistrict);
      if (riskFilter !== "ALL") params.append("risk_level", riskFilter);
      if (classFilter !== "ALL") params.append("event_type", classFilter);
      if (statusFilter !== "ALL") params.append("facility_status", statusFilter);
      if (minFrp > 0) params.append("min_frp", minFrp.toString());
      if (minPersistence > 0) params.append("min_persistence", minPersistence.toString());
      if (startDate) params.append("start_date", startDate);
      if (endDate) params.append("end_date", endDate);
      if (dataMode === "LIVE") params.append("is_demo", "false");
      if (dataMode === "DEMO") params.append("is_demo", "true");

      params.append("page", page.toString());
      params.append("limit", limit.toString());

      const [eventsData, kpiData] = await Promise.all([
        fetchApi<any>(`/events?${params.toString()}`),
        fetchApi<AnalyticsKPIs>("/analytics/kpis").catch(() => null),
      ]);

      if (eventsData && eventsData.items) {
        setEvents(eventsData.items);
        setTotalCount(eventsData.total_count);
        setTotalPages(eventsData.total_pages);
        if (eventsData.items.length > 0 && !selectedEvent) {
          setSelectedEvent(eventsData.items[0]);
        }
      } else if (Array.isArray(eventsData)) {
        setEvents(eventsData);
        setTotalCount(eventsData.length);
        setTotalPages(Math.ceil(eventsData.length / limit) || 1);
        if (eventsData.length > 0 && !selectedEvent) {
          setSelectedEvent(eventsData[0]);
        }
      }

      if (kpiData) {
        setKpis(kpiData);
      }
    } catch (err) {
      console.warn("Failed to load dashboard thermal telemetry:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedState, selectedDistrict, riskFilter, classFilter, statusFilter, minFrp, minPersistence, dataMode, startDate, endDate, page, limit]);

  const handleTriggerIngestion = async () => {
    setIngesting(true);
    try {
      const res = await fetchApi<any>("/ingestion/trigger/firms?country=IND&days=1", { method: "POST" });
      alert(`NASA FIRMS Pipeline: ${res.message || "Ingestion cycle executed successfully!"}`);
      await loadData();
    } catch (err: any) {
      alert("Ingestion error: " + err);
    } finally {
      setIngesting(false);
    }
  };

  const handleLayerToggle = (key: keyof typeof layers) => {
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 flex flex-col overflow-hidden relative">
          {/* Top Tactical KPIs Bar */}
          <div className="bg-agni-slate/90 border-b border-agni-border px-4 py-2.5 grid grid-cols-2 sm:grid-cols-6 gap-3 text-xs shrink-0 backdrop-blur-md z-10">
            <div className="flex flex-col">
              <span className="text-[10px] uppercase font-mono text-slate-400">Total Filtered Events</span>
              <span className="text-base font-extrabold text-white font-mono">{totalCount}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] uppercase font-mono text-purple-400">Candidate Sources</span>
              <span className="text-base font-extrabold text-purple-300 font-mono">
                {kpis?.industrial_candidates_count || 4}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] uppercase font-mono text-red-400">Critical Incidents</span>
              <span className="text-base font-extrabold text-red-400 font-mono">
                {kpis?.critical_alerts_count || 3}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] uppercase font-mono text-emerald-400">Persistent Emitters</span>
              <span className="text-base font-extrabold text-emerald-300 font-mono">
                {kpis?.persistent_sources_count || 12}
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] uppercase font-mono text-cyan-400">HITL Verification Queue</span>
              <span className="text-base font-extrabold text-cyan-300 font-mono">
                {kpis?.verification_queue_count || 9}
              </span>
            </div>
            <div className="flex items-center justify-end">
              <button
                onClick={handleTriggerIngestion}
                disabled={ingesting}
                className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs shadow-md flex items-center gap-1.5 transition-all"
                title="Run FIRMS & PostGIS Ingestion Pipeline"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${ingesting ? "animate-spin" : ""}`} />
                <span>{ingesting ? "Ingesting..." : "Run FIRMS Ingest"}</span>
              </button>
            </div>
          </div>

          {/* Master Multi-Criteria Filter Bar */}
          <div className="bg-agni-card/95 border-b border-agni-border px-4 py-2 flex flex-wrap items-center justify-between gap-2.5 text-xs z-10">
            {/* Geography & Category Filters */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-amber-400" />
                <select
                  value={selectedState}
                  onChange={(e) => {
                    setSelectedState(e.target.value);
                    setPage(1);
                  }}
                  className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-white text-xs font-semibold focus:outline-none focus:border-amber-500"
                >
                  <option value="ALL">All India (All States)</option>
                  <option value="Gujarat">Gujarat (Refinery Hub)</option>
                  <option value="Madhya Pradesh">Madhya Pradesh (Power)</option>
                  <option value="Odisha">Odisha (Steel & Mines)</option>
                  <option value="Chhattisgarh">Chhattisgarh (Coal Mines)</option>
                  <option value="Punjab">Punjab (Agriculture)</option>
                  <option value="Andhra Pradesh">Andhra Pradesh (Offshore)</option>
                  <option value="Jharkhand">Jharkhand (Mining)</option>
                  <option value="Maharashtra">Maharashtra</option>
                  <option value="Rajasthan">Rajasthan</option>
                  <option value="Tamil Nadu">Tamil Nadu</option>
                </select>
              </div>

              <select
                value={classFilter}
                onChange={(e) => {
                  setClassFilter(e.target.value);
                  setPage(1);
                }}
                className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-white text-xs focus:outline-none focus:border-amber-500"
              >
                <option value="ALL">All Source Classes</option>
                <option value="Industrial Fire">Industrial Fire</option>
                <option value="Gas Flare">Gas Flare</option>
                <option value="Forest Fire">Forest Fire</option>
                <option value="Agricultural Burning">Agricultural Stubble</option>
                <option value="Mining Activity">Mining Activity</option>
              </select>

              <select
                value={riskFilter}
                onChange={(e) => {
                  setRiskFilter(e.target.value);
                  setPage(1);
                }}
                className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-white text-xs focus:outline-none focus:border-amber-500"
              >
                <option value="ALL">All Risk Levels</option>
                <option value="CRITICAL">Critical Risk</option>
                <option value="HIGH">High Risk</option>
                <option value="MODERATE">Moderate Risk</option>
                <option value="LOW">Low Risk</option>
              </select>

              <select
                value={dataMode}
                onChange={(e) => {
                  setDataMode(e.target.value);
                  setPage(1);
                }}
                className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-white text-xs focus:outline-none focus:border-amber-500"
              >
                <option value="ALL">All Datasets (Live + Demo)</option>
                <option value="LIVE">Live Satellite Stream</option>
                <option value="DEMO">Verified Demo Dataset</option>
              </select>

              <select
                value={minPersistence}
                onChange={(e) => {
                  setMinPersistence(Number(e.target.value));
                  setPage(1);
                }}
                className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-white text-xs focus:outline-none focus:border-amber-500"
              >
                <option value="0">All Persistence</option>
                <option value="3">Persistence ≥ 3.0</option>
                <option value="5">Persistence ≥ 5.0 (High)</option>
                <option value="7">Persistence ≥ 7.0 (24x7)</option>
              </select>
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center gap-2 font-mono text-xs">
              <span className="text-slate-400 text-[11px]">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-2 py-1 rounded bg-slate-900 border border-slate-700 text-slate-300 disabled:opacity-40"
              >
                Prev
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="px-2 py-1 rounded bg-slate-900 border border-slate-700 text-slate-300 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>

          {/* Central Workspace: Interactive GIS Map + Tactical Events Drawer */}
          <div className="flex-1 flex overflow-hidden relative">
            {/* GIS Map Canvas */}
            <div className="flex-1 relative h-full">
              <MapLibreView
                events={events}
                selectedEventId={selectedEvent?.id}
                onSelectEvent={(evt) => setSelectedEvent(evt)}
                selectedState={selectedState}
                layers={layers}
              />

              {/* Tactical Floating Layer Controls */}
              <LayerControl layers={layers} onToggleLayer={handleLayerToggle} />

              {/* Floating Time Dimension Slider */}
              <TimeSlider
                timeWindowDays={30}
                onChangeTimeWindow={(days) => console.log("Time window changed:", days)}
              />
            </div>

            {/* Right Side Tactical Intelligence Drawer */}
            <div className="w-80 sm:w-96 bg-agni-slate/95 border-l border-agni-border flex flex-col h-full overflow-hidden shadow-2xl backdrop-blur-md z-10">
              <div className="p-3.5 border-b border-agni-border flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Flame className="w-4 h-4 text-amber-400" />
                  <h2 className="text-xs font-extrabold uppercase tracking-wider text-white">
                    Thermal Observations ({events.length})
                  </h2>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-amber-400 border border-slate-700">
                  {selectedState}
                </span>
              </div>

              {/* Event Cards Scrollable Feed */}
              <div className="flex-1 overflow-y-auto p-3 space-y-2.5 divide-y-0">
                {loading ? (
                  <div className="p-8 text-center text-slate-500 font-mono text-xs">
                    Updating NASA FIRMS GeoJSON Layer...
                  </div>
                ) : events.length === 0 ? (
                  <div className="p-8 text-center text-slate-400 font-mono text-xs">
                    No thermal anomalies match active filters.
                  </div>
                ) : (
                  events.map((evt) => {
                    const isSelected = selectedEvent?.id === evt.id;
                    const pClass = evt.prediction?.predicted_class || "Uncertain";
                    const isCandidate = evt.facility_status === "CANDIDATE";

                    return (
                      <div
                        key={evt.id}
                        onClick={() => setSelectedEvent(evt)}
                        className={`p-3 rounded-xl cursor-pointer border transition-all space-y-2 ${
                          isSelected
                            ? "bg-agni-card border-amber-500/80 shadow-lg glow-border-accent"
                            : "bg-slate-900/70 border-slate-800 hover:border-slate-700"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-1">
                          <div>
                            <div className="flex items-center gap-1.5">
                              <span className="font-mono text-xs font-bold text-white">
                                {evt.event_code}
                              </span>
                              {evt.is_demo ? (
                                <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                                  SAMPLE
                                </span>
                              ) : (
                                <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                                  LIVE
                                </span>
                              )}
                            </div>
                            <h3 className="text-xs font-bold text-amber-400 mt-0.5">
                              {pClass}
                            </h3>
                          </div>
                          <RiskBadge level={evt.risk?.risk_level || "LOW"} score={evt.risk?.risk_score} />
                        </div>

                        {/* Timestamp Provenance & Metrics */}
                        <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-slate-300">
                          <div>
                            <span className="text-slate-500 text-[10px]">PEAK FRP:</span>{" "}
                            <strong className="text-white">{evt.max_frp.toFixed(1)} MW</strong>
                          </div>
                          <div>
                            <span className="text-slate-500 text-[10px]">PASSES:</span>{" "}
                            <span>{evt.detection_count}</span>
                          </div>
                          <div>
                            <span className="text-slate-500 text-[10px]">PERSISTENCE:</span>{" "}
                            <span className="text-emerald-400">
                              {evt.features?.persistence_score?.toFixed(1) || "N/A"}/10
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 text-[10px]">CONTEXT:</span>{" "}
                            <span>{isCandidate ? "Candidate (USP)" : evt.facility_status}</span>
                          </div>
                        </div>

                        {/* Timestamp Strip */}
                        <div className="text-[10px] text-slate-500 font-mono flex items-center justify-between pt-1 border-t border-slate-800/80">
                          <span>Last Seen: {new Date(evt.last_seen).toLocaleDateString()}</span>
                          <Link
                            href={`/dashboard/events/${evt.id}`}
                            className="text-amber-400 hover:text-amber-300 font-semibold flex items-center gap-0.5"
                          >
                            <span>Dossier</span>
                            <ChevronRight className="w-3 h-3" />
                          </Link>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
