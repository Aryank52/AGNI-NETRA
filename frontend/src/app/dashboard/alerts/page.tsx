"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import RiskBadge from "@/components/intelligence/RiskBadge";
import { Alert } from "@/types";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { formatNumber, formatPercent } from "@/lib/formatters";
import { 
  Bell, ShieldAlert, CheckCircle2, AlertTriangle, 
  RefreshCw, CheckSquare, Clock, Filter, SlidersHorizontal,
  Send, ExternalLink, Zap, Eye, HelpCircle, Lock,
  ChevronRight, ArrowUpRight, Search, Check, X, ArrowRight
} from "lucide-react";

export default function AlertsPage() {
  const { user } = useAuth();

  // State & Data
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [totalAlerts, setTotalAlerts] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [apiError, setApiError] = useState<string | null>(null);

  // Filter Tabs
  const [activeTierTab, setActiveTierTab] = useState<string>("ALL"); // ALL, TIER_1, TIER_2, TIER_3
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [levelFilter, setLevelFilter] = useState<string>("ALL");
  const [stateFilter, setStateFilter] = useState<string>("ALL");
  const [sortBy, setSortBy] = useState<string>("priority");

  // Action Modal State
  const [actionModalOpen, setActionModalOpen] = useState<boolean>(false);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [targetAction, setTargetAction] = useState<string>("");
  const [actionNotes, setActionNotes] = useState<string>("");
  const [groundTruthClass, setGroundTruthClass] = useState<string>("Agricultural Burning");
  const [verificationOutcome, setVerificationOutcome] = useState<string>("CONFIRM");
  const [actionSubmitting, setActionSubmitting] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadAlerts = async () => {
    setLoading(true);
    setApiError(null);
    try {
      const params = new URLSearchParams();
      if (activeTierTab !== "ALL") {
        if (activeTierTab === "TIER_1") params.append("routing_tier", "TIER_1_AUTO_DISPATCH_CANDIDATE");
        if (activeTierTab === "TIER_2") params.append("routing_tier", "TIER_2_ANALYST_REVIEW_QUEUE");
        if (activeTierTab === "TIER_3") params.append("routing_tier", "TIER_3_UNCERTAINTY_QUEUE");
      }
      if (statusFilter !== "ALL") params.append("status_filter", statusFilter);
      if (levelFilter !== "ALL") params.append("alert_level", levelFilter);
      if (stateFilter !== "ALL") params.append("state", stateFilter);
      params.append("sort_by", sortBy);
      params.append("limit", "50");

      const data = await fetchApi<any>(`/alerts?${params.toString()}`);
      if (data && data.alerts) {
        setAlerts(data.alerts);
        setTotalAlerts(data.total_alerts || data.alerts.length);
      } else if (Array.isArray(data)) {
        setAlerts(data);
        setTotalAlerts(data.length);
      }
    } catch (err: any) {
      setApiError(err?.message || "Failed to load operational alerts.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [activeTierTab, statusFilter, levelFilter, stateFilter, sortBy]);

  const openActionModal = (alertObj: Alert, action: string) => {
    setSelectedAlert(alertObj);
    setTargetAction(action);
    setActionNotes("");
    setGroundTruthClass(alertObj.predicted_class || "Agricultural Burning");
    setVerificationOutcome("CONFIRM");
    setActionMessage(null);
    setActionModalOpen(true);
  };

  const handleExecuteAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAlert || !targetAction) return;

    setActionSubmitting(true);
    setActionMessage(null);
    try {
      let endpoint = "";
      let bodyData: any = {
        analyst_id: user?.id,
        analyst_name: user?.full_name || "Thermal Analyst",
        notes: actionNotes || `Executed ${targetAction} via Command Center Alert Center`
      };

      if (targetAction === "ACKNOWLEDGE") {
        endpoint = `/alerts/${selectedAlert.id}/acknowledge`;
      } else if (targetAction === "START_INVESTIGATION") {
        endpoint = `/alerts/${selectedAlert.id}/investigate`;
      } else if (targetAction === "VERIFY") {
        endpoint = `/alerts/${selectedAlert.id}/verify`;
        bodyData.ground_truth_class = groundTruthClass;
        bodyData.verification_outcome = verificationOutcome;
      } else if (targetAction === "ESCALATE") {
        endpoint = `/alerts/${selectedAlert.id}/escalate`;
        bodyData.escalation_reason = actionNotes;
      } else if (targetAction === "DISMISS") {
        endpoint = `/alerts/${selectedAlert.id}/dismiss`;
        bodyData.dismissal_reason = actionNotes;
      } else if (targetAction === "CLOSE") {
        endpoint = `/alerts/${selectedAlert.id}/close`;
        bodyData.closing_summary = actionNotes;
      }

      await fetchApi(endpoint, {
        method: "POST",
        body: JSON.stringify(bodyData)
      });

      setActionMessage("Action recorded in audit log.");
      setTimeout(() => {
        setActionModalOpen(false);
        loadAlerts();
      }, 700);
    } catch (err: any) {
      setActionMessage(`Error: ${err?.message || "Action failed"}`);
    } finally {
      setActionSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-7xl mx-auto">
          {/* Header Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-agni-border pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/30 font-bold">
                  TRI-TIER OPERATIONAL ALERT SYSTEM
                </span>
                <span className="text-xs text-slate-400">Human-in-the-Loop Decision Center</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5 mt-1">
                <Bell className="w-6 h-6 text-red-400" />
                Operational Alert Center & Decision Queue
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Point-in-time calibrated thermal alerts routed through strict confidence & risk tiers. Safe automated dispatch gating with immutable analyst audit trails.
              </p>
            </div>

            {/* Zero Dispatch Gating Tag */}
            <div className="flex items-center gap-3">
              <div className="px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 flex items-center gap-2 text-xs">
                <Lock className="w-4 h-4 text-amber-400" />
                <div>
                  <div className="font-mono font-bold leading-none">DISPATCH GATE: SAFE</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">0 Automated Alerts Dispatched</div>
                </div>
              </div>

              <button
                onClick={loadAlerts}
                className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                title="Refresh Alerts"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-amber-400" : ""}`} />
              </button>
            </div>
          </div>

          {/* Tri-Tier Queue Navigation Tabs */}
          <div className="flex flex-wrap items-center gap-2 border-b border-agni-border pb-2">
            <button
              onClick={() => setActiveTierTab("ALL")}
              className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition-all flex items-center gap-2 ${
                activeTierTab === "ALL"
                  ? "bg-amber-500 text-slate-950 shadow-md"
                  : "bg-slate-900/60 hover:bg-slate-800 text-slate-300 border border-slate-800"
              }`}
            >
              <span>All Alerts</span>
              <span className="px-1.5 py-0.2 rounded-full bg-slate-950/30 text-[10px]">
                {totalAlerts}
              </span>
            </button>

            <button
              onClick={() => setActiveTierTab("TIER_1")}
              className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition-all flex items-center gap-2 ${
                activeTierTab === "TIER_1"
                  ? "bg-purple-500 text-white shadow-md"
                  : "bg-slate-900/60 hover:bg-slate-800 text-slate-300 border border-slate-800"
              }`}
            >
              <Zap className="w-3.5 h-3.5 text-purple-300" />
              <span>Tier 1: Auto-Dispatch Candidates</span>
              <span className="text-[10px] text-purple-200">(&ge;65% Conf)</span>
            </button>

            <button
              onClick={() => setActiveTierTab("TIER_2")}
              className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition-all flex items-center gap-2 ${
                activeTierTab === "TIER_2"
                  ? "bg-blue-500 text-white shadow-md"
                  : "bg-slate-900/60 hover:bg-slate-800 text-slate-300 border border-slate-800"
              }`}
            >
              <Eye className="w-3.5 h-3.5 text-blue-300" />
              <span>Tier 2: Analyst Review Queue</span>
              <span className="text-[10px] text-blue-200">(45-65% Conf)</span>
            </button>

            <button
              onClick={() => setActiveTierTab("TIER_3")}
              className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition-all flex items-center gap-2 ${
                activeTierTab === "TIER_3"
                  ? "bg-emerald-600 text-white shadow-md"
                  : "bg-slate-900/60 hover:bg-slate-800 text-slate-300 border border-slate-800"
              }`}
            >
              <HelpCircle className="w-3.5 h-3.5 text-emerald-300" />
              <span>Tier 3: Uncertainty Queue</span>
              <span className="text-[10px] text-emerald-200">(&lt;45% Conf)</span>
            </button>
          </div>

          {/* Multi-Criteria Filter Toolbar */}
          <div className="p-3.5 rounded-2xl bg-agni-card border border-agni-border flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex flex-wrap items-center gap-3">
              {/* Lifecycle State Filter */}
              <div className="flex items-center gap-1.5">
                <span className="text-slate-400 font-semibold">Lifecycle State:</span>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
                >
                  <option value="ALL">All States</option>
                  <option value="NEW">NEW (Unacknowledged)</option>
                  <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
                  <option value="UNDER_INVESTIGATION">UNDER_INVESTIGATION</option>
                  <option value="VERIFIED">VERIFIED</option>
                  <option value="ESCALATED">ESCALATED</option>
                  <option value="DISMISSED">DISMISSED</option>
                  <option value="CLOSED">CLOSED</option>
                </select>
              </div>

              {/* Alert Level Filter */}
              <div className="flex items-center gap-1.5">
                <span className="text-slate-400 font-semibold">Alert Level:</span>
                <select
                  value={levelFilter}
                  onChange={(e) => setLevelFilter(e.target.value)}
                  className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
                >
                  <option value="ALL">All Levels</option>
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="MODERATE">MODERATE</option>
                  <option value="LOW">LOW</option>
                </select>
              </div>

              {/* State Filter */}
              <div className="flex items-center gap-1.5">
                <span className="text-slate-400 font-semibold">State:</span>
                <select
                  value={stateFilter}
                  onChange={(e) => setStateFilter(e.target.value)}
                  className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500 max-w-[130px]"
                >
                  <option value="ALL">All States</option>
                  <option value="Gujarat">Gujarat</option>
                  <option value="Jharkhand">Jharkhand</option>
                  <option value="Punjab">Punjab</option>
                  <option value="Odisha">Odisha</option>
                  <option value="Chhattisgarh">Chhattisgarh</option>
                  <option value="Madhya Pradesh">Madhya Pradesh</option>
                </select>
              </div>

              {/* Sort Order */}
              <div className="flex items-center gap-1.5">
                <span className="text-slate-400 font-semibold">Order:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="p-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
                >
                  <option value="priority">Priority Score (High → Low)</option>
                  <option value="recency">Recency (Newest First)</option>
                  <option value="risk">Risk Score</option>
                  <option value="confidence">Confidence</option>
                </select>
              </div>
            </div>

            <span className="text-slate-400 font-mono text-[11px]">
              Showing {alerts.length} operational alerts
            </span>
          </div>

          {/* Alert Queue Feed */}
          <div className="space-y-3">
            {loading && (
              <div className="p-12 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
                <RefreshCw className="w-6 h-6 animate-spin text-amber-400" />
                <span>Loading Tri-Tier operational queue...</span>
              </div>
            )}

            {!loading && alerts.length === 0 && (
              <div className="p-12 text-center text-slate-400 text-xs border border-dashed border-slate-800 rounded-2xl">
                <Bell className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <p className="font-bold text-slate-300 text-sm">No operational alerts found</p>
                <p className="text-slate-500 mt-1">All queues are clear or adjust filter parameters.</p>
              </div>
            )}

            {!loading &&
              alerts.map((alertItem) => {
                const isTier1 = alertItem.routing_tier === "TIER_1_AUTO_DISPATCH_CANDIDATE";
                const isTier2 = alertItem.routing_tier === "TIER_2_ANALYST_REVIEW_QUEUE";
                const priority = alertItem.priority_score ?? 50.0;

                return (
                  <div
                    key={alertItem.id}
                    className="p-4 rounded-2xl bg-agni-card border border-agni-border hover:border-slate-700 transition-all space-y-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex flex-wrap items-center gap-2.5">
                        {/* Priority Score Badge */}
                        <div
                          className="px-2.5 py-1 rounded-xl font-mono font-black text-xs text-slate-950 flex items-center gap-1 shadow"
                          style={{
                            backgroundColor:
                              priority >= 70 ? "#ef4444" : priority >= 50 ? "#f97316" : "#3b82f6",
                          }}
                        >
                          <span>PRIO: {formatNumber(priority, 1)}</span>
                        </div>

                        {/* Routing Tier Chip */}
                        {isTier1 ? (
                          <span className="px-2 py-0.5 rounded-lg bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[10px] font-mono font-bold flex items-center gap-1">
                            <Zap className="w-3 h-3" /> TIER 1 AUTO CANDIDATE
                          </span>
                        ) : isTier2 ? (
                          <span className="px-2 py-0.5 rounded-lg bg-blue-500/20 text-blue-300 border border-blue-500/30 text-[10px] font-mono font-bold flex items-center gap-1">
                            <Eye className="w-3 h-3" /> TIER 2 ANALYST REVIEW
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-mono font-bold flex items-center gap-1">
                            <HelpCircle className="w-3 h-3" /> TIER 3 UNCERTAINTY
                          </span>
                        )}

                        {/* Lifecycle State */}
                        <span
                          className={`px-2 py-0.5 rounded-lg text-[10px] font-mono font-bold uppercase ${
                            alertItem.status === "NEW"
                              ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                              : alertItem.status === "UNDER_INVESTIGATION"
                              ? "bg-sky-500/20 text-sky-300 border border-sky-500/30"
                              : alertItem.status === "VERIFIED"
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                              : alertItem.status === "ESCALATED"
                              ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {alertItem.status}
                        </span>

                        <span className="font-mono text-xs font-bold text-white">
                          {alertItem.event_code || alertItem.title}
                        </span>
                      </div>

                      <RiskBadge level={alertItem.alert_level} score={alertItem.risk_score} />
                    </div>

                    <p className="text-xs text-slate-300">{alertItem.description}</p>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs pt-1">
                      <div className="p-2 rounded-xl bg-slate-900/60 border border-slate-800">
                        <div className="text-[10px] text-slate-400">PREDICTED SOURCE</div>
                        <div className="font-bold text-amber-300 mt-0.5 truncate">
                          {alertItem.predicted_class || "Evaluating"}
                        </div>
                      </div>

                      <div className="p-2 rounded-xl bg-slate-900/60 border border-slate-800">
                        <div className="text-[10px] text-slate-400">CONFIDENCE</div>
                        <div className="font-bold text-emerald-400 font-mono mt-0.5">
                          {formatPercent(alertItem.confidence, 1, "—")}
                        </div>
                      </div>

                      <div className="p-2 rounded-xl bg-slate-900/60 border border-slate-800">
                        <div className="text-[10px] text-slate-400">LOCATION</div>
                        <div className="font-bold text-slate-200 mt-0.5 truncate">
                          {alertItem.state || "National"} {alertItem.district ? `• ${alertItem.district}` : ""}
                        </div>
                      </div>

                      <div className="p-2 rounded-xl bg-slate-900/60 border border-slate-800">
                        <div className="text-[10px] text-slate-400">DETECTED TIME</div>
                        <div className="font-mono text-slate-300 mt-0.5">
                          {new Date(alertItem.created_at).toLocaleString()}
                        </div>
                      </div>
                    </div>

                    {/* Action Bar */}
                    <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800/80">
                      {/* State Machine Transition Actions */}
                      <div className="flex flex-wrap items-center gap-2">
                        {alertItem.status === "NEW" && (
                          <button
                            onClick={() => openActionModal(alertItem, "ACKNOWLEDGE")}
                            className="px-3 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30 text-xs font-bold font-mono transition-colors"
                          >
                            Acknowledge →
                          </button>
                        )}

                        {alertItem.status === "ACKNOWLEDGED" && (
                          <button
                            onClick={() => openActionModal(alertItem, "START_INVESTIGATION")}
                            className="px-3 py-1 rounded-lg bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/30 text-xs font-bold font-mono transition-colors"
                          >
                            Start Investigation →
                          </button>
                        )}

                        {alertItem.status === "UNDER_INVESTIGATION" && (
                          <>
                            <button
                              onClick={() => openActionModal(alertItem, "VERIFY")}
                              className="px-3 py-1 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 text-xs font-bold font-mono transition-colors"
                            >
                              Verify Ground Truth
                            </button>
                            <button
                              onClick={() => openActionModal(alertItem, "ESCALATE")}
                              className="px-3 py-1 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 text-xs font-bold font-mono transition-colors"
                            >
                              Escalate
                            </button>
                          </>
                        )}

                        {["VERIFIED", "ESCALATED", "DISMISSED"].includes(alertItem.status) && (
                          <button
                            onClick={() => openActionModal(alertItem, "CLOSE")}
                            className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-bold font-mono transition-colors"
                          >
                            Close Alert
                          </button>
                        )}

                        {["NEW", "ACKNOWLEDGED", "UNDER_INVESTIGATION"].includes(alertItem.status) && (
                          <button
                            onClick={() => openActionModal(alertItem, "DISMISS")}
                            className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs font-mono transition-colors"
                          >
                            Dismiss
                          </button>
                        )}
                      </div>

                      {/* Link to Full Dossier */}
                      <Link
                        href={`/dashboard/events/${alertItem.event_id}`}
                        className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-400 hover:text-amber-300 font-bold text-xs flex items-center gap-1.5 transition-colors border border-slate-700"
                      >
                        <span>Full Evidence Dossier</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                );
              })}
          </div>

          {/* Action Modal */}
          {actionModalOpen && selectedAlert && (
            <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
              <div className="bg-agni-card border border-agni-border rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
                <div className="flex items-center justify-between border-b border-agni-border pb-3">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <CheckSquare className="w-5 h-5 text-amber-400" />
                    <span>Analyst Action: {targetAction}</span>
                  </h3>
                  <button
                    onClick={() => setActionModalOpen(false)}
                    className="p-1 rounded text-slate-400 hover:text-white"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-1">
                  <div className="text-slate-400">Target Alert:</div>
                  <div className="font-mono font-bold text-white">{selectedAlert.title}</div>
                  <div className="text-[11px] text-slate-400">
                    Current State: <strong className="text-amber-300">{selectedAlert.status}</strong> → Next State:{" "}
                    <strong className="text-emerald-300">
                      {targetAction === "ACKNOWLEDGE"
                        ? "ACKNOWLEDGED"
                        : targetAction === "START_INVESTIGATION"
                        ? "UNDER_INVESTIGATION"
                        : targetAction === "VERIFY"
                        ? "VERIFIED"
                        : targetAction === "ESCALATE"
                        ? "ESCALATED"
                        : targetAction === "DISMISS"
                        ? "DISMISSED"
                        : "CLOSED"}
                    </strong>
                  </div>
                </div>

                <form onSubmit={handleExecuteAction} className="space-y-4 text-xs">
                  {targetAction === "VERIFY" && (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-slate-300 font-semibold mb-1">
                          Verified Ground Truth Class:
                        </label>
                        <select
                          value={groundTruthClass}
                          onChange={(e) => setGroundTruthClass(e.target.value)}
                          className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
                        >
                          <option value="Agricultural Burning">Agricultural Burning</option>
                          <option value="Gas Flare">Gas Flare</option>
                          <option value="Industrial Fire">Industrial Fire</option>
                          <option value="Forest Fire">Forest Fire</option>
                          <option value="Landfill / Urban Fire">Landfill / Urban Fire</option>
                          <option value="Biomass / Stubble">Biomass / Stubble</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-slate-300 font-semibold mb-1">
                          Verification Outcome:
                        </label>
                        <select
                          value={verificationOutcome}
                          onChange={(e) => setVerificationOutcome(e.target.value)}
                          className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
                        >
                          <option value="CONFIRM">CONFIRM (Matches ML Prediction)</option>
                          <option value="RECLASSIFY">RECLASSIFY (Override with Ground Truth)</option>
                          <option value="REJECT">REJECT (False Hotspot / Sensor Noise)</option>
                        </select>
                      </div>
                    </div>
                  )}

                  <div>
                    <label className="block text-slate-300 font-semibold mb-1">
                      Analyst Decision Notes & Audit Evidence:
                    </label>
                    <textarea
                      rows={3}
                      value={actionNotes}
                      onChange={(e) => setActionNotes(e.target.value)}
                      placeholder="Document rationale, satellite evidence review, or agency coordination notes..."
                      className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
                    />
                  </div>

                  {actionMessage && (
                    <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-amber-300 font-mono text-[11px]">
                      {actionMessage}
                    </div>
                  )}

                  <div className="flex items-center justify-end gap-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setActionModalOpen(false)}
                      className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold"
                    >
                      Cancel
                    </button>

                    <button
                      type="submit"
                      disabled={actionSubmitting}
                      className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-slate-950 font-bold flex items-center gap-1.5 shadow-md"
                    >
                      {actionSubmitting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                      <span>Commit Decision to Audit Log</span>
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
