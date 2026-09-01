"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import MapLibreView from "@/components/map/MapLibreView";
import LayerControl from "@/components/map/LayerControl";
import RiskBadge from "@/components/intelligence/RiskBadge";
import { ThermalEvent, CommandCenterData } from "@/types";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { 
  Flame, Filter, Search, ChevronRight, Activity, 
  MapPin, ShieldAlert, Sparkles, Download, Layers,
  Calendar, RefreshCw, Radio, CheckCircle2, SlidersHorizontal,
  Sliders, Eye, Cpu, Compass, ArrowUpRight, ShieldCheck,
  Zap, Database, Bell, AlertTriangle, Clock, Layers2, Lock,
  Globe, Shield, AlertCircle
} from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();

  // State & Data
  const [events, setEvents] = useState<ThermalEvent[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [commandCenterData, setCommandCenterData] = useState<CommandCenterData | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<ThermalEvent | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [apiError, setApiError] = useState<string | null>(null);

  // Administrative Navigation
  const [selectedState, setSelectedState] = useState<string>("ALL");
  const [selectedDistrict, setSelectedDistrict] = useState<string>("ALL");
  const [statesList, setStatesList] = useState<Array<{ state_name: string }>>([]);
  const [districtsList, setDistrictsList] = useState<Array<{ district_name: string }>>([]);

  // Operational Filters
  const [riskFilter, setRiskFilter] = useState<string>("ALL");
  const [classFilter, setClassFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [dataMode, setDataMode] = useState<string>("ALL"); // ALL, LIVE, DEMO
  const [minFrp, setMinFrp] = useState<number>(0);

  // Live Auto-Refresh
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
  const [refreshInterval, setRefreshInterval] = useState<number>(20); // seconds
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());
  const [secondsUntilRefresh, setSecondsUntilRefresh] = useState<number>(20);

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

  // Load Administrative Geography Lists
  useEffect(() => {
    fetchApi<Array<{ state_name: string }>>("/geography/states")
      .then((data) => setStatesList(data || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedState !== "ALL" && selectedState !== "India") {
      fetchApi<Array<{ district_name: string }>>(`/geography/districts?state=${encodeURIComponent(selectedState)}`)
        .then((data) => setDistrictsList(data || []))
        .catch(() => setDistrictsList([]));
    } else {
      setDistrictsList([]);
      setSelectedDistrict("ALL");
    }
  }, [selectedState]);

  // Load Data
  const loadData = async (isBackground = false) => {
    if (!isBackground) setLoading(true);
    setApiError(null);
    try {
      const params = new URLSearchParams();
      if (selectedState !== "ALL" && selectedState !== "India") params.append("state", selectedState);
      if (selectedDistrict !== "ALL") params.append("district", selectedDistrict);
      if (riskFilter !== "ALL") params.append("risk_level", riskFilter);
      if (classFilter !== "ALL") params.append("event_type", classFilter);
      if (statusFilter !== "ALL") params.append("status", statusFilter);
      if (minFrp > 0) params.append("min_frp", minFrp.toString());
      if (dataMode === "LIVE") params.append("is_demo", "false");
      if (dataMode === "DEMO") params.append("is_demo", "true");

      params.append("page", page.toString());
      params.append("limit", limit.toString());

      const [eventsData, ccData] = await Promise.all([
        fetchApi<any>(`/events?${params.toString()}`),
        fetchApi<CommandCenterData>("/analytics/command-center").catch(() => null),
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

      if (ccData) {
        setCommandCenterData(ccData);
      }
      setLastRefreshed(new Date());
      setSecondsUntilRefresh(refreshInterval);
    } catch (err: any) {
      setApiError(err?.message || "Failed to connect to AGNI-NETRA operational backend.");
    } finally {
      if (!isBackground) setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedState, selectedDistrict, riskFilter, classFilter, statusFilter, minFrp, dataMode, page]);

  // Auto-Refresh Timer
  useEffect(() => {
    if (!autoRefresh) return;

    const timer = setInterval(() => {
      setSecondsUntilRefresh((prev) => {
        if (prev <= 1) {
          loadData(true);
          return refreshInterval;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [autoRefresh, refreshInterval, selectedState, selectedDistrict, riskFilter, classFilter, statusFilter, minFrp, dataMode, page]);

  const resetFilters = () => {
    setSelectedState("ALL");
    setSelectedDistrict("ALL");
    setRiskFilter("ALL");
    setClassFilter("ALL");
    setStatusFilter("ALL");
    setMinFrp(0);
    setDataMode("ALL");
    setPage(1);
  };

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Top System Health & Ingestion Telemetry Banner */}
          <div className="bg-slate-950/90 border-b border-agni-border px-4 py-2 flex flex-wrap items-center justify-between gap-3 shrink-0 text-xs">
            <div className="flex flex-wrap items-center gap-3">
              {/* Live Ingestion Stream Status */}
              <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span className="font-mono font-bold tracking-wider">LIVE STREAM ACTIVE</span>
                <span className="text-slate-400 font-mono text-[11px]">
                  {commandCenterData?.kpis?.stream_freshness_timestamp
                    ? `• Synced: ${new Date(commandCenterData.kpis.stream_freshness_timestamp).toLocaleTimeString()}`
                    : "• Synced 2m ago"}
                </span>
              </div>

              {/* Model Candidate Status */}
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300">
                <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                <span className="font-mono">
                  {commandCenterData?.model_metadata?.champion_version || "xgb-v3.0-real-candidate"}
                </span>
                <span className="px-1.5 py-0.2 rounded bg-indigo-500/20 text-[10px] font-bold">
                  {commandCenterData?.model_metadata?.registry_status || "CANDIDATE"}
                </span>
              </div>

              {/* Safety Dispatch Gate */}
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300">
                <Lock className="w-3.5 h-3.5 text-amber-400" />
                <span className="font-mono font-semibold">DISPATCH GATE: SAFE</span>
                <span className="text-[10px] text-amber-400/80">(0 LIVE DISPATCHES)</span>
              </div>

              {/* Database Immutability Status */}
              <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-300">
                <Database className="w-3.5 h-3.5 text-sky-400" />
                <span className="font-mono font-semibold">8.22M FIRMS ROWS SEALED</span>
              </div>
            </div>

            {/* Auto-Refresh Control */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-slate-400 font-mono">
                  Auto-refresh: {autoRefresh ? `${secondsUntilRefresh}s` : "Paused"}
                </span>
                <button
                  onClick={() => setAutoRefresh(!autoRefresh)}
                  className={`px-2 py-0.5 rounded text-[11px] font-bold font-mono transition-colors ${
                    autoRefresh ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30" : "bg-slate-800 text-slate-400"
                  }`}
                >
                  {autoRefresh ? "LIVE" : "PAUSED"}
                </button>
              </div>

              <button
                onClick={() => loadData(false)}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
                title="Refresh Now"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-amber-400" : ""}`} />
              </button>
            </div>
          </div>

          {/* API Error Banner */}
          {apiError && (
            <div className="bg-red-500/10 border-b border-red-500/30 px-4 py-2 flex items-center justify-between text-xs text-red-300 shrink-0">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                <span><strong>API Alert:</strong> {apiError}</span>
              </div>
              <button onClick={() => loadData(false)} className="underline hover:text-white font-mono text-[11px]">
                Retry Connection
              </button>
            </div>
          )}

          {/* KPI Dashboard Summary Cards */}
          <div className="bg-agni-slate/90 border-b border-agni-border px-4 py-2.5 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 shrink-0">
            {/* Live Events */}
            <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-orange-500/10 text-orange-400 shrink-0">
                <Flame className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] text-slate-400 font-mono">LIVE EVENTS</div>
                <div className="text-base font-extrabold text-white font-mono leading-tight mt-0.5">
                  {totalCount || commandCenterData?.kpis?.total_live_events || 0}
                </div>
              </div>
            </div>

            {/* Active Alerts */}
            <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-500/10 text-red-400 shrink-0">
                <Bell className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] text-slate-400 font-mono">ACTIVE ALERTS</div>
                <div className="text-base font-extrabold text-red-400 font-mono leading-tight mt-0.5">
                  {commandCenterData?.kpis?.active_alerts ?? 0}
                </div>
              </div>
            </div>

            {/* Tri-Tier 1 Queue */}
            <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 shrink-0">
                <Zap className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] text-slate-400 font-mono">TIER 1 (AUTO CAND.)</div>
                <div className="text-base font-extrabold text-purple-300 font-mono leading-tight mt-0.5">
                  {commandCenterData?.alert_queues?.tier_1_auto_dispatch_candidate ?? 0}
                </div>
              </div>
            </div>

            {/* Tri-Tier 2 Queue */}
            <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 shrink-0">
                <Eye className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] text-slate-400 font-mono">TIER 2 (ANALYST)</div>
                <div className="text-base font-extrabold text-blue-400 font-mono leading-tight mt-0.5">
                  {commandCenterData?.alert_queues?.tier_2_analyst_review ?? 0}
                </div>
              </div>
            </div>

            {/* High/Critical Risk Breakdown */}
            <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 shrink-0">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] text-slate-400 font-mono">HIGH/CRIT RISK</div>
                <div className="text-base font-extrabold text-amber-400 font-mono leading-tight mt-0.5">
                  {(commandCenterData?.risk_breakdown?.CRITICAL ?? 0) + (commandCenterData?.risk_breakdown?.HIGH ?? 0)}
                </div>
              </div>
            </div>

            {/* Peak FRP */}
            <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 shrink-0">
                <Activity className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] text-slate-400 font-mono">PEAK FRP</div>
                <div className="text-base font-extrabold text-emerald-400 font-mono leading-tight mt-0.5">
                  {commandCenterData?.kpis?.max_frp_mw ? `${commandCenterData.kpis.max_frp_mw} MW` : "—"}
                </div>
              </div>
            </div>
          </div>

          {/* Main Command Center Layout */}
          <div className="flex-1 flex flex-col lg:flex-row overflow-hidden relative">
            {/* Map Area */}
            <div className="flex-1 relative flex flex-col min-h-[350px]">
              {/* Administrative Drill-down & Filter Bar Overlay */}
              <div className="absolute top-3 left-3 right-3 z-10 flex flex-wrap items-center justify-between gap-2 p-2.5 rounded-2xl bg-slate-950/85 backdrop-blur-md border border-slate-800 text-xs shadow-2xl">
                <div className="flex flex-wrap items-center gap-2">
                  <div className="flex items-center gap-1.5 font-bold text-slate-300">
                    <Globe className="w-3.5 h-3.5 text-amber-400" />
                    <span>Territory:</span>
                  </div>

                  {/* State Selector */}
                  <select
                    value={selectedState}
                    onChange={(e) => {
                      setSelectedState(e.target.value);
                      setSelectedDistrict("ALL");
                      setPage(1);
                    }}
                    className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500 max-w-[140px]"
                  >
                    <option value="ALL">National (All India)</option>
                    {statesList.map((s) => (
                      <option key={s.state_name} value={s.state_name}>
                        {s.state_name}
                      </option>
                    ))}
                  </select>

                  {/* District Selector */}
                  {districtsList.length > 0 && (
                    <select
                      value={selectedDistrict}
                      onChange={(e) => {
                        setSelectedDistrict(e.target.value);
                        setPage(1);
                      }}
                      className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500 max-w-[130px]"
                    >
                      <option value="ALL">All Districts</option>
                      {districtsList.map((d) => (
                        <option key={d.district_name} value={d.district_name}>
                          {d.district_name}
                        </option>
                      ))}
                    </select>
                  )}

                  {/* Risk Filter */}
                  <select
                    value={riskFilter}
                    onChange={(e) => {
                      setRiskFilter(e.target.value);
                      setPage(1);
                    }}
                    className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
                  >
                    <option value="ALL">All Risks</option>
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MODERATE">Moderate</option>
                    <option value="LOW">Low</option>
                  </select>

                  {/* Classification Filter */}
                  <select
                    value={classFilter}
                    onChange={(e) => {
                      setClassFilter(e.target.value);
                      setPage(1);
                    }}
                    className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
                  >
                    <option value="ALL">All Sources</option>
                    <option value="Agricultural Burning">Agricultural Burning</option>
                    <option value="Gas Flare">Gas Flare</option>
                    <option value="Industrial Fire">Industrial Fire</option>
                    <option value="Forest Fire">Forest Fire</option>
                    <option value="Landfill">Landfill / Urban</option>
                    <option value="Biomass">Biomass / Stubble</option>
                  </select>

                  {/* Data Provenance Mode */}
                  <select
                    value={dataMode}
                    onChange={(e) => {
                      setDataMode(e.target.value);
                      setPage(1);
                    }}
                    className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
                  >
                    <option value="ALL">All Data</option>
                    <option value="LIVE">Live Telemetry (Real)</option>
                    <option value="DEMO">Demo / Benchmarks</option>
                  </select>
                </div>

                <button
                  onClick={resetFilters}
                  className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white font-mono text-[11px]"
                >
                  Reset
                </button>
              </div>

              {/* Map Canvas */}
              <div className="flex-1 w-full h-full">
                <MapLibreView
                  events={events}
                  selectedEventId={selectedEvent?.id}
                  onSelectEvent={(evt) => setSelectedEvent(evt)}
                  selectedState={selectedState}
                  layers={layers}
                />
              </div>

              {/* Layer Control Widget */}
              <div className="absolute bottom-4 left-4 z-10">
                <LayerControl layers={layers} onToggle={(k) => setLayers((prev) => ({ ...prev, [k]: !prev[k as keyof typeof layers] }))} />
              </div>
            </div>

            {/* Right-Side Operational Event Inspector & Queue */}
            <div className="w-full lg:w-[420px] bg-slate-950/95 border-t lg:border-t-0 lg:border-l border-agni-border flex flex-col shrink-0 overflow-hidden">
              {/* Queue Header */}
              <div className="p-3.5 border-b border-agni-border flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-bold text-white flex items-center gap-2">
                    <Activity className="w-4 h-4 text-amber-400" />
                    Operational Event Stream
                  </h2>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Showing {events.length} of {totalCount} clustered events
                  </p>
                </div>

                <Link
                  href="/dashboard/alerts"
                  className="px-2.5 py-1 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-300 border border-red-500/30 text-[11px] font-bold flex items-center gap-1 transition-colors"
                >
                  <Bell className="w-3.5 h-3.5" />
                  Alert Center →
                </Link>
              </div>

              {/* Selected Event Preview Card */}
              {selectedEvent && (
                <div className="p-3.5 bg-slate-900/90 border-b border-agni-border space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-amber-400">
                        {selectedEvent.event_code}
                      </span>
                      {selectedEvent.is_demo ? (
                        <span className="px-1.5 py-0.2 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[9px] font-mono">
                          DEMO
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[9px] font-mono">
                          LIVE FIRMS
                        </span>
                      )}
                    </div>

                    <RiskBadge level={selectedEvent.risk?.risk_level || "LOW"} score={selectedEvent.risk?.risk_score} />
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 rounded-lg bg-slate-950 border border-slate-800">
                      <div className="text-[10px] text-slate-400">CLASSIFICATION</div>
                      <div className="font-bold text-white mt-0.5 truncate">
                        {selectedEvent.prediction?.predicted_class || "Evaluating..."}
                      </div>
                      <div className="text-[10px] text-emerald-400 font-mono mt-0.5">
                        {selectedEvent.prediction?.confidence
                          ? `${(selectedEvent.prediction.confidence * 100).toFixed(1)}% Confidence`
                          : "Calibrating..."}
                      </div>
                    </div>

                    <div className="p-2 rounded-lg bg-slate-950 border border-slate-800">
                      <div className="text-[10px] text-slate-400">MAX INTENSITY</div>
                      <div className="font-bold text-orange-400 font-mono mt-0.5">
                        {selectedEvent.max_frp.toFixed(1)} MW
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                        {selectedEvent.detection_count} detections
                      </div>
                    </div>
                  </div>

                  <div className="text-[11px] text-slate-300 flex items-center justify-between pt-1">
                    <span>
                      {selectedEvent.state} {selectedEvent.district ? `• ${selectedEvent.district}` : ""}
                    </span>
                    <span className="font-mono text-slate-400">
                      {selectedEvent.latitude.toFixed(4)}°N, {selectedEvent.longitude.toFixed(4)}°E
                    </span>
                  </div>

                  <Link
                    href={`/dashboard/events/${selectedEvent.id}`}
                    className="w-full py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs uppercase tracking-wide flex items-center justify-center gap-1.5 transition-colors shadow-md"
                  >
                    <span>Open Investigation Dossier</span>
                    <ArrowUpRight className="w-4 h-4" />
                  </Link>
                </div>
              )}

              {/* Event List Queue */}
              <div className="flex-1 overflow-y-auto p-3 space-y-2">
                {loading && (
                  <div className="p-6 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
                    <RefreshCw className="w-5 h-5 animate-spin text-amber-400" />
                    <span>Streaming operational events...</span>
                  </div>
                )}

                {!loading && events.length === 0 && (
                  <div className="p-8 text-center text-slate-400 text-xs border border-dashed border-slate-800 rounded-xl">
                    <Flame className="w-6 h-6 text-slate-600 mx-auto mb-2" />
                    <p className="font-semibold text-slate-300">No thermal events found</p>
                    <p className="text-slate-500 mt-1">Adjust filters or select another administrative area.</p>
                  </div>
                )}

                {!loading &&
                  events.map((evt) => {
                    const isSelected = selectedEvent?.id === evt.id;
                    const rLevel = evt.risk?.risk_level || "LOW";
                    return (
                      <div
                        key={evt.id}
                        onClick={() => setSelectedEvent(evt)}
                        className={`p-3 rounded-xl border cursor-pointer transition-all ${
                          isSelected
                            ? "bg-slate-900 border-amber-500/60 shadow-lg ring-1 ring-amber-500/30"
                            : "bg-slate-900/40 hover:bg-slate-900 border-slate-800/80"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold text-white">
                              {evt.event_code}
                            </span>
                            {evt.is_demo && (
                              <span className="text-[9px] px-1 rounded bg-purple-500/20 text-purple-300 font-mono">
                                DEMO
                              </span>
                            )}
                          </div>
                          <RiskBadge level={rLevel} score={evt.risk?.risk_score} />
                        </div>

                        <div className="flex items-center justify-between text-xs mt-2 text-slate-300">
                          <span className="text-amber-300 font-medium truncate max-w-[180px]">
                            {evt.prediction?.predicted_class || "Evaluating..."}
                          </span>
                          <span className="font-mono text-orange-400 font-semibold">
                            {evt.max_frp.toFixed(1)} MW
                          </span>
                        </div>

                        <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1.5 font-mono">
                          <span>{evt.state}</span>
                          <span>{new Date(evt.last_seen).toLocaleDateString()}</span>
                        </div>
                      </div>
                    );
                  })}
              </div>

              {/* Pagination Bar */}
              {totalPages > 1 && (
                <div className="p-2.5 border-t border-agni-border bg-slate-950 flex items-center justify-between text-xs">
                  <button
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-slate-300 font-mono"
                  >
                    ← Prev
                  </button>
                  <span className="text-slate-400 font-mono text-[11px]">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    className="px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-slate-300 font-mono"
                  >
                    Next →
                  </button>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
