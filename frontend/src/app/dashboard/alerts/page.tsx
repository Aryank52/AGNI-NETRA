"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import RiskBadge from "@/components/intelligence/RiskBadge";
import { Alert } from "@/types";
import { fetchApi } from "@/lib/api";
import { 
  Bell, ShieldAlert, CheckCircle2, AlertTriangle, 
  RefreshCw, CheckSquare, Clock, Filter, SlidersHorizontal,
  Send, ExternalLink
} from "lucide-react";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [levelFilter, setLevelFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (levelFilter !== "ALL") params.append("alert_level", levelFilter);
      if (statusFilter !== "ALL") params.append("status_filter", statusFilter);

      const data = await fetchApi<Alert[]>(`/alerts?${params.toString()}`);
      setAlerts(data || []);
    } catch (err) {
      console.warn("Failed to load alerts:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [levelFilter, statusFilter]);

  const handleUpdateStatus = async (alertId: string, newStatus: string) => {
    setUpdatingId(alertId);
    try {
      await fetchApi(`/alerts/${alertId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: newStatus }),
      });
      await loadAlerts();
    } catch (err) {
      alert("Failed to update alert: " + err);
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-agni-border pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/30 font-bold">
                  EMERGENCY DISPATCH PROTOCOL
                </span>
                <span className="text-xs text-slate-400">Automated Multi-Agency Warning System</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5 mt-1">
                <Bell className="w-6 h-6 text-red-400" />
                Incident Alerts & Dispatch Center
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Automated threshold breach alarms for industrial plant emergencies, flare-stack spikes, and forest canopy threats. Dispatched to NDRF, CPCB, and State Disaster Management Authorities.
              </p>
            </div>

            <button
              onClick={loadAlerts}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
              title="Refresh Alerts"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-red-400" : ""}`} />
            </button>
          </div>

          {/* Filter Bar */}
          <div className="p-4 rounded-2xl bg-agni-card border border-agni-border flex flex-wrap items-center gap-4 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-semibold">Alert Level:</span>
              <select
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
                className="p-2 rounded-xl bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
              >
                <option value="ALL">All Levels</option>
                <option value="CRITICAL">Critical Alerts</option>
                <option value="HIGH">High Priority</option>
                <option value="MODERATE">Moderate</option>
                <option value="INFO">Informational</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-semibold">Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="p-2 rounded-xl bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
              >
                <option value="ALL">All Statuses</option>
                <option value="NEW">New / Unacknowledged</option>
                <option value="ACKNOWLEDGED">Acknowledged</option>
                <option value="RESOLVED">Resolved</option>
              </select>
            </div>

            <span className="ml-auto font-mono text-slate-400">
              {alerts.length} Active Notifications
            </span>
          </div>

          {/* Alerts Feed List */}
          <div className="space-y-4">
            {alerts.length === 0 ? (
              <div className="p-12 text-center rounded-2xl bg-agni-card border border-agni-border space-y-2">
                <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
                <div className="text-sm font-bold text-white">No Active Alerts In Selected Filter</div>
                <p className="text-xs text-slate-400">All industrial thermal thresholds are within safe baseline parameters.</p>
              </div>
            ) : (
              alerts.map((alert) => {
                const isCrit = alert.alert_level === "CRITICAL";
                const isHigh = alert.alert_level === "HIGH";

                return (
                  <div
                    key={alert.id}
                    className={`p-5 rounded-2xl bg-agni-card border transition-all space-y-3 shadow-lg ${
                      isCrit
                        ? "border-red-500/40 hover:border-red-500/70"
                        : isHigh
                        ? "border-orange-500/40 hover:border-orange-500/70"
                        : "border-agni-border"
                    }`}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                      <div className="flex items-center gap-3">
                        <span className={`text-[10px] uppercase font-mono px-2.5 py-0.5 rounded font-bold ${
                          isCrit
                            ? "bg-red-500/20 text-red-300 border border-red-500/30 animate-pulse"
                            : isHigh
                            ? "bg-orange-500/20 text-orange-300 border border-orange-500/30"
                            : "bg-yellow-500/20 text-yellow-300 border border-yellow-500/30"
                        }`}>
                          {alert.alert_level} ALERT
                        </span>
                        <span className="text-xs font-bold text-white">{alert.title}</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                          alert.status === "NEW"
                            ? "bg-red-500/20 text-red-300 border border-red-500/30 font-bold"
                            : alert.status === "ACKNOWLEDGED"
                            ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                            : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                        }`}>
                          STATUS: {alert.status}
                        </span>
                      </div>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">
                      {alert.message}
                    </p>

                    <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800/80 text-xs">
                      <div className="flex items-center gap-4 text-slate-400 font-mono text-[11px]">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-slate-500" />
                          {new Date(alert.created_at).toLocaleString()}
                        </span>
                        <span>Dispatched via: <strong>SMS / Webhook / Dashboard</strong></span>
                      </div>

                      <div className="flex items-center gap-2">
                        {alert.event_id && (
                          <Link
                            href={`/dashboard/events/${alert.event_id}`}
                            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
                          >
                            Inspect Event Dossier
                          </Link>
                        )}
                        {alert.status === "NEW" && (
                          <button
                            disabled={updatingId === alert.id}
                            onClick={() => handleUpdateStatus(alert.id, "ACKNOWLEDGED")}
                            className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs shadow-sm"
                          >
                            Acknowledge
                          </button>
                        )}
                        {alert.status !== "RESOLVED" && (
                          <button
                            disabled={updatingId === alert.id}
                            onClick={() => handleUpdateStatus(alert.id, "RESOLVED")}
                            className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-sm"
                          >
                            Resolve Alert
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
