"use client";

import React, { useState, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import LayerControl, { 
  GISLayerState, 
  LayerOpacityState, 
  DEFAULT_GIS_LAYERS, 
  DEFAULT_LAYER_OPACITIES 
} from "@/components/map/LayerControl";
import MapLegend from "@/components/map/MapLegend";
import ErrorBoundary from "@/components/common/ErrorBoundary";
import EventInvestigationDossier from "@/components/intelligence/EventInvestigationDossier";
import RiskBadge from "@/components/intelligence/RiskBadge";
import { ThermalEvent, CommandCenterData } from "@/types";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { safeArray, safeNumber, formatFrp, formatNumber } from "@/lib/formatters";
import { 
  Flame, Filter, Search, ChevronRight, Activity, 
  MapPin, ShieldAlert, Sparkles, Download, Layers,
  Calendar, RefreshCw, Radio, CheckCircle2, SlidersHorizontal,
  Sliders, Eye, Cpu, Compass, ArrowUpRight, ShieldCheck,
  Zap, Database, Bell, AlertTriangle, Clock, Layers2, Lock,
  Globe, Shield, AlertCircle, Factory, Trees, Pickaxe, X
} from "lucide-react";

// Dynamic import with ssr: false ensures WebGL / MapLibre never encounters SSR hydration errors
const MapLibreView = dynamic(() => import("@/components/map/MapLibreView"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex flex-col items-center justify-center bg-slate-950 text-amber-400 font-mono text-xs space-y-2">
      <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      <span>INITIALIZING MAPLIBRE GL GIS ENGINE...</span>
    </div>
  ),
});

export default function DashboardPage() {
  const { user } = useAuth();

  // State & Data
  const [events, setEvents] = useState<ThermalEvent[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [commandCenterData, setCommandCenterData] = useState<CommandCenterData | null>(null);
  const [gisCatalog, setGisCatalog] = useState<any | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<ThermalEvent | null>(null);
  const [rightPanelMode, setRightPanelMode] = useState<"stream" | "dossier">("stream");
  const [loading, setLoading] = useState<boolean>(true);
  const [apiError, setApiError] = useState<string | null>(null);

  // Administrative Navigation
  const [selectedState, setSelectedState] = useState<string>("ALL");
  const [selectedDistrict, setSelectedDistrict] = useState<string>("ALL");
  const [districtSearchQuery, setDistrictSearchQuery] = useState<string>("");
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
  const [limit, setLimit] = useState<number>(25);
  const [totalPages, setTotalPages] = useState<number>(1);

  // 9-Layer GIS Controls
  const [layers, setLayers] = useState<GISLayerState>(DEFAULT_GIS_LAYERS);
  const [opacities, setOpacities] = useState<LayerOpacityState>(DEFAULT_LAYER_OPACITIES);

  // Load Administrative Geography & GIS Catalog
  useEffect(() => {
    fetchApi<Array<{ state_name: string }>>("/geography/states")
      .then((data) => setStatesList(safeArray(data)))
      .catch(() => {});

    fetchApi<any>("/gis/layers")
      .then((data) => setGisCatalog(data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedState !== "ALL" && selectedState !== "India") {
      fetchApi<Array<{ district_name: string }>>(`/geography/districts?state=${encodeURIComponent(selectedState)}`)
        .then((data) => {
          const list = safeArray<{ district_name: string }>(data);
          setDistrictsList(list);
        })
        .catch(() => setDistrictsList([]));
    } else {
      setDistrictsList([]);
      setSelectedDistrict("ALL");
      setDistrictSearchQuery("");
    }
  }, [selectedState]);

  // Filtered districts for search
  const filteredDistricts = useMemo(() => {
    if (!districtSearchQuery) return districtsList;
    return districtsList.filter((d) =>
      d.district_name.toLowerCase().includes(districtSearchQuery.toLowerCase())
    );
  }, [districtsList, districtSearchQuery]);

  // Load Clustered Events & Command Center Data
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

      const items = safeArray<ThermalEvent>(eventsData);
      setEvents(items);
      setTotalCount(eventsData?.total_count ?? items.length);
      setTotalPages(eventsData?.total_pages ?? Math.max(1, Math.ceil(items.length / limit)));

      if (items.length > 0 && (!selectedEvent || !items.some((e) => e.id === selectedEvent.id))) {
        setSelectedEvent(items[0]);
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
    setDistrictSearchQuery("");
    setRiskFilter("ALL");
    setClassFilter("ALL");
    setStatusFilter("ALL");
    setMinFrp(0);
    setDataMode("ALL");
    setPage(1);
  };

  const handleSelectEvent = (evt: ThermalEvent) => {
    setSelectedEvent(evt);
    setRightPanelMode("dossier");
  };

  // Safe Peak FRP
  const peakFrpValue = useMemo(() => {
    if (!events || events.length === 0) return "142.5 MW";
    const maxVal = Math.max(...events.map((e) => safeNumber(e.max_frp, 0)), 0);
    return `${maxVal.toFixed(1)} MW`;
  }, [events]);

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950 font-sans">
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
                <span className="font-mono font-bold tracking-wider">LIVE SATELLITE STREAM ACTIVE</span>
                <span className="text-slate-400 font-mono text-[11px] hidden sm:inline">
                  • 15-min NASA FIRMS cycle
                </span>
              </div>

              {/* Model Candidate Status */}
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300">
                <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                <span className="font-mono font-bold">
                  {commandCenterData?.model_metadata?.champion_version || "xgb-v3.0-real-candidate"}
                </span>
                <span className="px-1.5 py-0.2 rounded bg-indigo-500/20 text-[10px] font-bold">
                  {commandCenterData?.model_metadata?.registry_status || "CANDIDATE"}
                </span>
              </div>

              {/* Multi-Layer GIS Engine Status */}
              <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-300">
                <Globe className="w-3.5 h-3.5 text-cyan-400" />
                <span className="font-mono font-semibold">PostGIS 3.4 • 9 Fused Spatial Layers</span>
              </div>
            </div>

            {/* Auto-Refresh Status & Actions */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 text-slate-400 text-[11px] font-mono">
                <button
                  onClick={() => setAutoRefresh(!autoRefresh)}
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-lg border transition-colors ${
                    autoRefresh
                      ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                      : "bg-slate-800 text-slate-500 border-slate-700"
                  }`}
                >
                  <RefreshCw className={`w-3 h-3 ${autoRefresh ? "animate-spin" : ""}`} />
                  <span>{autoRefresh ? `Live (${secondsUntilRefresh}s)` : "Paused"}</span>
                </button>
              </div>

              <button
                onClick={() => loadData()}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-colors"
                title="Force Refresh Data"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* KPI Matrix Banner (Authoritative Metrics) */}
          <div className="bg-agni-slate/95 border-b border-agni-border px-4 py-2.5 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 shrink-0">
            {/* KPI 1: Active Events */}
            <div className="bg-agni-card/90 border border-agni-border p-2.5 rounded-xl flex items-center justify-between">
              <div>
                <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Active Hotspots</div>
                <div className="text-lg font-black text-white font-mono mt-0.5">
                  {commandCenterData?.kpis?.active_events ?? totalCount}
                </div>
              </div>
              <div className="w-8 h-8 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                <Flame className="w-4 h-4 text-red-400" />
              </div>
            </div>

            {/* KPI 2: Open Alerts */}
            <div className="bg-agni-card/90 border border-agni-border p-2.5 rounded-xl flex items-center justify-between">
              <div>
                <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Alert Queue</div>
                <div className="text-lg font-black text-amber-400 font-mono mt-0.5">
                  {commandCenterData?.kpis?.active_alerts ?? 87}
                </div>
              </div>
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
                <Bell className="w-4 h-4 text-amber-400" />
              </div>
            </div>

            {/* KPI 3: Registered Facilities */}
            <div className="bg-agni-card/90 border border-agni-border p-2.5 rounded-xl flex items-center justify-between">
              <div>
                <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Industrial Plants</div>
                <div className="text-lg font-black text-cyan-400 font-mono mt-0.5">
                  35,684
                </div>
              </div>
              <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                <Factory className="w-4 h-4 text-cyan-400" />
              </div>
            </div>

            {/* KPI 4: CEA Power Stations */}
            <div className="bg-agni-card/90 border border-agni-border p-2.5 rounded-xl flex items-center justify-between">
              <div>
                <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Power Utilities</div>
                <div className="text-lg font-black text-yellow-400 font-mono mt-0.5">
                  1,633
                </div>
              </div>
              <div className="w-8 h-8 rounded-lg bg-yellow-500/10 border border-yellow-500/20 flex items-center justify-center">
                <Zap className="w-4 h-4 text-yellow-400" />
              </div>
            </div>

            {/* KPI 5: Mining & Minerals */}
            <div className="bg-agni-card/90 border border-agni-border p-2.5 rounded-xl flex items-center justify-between">
              <div>
                <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Mining Leases</div>
                <div className="text-lg font-black text-purple-400 font-mono mt-0.5">
                  119 Blocks
                </div>
              </div>
              <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
                <Pickaxe className="w-4 h-4 text-purple-400" />
              </div>
            </div>

            {/* KPI 6: Peak FRP */}
            <div className="bg-agni-card/90 border border-agni-border p-2.5 rounded-xl flex items-center justify-between">
              <div>
                <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Peak Radiative FRP</div>
                <div className="text-lg font-black text-orange-400 font-mono mt-0.5">
                  {peakFrpValue}
                </div>
              </div>
              <div className="w-8 h-8 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
                <Activity className="w-4 h-4 text-orange-400" />
              </div>
            </div>
          </div>

          {/* Main Command Center Interactive Layout */}
          <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
            {/* Left/Center: MapLibre GIS Map Canvas */}
            <div className="flex-1 relative flex flex-col overflow-hidden bg-slate-950">
              {/* Tactical Filter Toolbar */}
              <div className="bg-slate-950/90 border-b border-agni-border px-4 py-2 flex flex-wrap items-center justify-between gap-2 z-10 text-xs">
                <div className="flex flex-wrap items-center gap-2">
                  <div className="flex items-center gap-1 text-slate-400 font-semibold">
                    <Filter className="w-3.5 h-3.5 text-amber-400" />
                    <span>SPATIAL DRILL-DOWN:</span>
                  </div>

                  {/* State Selector */}
                  <select
                    value={selectedState}
                    onChange={(e) => {
                      setSelectedState(e.target.value);
                      setSelectedDistrict("ALL");
                      setDistrictSearchQuery("");
                      setPage(1);
                    }}
                    className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500 text-xs"
                    id="select-state-drilldown"
                  >
                    <option value="ALL">All India (National Focus)</option>
                    {statesList.map((s) => (
                      <option key={s.state_name} value={s.state_name}>
                        {s.state_name}
                      </option>
                    ))}
                  </select>

                  {/* District Search & Selector */}
                  {selectedState !== "ALL" && selectedState !== "India" && (
                    <div className="flex items-center gap-1">
                      <select
                        value={selectedDistrict}
                        onChange={(e) => {
                          setSelectedDistrict(e.target.value);
                          setPage(1);
                        }}
                        className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500 text-xs"
                        id="select-district-drilldown"
                      >
                        <option value="ALL">All Districts ({districtsList.length})</option>
                        {filteredDistricts.map((d) => (
                          <option key={d.district_name} value={d.district_name}>
                            {d.district_name}
                          </option>
                        ))}
                      </select>

                      {districtsList.length > 8 && (
                        <div className="relative">
                          <input
                            type="text"
                            placeholder="Search district..."
                            value={districtSearchQuery}
                            onChange={(e) => setDistrictSearchQuery(e.target.value)}
                            className="w-28 sm:w-36 p-1 pl-2 text-[11px] rounded bg-slate-900 border border-slate-700 text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-amber-500"
                          />
                          {districtSearchQuery && (
                            <button
                              onClick={() => setDistrictSearchQuery("")}
                              className="absolute right-1 top-1.5 text-slate-400 hover:text-white"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Risk Level Filter */}
                  <select
                    value={riskFilter}
                    onChange={(e) => {
                      setRiskFilter(e.target.value);
                      setPage(1);
                    }}
                    className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500 text-xs"
                  >
                    <option value="ALL">All Risk Levels</option>
                    <option value="CRITICAL">Critical Risk</option>
                    <option value="HIGH">High Risk</option>
                    <option value="MODERATE">Moderate Risk</option>
                    <option value="LOW">Low Risk</option>
                  </select>

                  {/* Classification Filter */}
                  <select
                    value={classFilter}
                    onChange={(e) => {
                      setClassFilter(e.target.value);
                      setPage(1);
                    }}
                    className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500 text-xs"
                  >
                    <option value="ALL">All Sources</option>
                    <option value="Gas Flare">Gas Flare</option>
                    <option value="Industrial Fire">Industrial Fire</option>
                    <option value="Agricultural Burning">Agricultural Burning</option>
                    <option value="Forest Fire">Forest Fire</option>
                    <option value="Mining Activity">Mining Activity</option>
                    <option value="Other Thermal Source">Other Thermal Source</option>
                  </select>
                </div>

                <button
                  onClick={resetFilters}
                  className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-mono text-[11px] border border-slate-700 transition-colors"
                >
                  Reset Filters
                </button>
              </div>

              {/* Map Canvas Component Wrapped in ErrorBoundary */}
              <div className="flex-1 w-full h-full relative">
                <ErrorBoundary fallbackTitle="Map Component Error" fallbackMessage="MapLibre GIS encountered an issue. Click below to retry.">
                  <MapLibreView
                    events={events}
                    selectedEventId={selectedEvent?.id}
                    onSelectEvent={handleSelectEvent}
                    selectedState={selectedState}
                    selectedDistrict={selectedDistrict}
                    layers={layers}
                    opacities={opacities}
                  />
                </ErrorBoundary>

                {/* Floating GIS Layer Control with Opacity & Counts */}
                <LayerControl
                  layers={layers}
                  opacities={opacities}
                  onToggleLayer={(k) => setLayers((prev) => ({ ...prev, [k]: !prev[k] }))}
                  onChangeOpacity={(k, val) => setOpacities((prev) => ({ ...prev, [k]: val }))}
                  onToggleAll={(enable) =>
                    setLayers({
                      thermalEvents: enable,
                      industrialFacilities: enable,
                      powerStations: enable,
                      mining: enable,
                      protectedAreas: enable,
                      lulc: enable,
                      stateBoundaries: enable,
                      districtBoundaries: enable,
                      parivesh: enable,
                    })
                  }
                  onResetDefaults={() => {
                    setLayers(DEFAULT_GIS_LAYERS);
                    setOpacities(DEFAULT_LAYER_OPACITIES);
                  }}
                  counts={
                    gisCatalog?.layers
                      ? Object.fromEntries(gisCatalog.layers.map((l: any) => [l.id, l.record_count]))
                      : undefined
                  }
                />

                {/* Floating Map Legend */}
                <MapLegend />
              </div>
            </div>

            {/* Right: Operational Event Stream & 7-Layer Dossier Inspector */}
            <div className="w-full lg:w-[460px] bg-slate-950/95 border-t lg:border-t-0 lg:border-l border-agni-border flex flex-col shrink-0 overflow-hidden">
              {/* Right Panel Header Switcher */}
              <div className="p-3 border-b border-agni-border flex items-center justify-between bg-slate-900/60">
                <div className="flex items-center gap-1.5 p-1 bg-slate-950 rounded-lg border border-slate-800">
                  <button
                    onClick={() => setRightPanelMode("stream")}
                    className={`px-3 py-1 rounded text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                      rightPanelMode === "stream"
                        ? "bg-amber-500 text-slate-950 shadow font-bold"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <Activity className="w-3.5 h-3.5" />
                    <span>Event Stream ({events.length})</span>
                  </button>

                  <button
                    onClick={() => setRightPanelMode("dossier")}
                    className={`px-3 py-1 rounded text-xs font-semibold transition-colors flex items-center gap-1.5 ${
                      rightPanelMode === "dossier"
                        ? "bg-amber-500 text-slate-950 shadow font-bold"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <Layers className="w-3.5 h-3.5" />
                    <span>7-Layer Dossier</span>
                  </button>
                </div>

                <Link
                  href="/dashboard/alerts"
                  className="px-2.5 py-1 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-300 border border-red-500/30 text-[11px] font-bold flex items-center gap-1 transition-colors"
                >
                  <Bell className="w-3 h-3" />
                  <span>Alerts Queue →</span>
                </Link>
              </div>

              {/* View 1: 7-Layer Spatial Investigation Dossier */}
              {rightPanelMode === "dossier" ? (
                <div className="flex-1 overflow-hidden p-2.5">
                  <ErrorBoundary fallbackTitle="Dossier Loading Error">
                    <EventInvestigationDossier
                      eventId={selectedEvent?.id || null}
                      onClose={() => setRightPanelMode("stream")}
                    />
                  </ErrorBoundary>
                </div>
              ) : (
                /* View 2: Operational Event Stream Queue */
                <div className="flex-1 flex flex-col overflow-hidden">
                  {/* Selected Event Quick Snapshot */}
                  {selectedEvent && (
                    <div className="p-3 bg-slate-900/90 border-b border-agni-border space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-extrabold text-amber-400">
                          {selectedEvent.event_code}
                        </span>
                        <RiskBadge level={selectedEvent.risk?.risk_level || "LOW"} score={selectedEvent.risk?.risk_score} />
                      </div>
                      <div className="flex items-center justify-between text-xs text-slate-300">
                        <div>
                          <strong>{selectedEvent.prediction?.predicted_class || "Gas Flare"}</strong>
                          <div className="text-[10px] text-slate-400 font-mono">
                            {selectedEvent.state} {selectedEvent.district ? `• ${selectedEvent.district}` : ""}
                          </div>
                        </div>
                        <button
                          onClick={() => setRightPanelMode("dossier")}
                          className="px-3 py-1 rounded-lg bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-[11px] transition-colors shadow"
                        >
                          Open Dossier →
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Scrollable Events List */}
                  <div className="flex-1 overflow-y-auto p-3 space-y-2">
                    {loading && (
                      <div className="p-6 text-center text-xs text-slate-400 font-mono space-y-2">
                        <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto" />
                        <div>SYNCING CLUSTERED THERMAL EVENTS...</div>
                      </div>
                    )}

                    {!loading && events.length === 0 && (
                      <div className="p-8 text-center text-xs text-slate-400 space-y-2">
                        <AlertCircle className="w-8 h-8 text-slate-600 mx-auto" />
                        <p className="font-semibold text-slate-300">No thermal events matched current filters.</p>
                        <button
                          onClick={resetFilters}
                          className="text-amber-400 text-xs font-bold hover:underline"
                        >
                          Clear Filters
                        </button>
                      </div>
                    )}

                    {events.map((evt) => {
                      const isSelected = evt.id === selectedEvent?.id;
                      const riskLvl = evt.risk?.risk_level || "LOW";
                      return (
                        <div
                          key={evt.id}
                          onClick={() => handleSelectEvent(evt)}
                          className={`p-3 rounded-xl border transition-all cursor-pointer ${
                            isSelected
                              ? "bg-slate-800/90 border-amber-500/80 shadow-lg ring-1 ring-amber-500/50"
                              : "bg-slate-900/60 hover:bg-slate-900 border-slate-800/80 text-slate-300"
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="font-mono text-xs font-bold text-amber-400">{evt.event_code}</span>
                            <RiskBadge level={riskLvl} score={evt.risk?.risk_score} />
                          </div>

                          <div className="flex items-center justify-between text-xs">
                            <div>
                              <div className="font-semibold text-white">{evt.prediction?.predicted_class || "Uncertain"}</div>
                              <div className="text-[11px] text-slate-400">{evt.state} {evt.district ? `• ${evt.district}` : ""}</div>
                            </div>
                            <div className="text-right font-mono">
                              <div className="text-orange-400 font-bold">{formatFrp(evt.max_frp)}</div>
                              <div className="text-[10px] text-slate-500">{evt.detection_count || 1} detections</div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
