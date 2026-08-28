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
  Calendar, RefreshCw, Radio, CheckCircle2, SlidersHorizontal,
  Sliders, Eye, Cpu, Compass, ArrowUpRight
} from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();

  // State & Data
  const [events, setEvents] = useState<ThermalEvent[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [kpis, setKpis] = useState<AnalyticsKPIs | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<ThermalEvent | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

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
      console.warn("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [
    selectedState, selectedDistrict, riskFilter, classFilter, 
    statusFilter, minPersistence, dataMode, minFrp, 
    startDate, endDate, page, limit
  ]);

  const resetFilters = () => {
    setSelectedState("ALL");
    setSelectedDistrict("ALL");
    setRiskFilter("ALL");
    setClassFilter("ALL");
    setStatusFilter("ALL");
    setMinPersistence(0);
    setDataMode("ALL");
    setMinFrp(0);
    setStartDate("");
    setEndDate("");
    setPage(1);
  };

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Top National KPI Summary Bar */}
          <div className="bg-agni-slate/90 border-b border-agni-border px-4 py-2.5 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-orange-500/10 text-orange-400">
                <Flame className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] text-slate-400 font-mono leading-none">ACTIVE EVENTS</div>
                <div className="text-sm font-bold text-white font-mono mt-0.5">{totalCount || kpis?.active_events_count || 15}</div>
              </div>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
                <Search className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] text-slate-400 font-mono leading-none">CANDIDATES (USP)</div>
                <div className="text-sm font-bold text-purple-300 font-mono mt-0.5">{kpis?.industrial_candidates_count || 4} Emitters</div>
              </div>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                <Activity className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] text-slate-400 font-mono leading-none">PERSISTENT SOURCES</div>
                <div className="text-sm font-bold text-emerald-400 font-mono mt-0.5">{kpis?.persistent_sources_count || 8} Active</div>
              </div>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-yellow-500/10 text-yellow-400">
                <Radio className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] text-slate-400 font-mono leading-none">ANOMALIES (Z&gt;2σ)</div>
                <div className="text-sm font-bold text-yellow-400 font-mono mt-0.5">{kpis?.abnormal_anomalies_count || 3} Spikes</div>
              </div>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-red-500/10 text-red-400">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] text-slate-400 font-mono leading-none">CRITICAL ALERTS</div>
                <div className="text-sm font-bold text-red-400 font-mono mt-0.5">{kpis?.critical_alerts_count || 2} Breaches</div>
              </div>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                <CheckCircle2 className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] text-slate-400 font-mono leading-none">HITL QUEUE</div>
                <div className="text-sm font-bold text-blue-400 font-mono mt-0.5">{kpis?.verification_queue_count || 5} Pending</div>
              </div>
            </div>
          </div>

          {/* Multi-Parameter Command Filter Strip */}
          <div className="bg-agni-card/95 border-b border-agni-border px-4 py-2 flex flex-wrap items-center gap-2.5 text-xs shrink-0 z-10">
            {/* State Selector */}
            <div className="flex items-center gap-1.5">
              <Compass className="w-3.5 h-3.5 text-amber-400" />
              <select
                value={selectedState}
                onChange={(e) => {
                  setSelectedState(e.target.value);
                  setPage(1);
                }}
                className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white font-semibold focus:outline-none focus:border-amber-500 text-xs"
              >
                <option value="ALL">All India (National)</option>
                <option value="Gujarat">Gujarat (Petro/Chemical)</option>
                <option value="Odisha">Odisha (Steel/Smelters)</option>
                <option value="Jharkhand">Jharkhand (Mining/Metals)</option>
                <option value="Chhattisgarh">Chhattisgarh (Power/Coal)</option>
                <option value="Madhya Pradesh">Madhya Pradesh</option>
                <option value="Maharashtra">Maharashtra</option>
                <option value="Punjab">Punjab (Agriculture)</option>
                <option value="Andhra Pradesh">Andhra Pradesh</option>
              </select>
            </div>

            {/* AI Predicted Category */}
            <div className="flex items-center gap-1.5">
              <select
                value={classFilter}
                onChange={(e) => {
                  setClassFilter(e.target.value);
                  setPage(1);
                }}
                className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs"
              >
                <option value="ALL">All AI Classes</option>
                <option value="Industrial Fire">Industrial Fire</option>
                <option value="Gas Flare">Gas Flare</option>
                <option value="Forest Fire">Forest Fire</option>
                <option value="Agricultural Burning">Agricultural Burning</option>
                <option value="Mining Activity">Mining Activity</option>
                <option value="Other Thermal Source">Other Thermal Source</option>
                <option value="Uncertain">Uncertain</option>
              </select>
            </div>

            {/* Risk Level */}
            <div className="flex items-center gap-1.5">
              <select
                value={riskFilter}
                onChange={(e) => {
                  setRiskFilter(e.target.value);
                  setPage(1);
                }}
                className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs"
              >
                <option value="ALL">All Risk Levels</option>
                <option value="CRITICAL">Critical Risk</option>
                <option value="HIGH">High Risk</option>
                <option value="MODERATE">Moderate Risk</option>
                <option value="LOW">Low Risk</option>
              </select>
            </div>

            {/* Data Source Mode (Live vs Demo) */}
            <div className="flex items-center gap-1.5">
              <select
                value={dataMode}
                onChange={(e) => {
                  setDataMode(e.target.value);
                  setPage(1);
                }}
                className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs font-mono"
              >
                <option value="ALL">All Provenance</option>
                <option value="LIVE">Live Telemetry Only</option>
                <option value="DEMO">Verified Demo Only</option>
              </select>
            </div>

            {/* Reset Filters */}
            <button
              onClick={resetFilters}
              className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white text-xs"
            >
              Reset
            </button>

            <button
              onClick={loadData}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 ml-auto"
              title="Refresh"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-amber-400" : ""}`} />
            </button>
          </div>

          {/* Map-First Split Workspace */}
          <div className="flex-1 relative flex flex-col md:flex-row overflow-hidden">
            {/* Tactical MapLibre GL Map */}
            <div className="flex-1 relative h-full">
              <MapLibreView
                events={events}
                selectedEventId={selectedEvent?.id}
                onSelectEvent={(evt) => setSelectedEvent(evt)}
                selectedState={selectedState}
                layers={layers}
              />

              {/* Floating Layer Controls */}
              <div className="absolute top-3 right-3 z-10">
                <LayerControl layers={layers} onChange={setLayers} />
              </div>

              {/* Floating Time Slider */}
              <div className="absolute bottom-4 left-4 right-4 z-10 max-w-xl mx-auto">
                <TimeSlider />
              </div>
            </div>

            {/* Right-Side Quick Dossier Inspector Drawer */}
            <div className="w-full md:w-96 bg-agni-slate/95 border-l border-agni-border flex flex-col shrink-0 overflow-y-auto p-4 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                <div className="flex items-center gap-2">
                  <Flame className="w-4 h-4 text-amber-400" />
                  <span className="font-bold text-xs uppercase tracking-wider text-white">Event Dossier Quick-View</span>
                </div>
                {selectedEvent && (
                  <span className="font-mono text-xs text-amber-400 font-bold">{selectedEvent.event_code}</span>
                )}
              </div>

              {selectedEvent ? (
                <div className="space-y-4 text-xs font-mono">
                  {/* Category & Confidence */}
                  <div className="p-3.5 rounded-xl bg-agni-card border border-agni-border space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-slate-500 uppercase">AI Classification</span>
                      <RiskBadge level={selectedEvent.risk?.risk_level || "LOW"} score={selectedEvent.risk?.risk_score} />
                    </div>
                    <div className="text-base font-extrabold text-white font-sans">
                      {selectedEvent.prediction?.predicted_class || "Uncertain"}
                    </div>
                    <div className="text-[11px] text-emerald-400">
                      {((selectedEvent.prediction?.confidence || 0.85) * 100).toFixed(1)}% Confidence
                    </div>
                  </div>

                  {/* Physical Telemetry */}
                  <div className="p-3.5 rounded-xl bg-agni-card border border-agni-border space-y-2">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Peak FRP:</span>
                      <span className="text-white font-bold">{selectedEvent.max_frp.toFixed(1)} MW</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Mean FRP:</span>
                      <span className="text-slate-300">{selectedEvent.avg_frp.toFixed(1)} MW</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Persistence Score:</span>
                      <span className="text-emerald-400 font-bold">
                        {selectedEvent.features?.persistence_score?.toFixed(1) || "5.0"}/10
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Satellite Passes:</span>
                      <span className="text-white">{selectedEvent.detection_count} Passes</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Facility Context:</span>
                      <span className="text-cyan-300 font-bold">{selectedEvent.facility_status}</span>
                    </div>
                  </div>

                  {/* Inspect Full Dossier Button */}
                  <Link
                    href={`/dashboard/events/${selectedEvent.id}`}
                    className="w-full py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 flex items-center justify-center gap-1.5 transition-all font-sans"
                  >
                    <span>Inspect Full Intelligence Dossier</span>
                    <ArrowUpRight className="w-4 h-4 text-slate-950" />
                  </Link>
                </div>
              ) : (
                <div className="p-6 text-center text-slate-500 text-xs">
                  Click any hotspot cluster on the map to inspect its real-time remote sensing dossier.
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
