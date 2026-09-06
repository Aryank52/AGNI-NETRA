"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import PageHeader from "@/components/common/PageHeader";
import EmptyState from "@/components/common/EmptyState";
import { CardSkeleton, MapLoadingSkeleton } from "@/components/common/Skeletons";
import { fetchApi } from "@/lib/api";
import { safeArray, safeNumber, formatFrp, formatNumber } from "@/lib/formatters";
import { ThermalEvent } from "@/types";
import { 
  ShieldAlert, Flame, Bell, MapPin, CheckCircle2, 
  AlertTriangle, Clock, Activity, Eye, Shield, 
  RefreshCw, Check, AlertOctagon, ArrowUpRight, 
  X, ChevronRight, PhoneCall, Radio, Send, ExternalLink
} from "lucide-react";

// Dynamic import for MapLibre (SSR disabled)
const MapLibreView = dynamic(() => import("@/components/map/MapLibreView"), {
  ssr: false,
  loading: () => <MapLoadingSkeleton />,
});

// Emergency Response specific layer visibility (prioritizes thermal events, critical assets, settlements)
const AGENCY_RESPONSE_LAYERS = {
  thermalEvents: true,
  industrialFacilities: true,
  powerStations: true,
  mining: false,
  protectedAreas: true,
  lulc: false,
  stateBoundaries: true,
  districtBoundaries: true,
  parivesh: false,
};

interface AlertItem {
  alert_id: string;
  event_id: string;
  alert_level: string;
  alert_type: string;
  title: string;
  status: string;
  routing_tier?: string;
  priority_score?: number;
  predicted_class?: string;
  confidence?: number;
  risk_score?: number;
  created_at: string;
  updated_at?: string;
  state?: string;
  district?: string;
  max_frp?: number;
  detection_count?: number;
  event_code?: string;
}

export default function AgencyPortalPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [events, setEvents] = useState<ThermalEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  
  // Selection and Map Focus
  const [selectedIncident, setSelectedIncident] = useState<ThermalEvent | null>(null);
  const [targetCoords, setTargetCoords] = useState<{ lat: number; lon: number; zoom?: number } | null>(null);
  const [alertFilter, setAlertFilter] = useState<string>("ALL");
  const [queueSeverityFilter, setQueueSeverityFilter] = useState<string>("ALL");

  // Load operational data from backend
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [alertsRes, eventsRes] = await Promise.all([
        fetchApi<any>("/alerts?limit=50&sort_by=priority").catch(() => ({ alerts: [] })),
        fetchApi<any>("/events?limit=100").catch(() => []),
      ]);

      if (alertsRes && Array.isArray(alertsRes.alerts)) {
        setAlerts(alertsRes.alerts);
      } else if (Array.isArray(alertsRes)) {
        setAlerts(alertsRes);
      }

      if (Array.isArray(eventsRes)) {
        setEvents(eventsRes);
      } else if (eventsRes && Array.isArray(eventsRes.events)) {
        setEvents(eventsRes.events);
      }
    } catch (err) {
      console.warn("Failed to load agency operations data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Operational Alert Action Handlers (Real Backend Endpoints)
  const handleAcknowledge = async (alertId: string) => {
    setActionLoading(alertId);
    try {
      await fetchApi(`/alerts/${alertId}/acknowledge`, {
        method: "POST",
        body: JSON.stringify({ notes: "Acknowledged by Emergency Response Center operator" }),
      });
      setAlerts((prev) =>
        prev.map((a) => (a.alert_id === alertId ? { ...a, status: "ACKNOWLEDGED" } : a))
      );
      setActionSuccess(`Alert acknowledged`);
      setTimeout(() => setActionSuccess(null), 3500);
    } catch (err: any) {
      alert(`Failed to acknowledge alert: ${err.message || err}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleStartInvestigation = async (alertId: string) => {
    setActionLoading(alertId);
    try {
      await fetchApi(`/alerts/${alertId}/start-investigation`, {
        method: "POST",
        body: JSON.stringify({ notes: "Tactical response investigation initiated by Agency operations" }),
      });
      setAlerts((prev) =>
        prev.map((a) => (a.alert_id === alertId ? { ...a, status: "UNDER_INVESTIGATION" } : a))
      );
      setActionSuccess(`Investigation initiated`);
      setTimeout(() => setActionSuccess(null), 3500);
    } catch (err: any) {
      alert(`Failed to start investigation: ${err.message || err}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleVerifyAlert = async (alertId: string, groundTruth: string = "Industrial Fire") => {
    setActionLoading(alertId);
    try {
      await fetchApi(`/alerts/${alertId}/verify`, {
        method: "POST",
        body: JSON.stringify({
          verification_outcome: "CONFIRM",
          ground_truth_class: groundTruth,
          confidence: 1.0,
          notes: "Confirmed by State Disaster Operations Center field telemetry",
        }),
      });
      setAlerts((prev) =>
        prev.map((a) => (a.alert_id === alertId ? { ...a, status: "VERIFIED" } : a))
      );
      setActionSuccess(`Incident verified and confirmed`);
      setTimeout(() => setActionSuccess(null), 3500);
    } catch (err: any) {
      alert(`Failed to verify alert: ${err.message || err}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Find linked event for an alert or focus map on it
  const focusOnIncident = (eventCodeOrId: string, lat?: number, lon?: number) => {
    const matched = events.find(
      (e) => e.id === eventCodeOrId || e.event_code === eventCodeOrId
    );

    if (matched) {
      setSelectedIncident(matched);
      setTargetCoords({ lat: matched.latitude, lon: matched.longitude, zoom: 12.5 });
    } else if (lat && lon) {
      setTargetCoords({ lat, lon, zoom: 12.5 });
    }
  };

  // Top Metrics Calculations
  const criticalIncidentsCount = useMemo(() => {
    return alerts.filter(
      (a) => (a.alert_level || "").toUpperCase() === "CRITICAL" || (a.risk_score || 0) >= 70
    ).length;
  }, [alerts]);

  const highPriorityAlertsCount = useMemo(() => {
    return alerts.filter((a) => {
      const lvl = (a.alert_level || "").toUpperCase();
      return lvl === "CRITICAL" || lvl === "HIGH";
    }).length;
  }, [alerts]);

  const responseRequiredCount = useMemo(() => {
    return alerts.filter((a) => a.status === "NEW" || a.status === "ACKNOWLEDGED").length;
  }, [alerts]);

  const recentlyVerifiedCount = useMemo(() => {
    return alerts.filter((a) => a.status === "VERIFIED" || a.status === "RESOLVED").length;
  }, [alerts]);

  // Filtered Alerts for Right Panel
  const filteredAlerts = useMemo(() => {
    return alerts.filter((a) => {
      if (alertFilter === "ALL") return true;
      if (alertFilter === "CRITICAL") return (a.alert_level || "").toUpperCase() === "CRITICAL";
      if (alertFilter === "RESPONSE_REQUIRED") return a.status === "NEW" || a.status === "ACKNOWLEDGED";
      if (alertFilter === "INVESTIGATING") return a.status === "UNDER_INVESTIGATION";
      return true;
    });
  }, [alerts, alertFilter]);

  // Response Queue Sorted by Severity (CRITICAL -> HIGH -> MODERATE -> LOW)
  const sortedQueue = useMemo(() => {
    const severityRank: Record<string, number> = {
      CRITICAL: 4,
      HIGH: 3,
      MEDIUM: 2,
      MODERATE: 2,
      LOW: 1,
    };

    let filtered = [...events];
    if (queueSeverityFilter !== "ALL") {
      filtered = filtered.filter((evt) => {
        const lvl = (evt.risk?.risk_level || "LOW").toUpperCase();
        return lvl === queueSeverityFilter;
      });
    }

    return filtered.sort((a, b) => {
      const rankA = severityRank[(a.risk?.risk_level || "LOW").toUpperCase()] || 1;
      const rankB = severityRank[(b.risk?.risk_level || "LOW").toUpperCase()] || 1;
      if (rankB !== rankA) return rankB - rankA;
      // Secondary: Risk Score
      const riskA = a.risk?.risk_score || 0;
      const riskB = b.risk?.risk_score || 0;
      if (riskB !== riskA) return riskB - riskA;
      // Tertiary: Max FRP
      return (b.max_frp || 0) - (a.max_frp || 0);
    });
  }, [events, queueSeverityFilter]);

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950 font-sans">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Operational Page Header */}
          <PageHeader
            category="EMERGENCY OPERATIONS COMMAND"
            title="Agency Rapid Response & Incident Operations Center"
            description="Operational command workstation for NDMA, SDMAs, and Quick Response Teams. Real-time alert triage, incident containment, and immediate response dispatch gating."
            icon={<ShieldAlert className="w-6 h-6 text-red-400" />}
            actions={
              <div className="flex items-center gap-2">
                <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 text-red-400 border border-red-500/30 text-xs font-mono font-bold">
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                  <span>LEVEL 1 ESCALATION PROTOCOL</span>
                </span>
                <button
                  onClick={loadData}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                  title="Refresh Operational Telemetry"
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-red-400" : ""}`} />
                </button>
              </div>
            }
          />

          {/* Action Feedback Toast */}
          {actionSuccess && (
            <div className="p-3 rounded-xl bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 text-xs flex items-center justify-between animate-in fade-in slide-in-from-top-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="font-semibold">{actionSuccess}</span>
              </div>
              <button onClick={() => setActionSuccess(null)} className="text-emerald-400 hover:text-white">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* TOP SUMMARY STATS STRIP */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
            <div className="p-4 rounded-xl bg-red-950/20 border border-red-500/30 space-y-1">
              <div className="text-[10px] text-red-400 font-mono font-bold uppercase flex items-center gap-1.5">
                <AlertOctagon className="w-3.5 h-3.5" />
                <span>Critical Incidents</span>
              </div>
              <div className="text-2xl font-extrabold text-white font-mono">
                {criticalIncidentsCount}
              </div>
              <p className="text-[10px] text-slate-400">Exceeding 70 Risk or Tier 1</p>
            </div>

            <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/30 space-y-1">
              <div className="text-[10px] text-amber-400 font-mono font-bold uppercase flex items-center gap-1.5">
                <Bell className="w-3.5 h-3.5" />
                <span>High-Priority Alerts</span>
              </div>
              <div className="text-2xl font-extrabold text-amber-400 font-mono">
                {highPriorityAlertsCount}
              </div>
              <p className="text-[10px] text-slate-400">Critical + High priority</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-agni-border space-y-1">
              <div className="text-[10px] text-orange-400 font-mono font-bold uppercase flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5" />
                <span>Response Required</span>
              </div>
              <div className="text-2xl font-extrabold text-orange-400 font-mono">
                {responseRequiredCount}
              </div>
              <p className="text-[10px] text-slate-400">Unacknowledged or pending</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-agni-border space-y-1">
              <div className="text-[10px] text-emerald-400 font-mono font-bold uppercase flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Recently Verified</span>
              </div>
              <div className="text-2xl font-extrabold text-emerald-400 font-mono">
                {recentlyVerifiedCount}
              </div>
              <p className="text-[10px] text-slate-400">Confirmed by field telemetry</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-agni-border space-y-1 col-span-2 lg:col-span-1">
              <div className="text-[10px] text-cyan-400 font-mono font-bold uppercase flex items-center gap-1.5">
                <Radio className="w-3.5 h-3.5" />
                <span>Regional Status</span>
              </div>
              <div className="text-2xl font-extrabold text-white font-mono">
                Active
              </div>
              <p className="text-[10px] text-slate-400">36 States under live sweep</p>
            </div>
          </div>

          {/* MAIN OPERATIONAL GRID (LEFT: MAP, RIGHT: ALERTS) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* LEFT / MAIN: Large Operational Map (7 cols on lg) */}
            <div className="lg:col-span-7 flex flex-col space-y-2">
              <div className="flex items-center justify-between bg-agni-card px-4 py-2.5 rounded-t-xl border border-agni-border">
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-red-400" />
                  <span className="text-xs font-bold text-white uppercase tracking-wider">
                    Operational Tactical Map
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                    <span>Thermal Incident</span>
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                    <span>Critical Asset</span>
                  </span>
                </div>
              </div>

              <div className="h-[460px] sm:h-[520px] rounded-b-xl overflow-hidden border border-agni-border relative">
                <MapLibreView 
                  events={events}
                  layers={AGENCY_RESPONSE_LAYERS}
                  targetCoordinates={targetCoords}
                  onSelectEvent={(evt) => setSelectedIncident(evt)}
                  selectedState="India"
                />
              </div>

              <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                <span>* Map layers prioritized for emergency response: Thermal hotspots, industrial assets, power plants, protected reserves.</span>
                <span className="font-mono text-slate-500 shrink-0">GIS Gated</span>
              </div>
            </div>

            {/* RIGHT PANEL: Active Response Alerts (5 cols on lg) */}
            <div className="lg:col-span-5 flex flex-col space-y-3">
              <div className="p-3.5 rounded-xl bg-agni-card border border-agni-border space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-red-400" />
                    <h2 className="text-xs font-bold uppercase tracking-wider text-white">
                      Active Response Alerts
                    </h2>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-bold">
                    {filteredAlerts.length} Active
                  </span>
                </div>

                {/* Filter Tabs */}
                <div className="grid grid-cols-4 gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-[10px] font-mono">
                  {[
                    { id: "ALL", label: "All" },
                    { id: "CRITICAL", label: "Critical" },
                    { id: "RESPONSE_REQUIRED", label: "Pending" },
                    { id: "INVESTIGATING", label: "Investigating" },
                  ].map((f) => (
                    <button
                      key={f.id}
                      onClick={() => setAlertFilter(f.id)}
                      className={`py-1 rounded text-center font-semibold transition-all ${
                        alertFilter === f.id
                          ? "bg-amber-500 text-slate-950 font-bold shadow"
                          : "text-slate-400 hover:text-white"
                      }`}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Scrollable Alerts Feed */}
              <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
                {loading ? (
                  <div className="space-y-3">
                    <CardSkeleton />
                    <CardSkeleton />
                  </div>
                ) : filteredAlerts.length === 0 ? (
                  <div className="p-8 rounded-xl bg-agni-card border border-agni-border text-center space-y-2">
                    <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
                    <div className="text-xs font-bold text-white">All Clear in Active Filter</div>
                    <p className="text-[11px] text-slate-400">
                      No active alerts require immediate action under this filter criterion.
                    </p>
                  </div>
                ) : (
                  filteredAlerts.map((alert) => {
                    const level = (alert.alert_level || "MEDIUM").toUpperCase();
                    const isCritical = level === "CRITICAL";
                    const isNew = alert.status === "NEW";
                    const isInvestigating = alert.status === "UNDER_INVESTIGATION";

                    return (
                      <div
                        key={alert.alert_id}
                        className={`p-4 rounded-xl bg-agni-card border transition-all space-y-3 ${
                          isCritical
                            ? "border-red-500/50 shadow-md shadow-red-950/20"
                            : "border-agni-border hover:border-amber-500/40"
                        }`}
                      >
                        {/* Alert Top Strip */}
                        <div className="flex items-start justify-between gap-2 border-b border-slate-800/80 pb-2">
                          <div className="space-y-0.5">
                            <div className="flex items-center gap-1.5">
                              <span className={`text-[9px] font-mono font-bold uppercase px-2 py-0.5 rounded border ${
                                isCritical
                                  ? "bg-red-500/20 text-red-300 border-red-500/40 animate-pulse"
                                  : "bg-amber-500/20 text-amber-300 border-amber-500/40"
                              }`}>
                                {level}
                              </span>
                              <span className="text-[10px] font-mono text-slate-400">
                                {alert.event_code || "INCIDENT"}
                              </span>
                            </div>
                            <div className="text-xs font-bold text-white leading-snug">
                              {alert.title}
                            </div>
                          </div>

                          <span className={`text-[9px] font-mono px-2 py-0.5 rounded font-bold uppercase shrink-0 border ${
                            alert.status === "VERIFIED"
                              ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                              : alert.status === "UNDER_INVESTIGATION"
                              ? "bg-blue-500/20 text-blue-300 border-blue-500/30"
                              : isNew
                              ? "bg-red-500/20 text-red-300 border-red-500/30"
                              : "bg-slate-800 text-slate-300 border-slate-700"
                          }`}>
                            {alert.status}
                          </span>
                        </div>

                        {/* Alert Attributes Grid */}
                        <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                          <div className="flex items-center gap-1 text-slate-300">
                            <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                            <span className="truncate">{alert.district || "District"}, {alert.state || "State"}</span>
                          </div>
                          <div className="flex items-center justify-end gap-1 text-slate-300">
                            <Flame className="w-3.5 h-3.5 text-orange-400 shrink-0" />
                            <span>{formatFrp(alert.max_frp || 0)}</span>
                          </div>
                          <div className="flex items-center gap-1 text-slate-400">
                            <Activity className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                            <span>Risk: <strong className="text-white">{alert.risk_score || 0}/100</strong></span>
                          </div>
                          <div className="flex items-center justify-end gap-1 text-slate-400">
                            <Clock className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                            <span>{new Date(alert.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}</span>
                          </div>
                        </div>

                        {/* Operational Action Buttons (Backed by Real API) */}
                        <div className="flex items-center gap-2 pt-1 border-t border-slate-800/80">
                          {isNew && (
                            <button
                              onClick={() => handleAcknowledge(alert.alert_id)}
                              disabled={actionLoading === alert.alert_id}
                              className="flex-1 py-1.5 px-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-colors flex items-center justify-center gap-1"
                            >
                              <Check className="w-3.5 h-3.5" />
                              <span>Acknowledge</span>
                            </button>
                          )}

                          {(isNew || alert.status === "ACKNOWLEDGED") && (
                            <button
                              onClick={() => handleStartInvestigation(alert.alert_id)}
                              disabled={actionLoading === alert.alert_id}
                              className="flex-1 py-1.5 px-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-colors flex items-center justify-center gap-1"
                            >
                              <Radio className="w-3.5 h-3.5" />
                              <span>Investigate</span>
                            </button>
                          )}

                          {isInvestigating && (
                            <button
                              onClick={() => handleVerifyAlert(alert.alert_id)}
                              disabled={actionLoading === alert.alert_id}
                              className="flex-1 py-1.5 px-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-colors flex items-center justify-center gap-1"
                            >
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>Confirm / Verify</span>
                            </button>
                          )}

                          <button
                            onClick={() => focusOnIncident(alert.event_id || alert.event_code || "")}
                            className="py-1.5 px-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors border border-slate-700 flex items-center gap-1 shrink-0"
                            title="Inspect details & center on map"
                          >
                            <Eye className="w-3.5 h-3.5 text-cyan-400" />
                            <span>Inspect</span>
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          {/* BOTTOM SECTION: PRIORITY RESPONSE QUEUE */}
          <div className="p-5 rounded-2xl bg-agni-card border border-agni-border space-y-4 shadow-xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Flame className="w-5 h-5 text-red-400" />
                <div>
                  <h2 className="text-sm font-bold uppercase tracking-wider text-white">
                    Priority Incident Response Queue
                  </h2>
                  <p className="text-xs text-slate-400">
                    Incidents sorted strictly by priority & severity (Critical → High → Moderate → Low)
                  </p>
                </div>
              </div>

              {/* Severity Filter */}
              <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs font-mono">
                {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((sev) => (
                  <button
                    key={sev}
                    onClick={() => setQueueSeverityFilter(sev)}
                    className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-all ${
                      queueSeverityFilter === sev
                        ? "bg-amber-500 text-slate-950 font-bold"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {sev}
                  </button>
                ))}
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-mono text-[10px] uppercase tracking-wider">
                    <th className="py-2.5 px-3">Priority / Level</th>
                    <th className="py-2.5 px-3">Incident ID</th>
                    <th className="py-2.5 px-3">Location</th>
                    <th className="py-2.5 px-3">Radiative Power</th>
                    <th className="py-2.5 px-3">Hazard Nature</th>
                    <th className="py-2.5 px-3">Risk Rating</th>
                    <th className="py-2.5 px-3">Exposure Proximity</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {loading ? (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-slate-500">
                        Loading operational incident queue...
                      </td>
                    </tr>
                  ) : sortedQueue.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-slate-500">
                        No incidents match current filter.
                      </td>
                    </tr>
                  ) : (
                    sortedQueue.slice(0, 15).map((evt) => {
                      const level = (evt.risk?.risk_level || "LOW").toUpperCase();
                      const isCritical = level === "CRITICAL";
                      const isHigh = level === "HIGH";

                      return (
                        <tr
                          key={evt.id}
                          className="hover:bg-slate-800/50 transition-colors group cursor-pointer"
                          onClick={() => focusOnIncident(evt.id, evt.latitude, evt.longitude)}
                        >
                          <td className="py-3 px-3">
                            <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase border ${
                              isCritical
                                ? "bg-red-500/20 text-red-300 border-red-500/40 animate-pulse"
                                : isHigh
                                ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                                : "bg-slate-800 text-slate-300 border-slate-700"
                            }`}>
                              {level}
                            </span>
                          </td>
                          <td className="py-3 px-3 font-bold text-white">
                            {evt.event_code || evt.id.slice(0, 8)}
                          </td>
                          <td className="py-3 px-3 text-slate-300 font-sans">
                            {evt.district || "District"}, {evt.state || "State"}
                          </td>
                          <td className="py-3 px-3 font-bold text-orange-400">
                            {formatFrp(evt.max_frp || 0)}
                          </td>
                          <td className="py-3 px-3 text-slate-300 font-sans">
                            {evt.prediction?.predicted_class || evt.landcover_class || "Thermal Source"}
                          </td>
                          <td className="py-3 px-3">
                            <span className="font-bold text-white">{evt.risk?.risk_score || 0}</span>
                            <span className="text-slate-500">/100</span>
                          </td>
                          <td className="py-3 px-3 text-slate-400 text-[11px]">
                            {evt.features?.dist_to_settlement_m
                              ? `${Math.round(evt.features.dist_to_settlement_m / 1000)} km to Settlement`
                              : `${Math.round(evt.nearest_facility_distance_m || 0)} m to Facility`}
                          </td>
                          <td className="py-3 px-3 text-right" onClick={(e) => e.stopPropagation()}>
                            <button
                              onClick={() => focusOnIncident(evt.id, evt.latitude, evt.longitude)}
                              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-semibold transition-colors inline-flex items-center gap-1"
                            >
                              <span>Inspect</span>
                              <ChevronRight className="w-3.5 h-3.5" />
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* QUICK RESPONSE INCIDENT DRAWER / MODAL */}
          {selectedIncident && (
            <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in">
              <div className="bg-agni-card border border-agni-border rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto">
                {/* Modal Header */}
                <div className="flex items-start justify-between border-b border-slate-800 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className={`text-[9px] font-mono font-bold uppercase px-2 py-0.5 rounded border ${
                        (selectedIncident.risk?.risk_level || "").toUpperCase() === "CRITICAL"
                          ? "bg-red-500/20 text-red-300 border-red-500/40"
                          : "bg-amber-500/20 text-amber-300 border-amber-500/40"
                      }`}>
                        {(selectedIncident.risk?.risk_level || "MEDIUM").toUpperCase()} SEVERITY
                      </span>
                      <span className="text-xs font-mono text-slate-400 font-bold">
                        {selectedIncident.event_code || selectedIncident.id}
                      </span>
                    </div>
                    <h3 className="text-base font-bold text-white mt-1">
                      {selectedIncident.prediction?.predicted_class || "Thermal Incident"} in {selectedIncident.district}, {selectedIncident.state}
                    </h3>
                  </div>

                  <button
                    onClick={() => setSelectedIncident(null)}
                    className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Incident Coordinates & Map Trigger */}
                <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2 text-slate-300">
                    <MapPin className="w-4 h-4 text-red-400 shrink-0" />
                    <span>Lat: {selectedIncident.latitude.toFixed(4)}, Lon: {selectedIncident.longitude.toFixed(4)}</span>
                  </div>
                  <button
                    onClick={() => {
                      setTargetCoords({ lat: selectedIncident.latitude, lon: selectedIncident.longitude, zoom: 13.5 });
                      setSelectedIncident(null);
                    }}
                    className="text-cyan-400 hover:underline flex items-center gap-1 font-semibold"
                  >
                    <span>Center on Map</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Operational Summary */}
                <div className="space-y-1.5">
                  <div className="text-xs font-bold text-slate-300 uppercase tracking-wide">
                    Operational Situation Summary:
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                    {selectedIncident.risk?.risk_reasons?.[0] || 
                      `Elevated thermal anomaly observed with peak radiative intensity of ${formatFrp(selectedIncident.max_frp || 0)}. Nearest industrial asset located at ${Math.round(selectedIncident.nearest_facility_distance_m || 0)}m distance.`
                    }
                  </p>
                </div>

                {/* Risk & Exposure Attributes */}
                <div className="grid grid-cols-3 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                    <div className="text-[10px] text-slate-400 uppercase font-mono">Overall Risk</div>
                    <div className="text-lg font-bold text-red-400 font-mono">
                      {selectedIncident.risk?.risk_score || 0}/100
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                    <div className="text-[10px] text-slate-400 uppercase font-mono">Peak Intensity</div>
                    <div className="text-lg font-bold text-orange-400 font-mono">
                      {formatFrp(selectedIncident.max_frp || 0)}
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                    <div className="text-[10px] text-slate-400 uppercase font-mono">Settlement Exposure</div>
                    <div className="text-lg font-bold text-white font-mono">
                      {selectedIncident.features?.dist_to_settlement_m 
                        ? `${Math.round(selectedIncident.features.dist_to_settlement_m / 1000)} km`
                        : "Non-proximate"}
                    </div>
                  </div>
                </div>

                {/* Statutory Operational Response Guidance */}
                <div className="p-3.5 rounded-xl bg-red-950/20 border border-red-500/30 space-y-1.5 text-xs text-slate-300">
                  <div className="font-bold text-red-400 flex items-center gap-1.5">
                    <Shield className="w-4 h-4" />
                    <span>Statutory Dispatch Protocol:</span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    Under National Disaster Management Authority operational doctrine, automated live dispatch is gated. Response teams must acknowledge and confirm incident telemetry via state-authorized protocols prior to field deployment.
                  </p>
                </div>

                {/* Modal Footer Actions */}
                <div className="flex items-center justify-between pt-3 border-t border-slate-800">
                  <Link
                    href={`/dashboard/events/${selectedIncident.id}`}
                    className="text-xs text-slate-400 hover:text-white flex items-center gap-1 font-mono"
                  >
                    <span>Open Full Event Dossier</span>
                    <ExternalLink className="w-3 h-3" />
                  </Link>

                  <button
                    onClick={() => setSelectedIncident(null)}
                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition-colors"
                  >
                    Close Incident View
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
