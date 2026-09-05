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
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { formatNumber, formatFrp, formatPercent, formatCoord, formatDistance, safeNumber } from "@/lib/formatters";
import { 
  CheckSquare, Shield, CheckCircle2, 
  XCircle, HelpCircle, ChevronRight, MessageSquare,
  Activity, MapPin, Eye, AlertTriangle, UserCheck,
  Flame, Cpu, Database, RefreshCw, ExternalLink, Sliders
} from "lucide-react";

export default function VerificationPage() {
  const { user } = useAuth();
  const [queue, setQueue] = useState<ThermalEvent[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<ThermalEvent | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifiedClass, setVerifiedClass] = useState("Industrial Fire");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const loadQueue = async () => {
    try {
      const data = await fetchApi<ThermalEvent[]>("/verification/queue");
      const list = Array.isArray(data) ? data : [];
      setQueue(list);
      if (list.length > 0 && (!selectedEvent || !list.some((e) => e.id === selectedEvent.id))) {
        setSelectedEvent(list[0]);
        setVerifiedClass(list[0].prediction?.predicted_class || "Industrial Fire");
      } else if (list.length === 0) {
        setSelectedEvent(null);
      }
    } catch (err) {
      console.warn("Failed to load verification queue:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const handleSelectEvent = (evt: ThermalEvent) => {
    setSelectedEvent(evt);
    setVerifiedClass(evt.prediction?.predicted_class || "Industrial Fire");
    setNotes("");
  };

  const handleVerify = async (action: string) => {
    if (!selectedEvent) return;
    setSubmitting(true);
    try {
      await fetchApi("/verification", {
        method: "POST",
        body: JSON.stringify({
          event_id: selectedEvent.id,
          verified_label: verifiedClass,
          verification_action: action,
          notes: notes || `Verified by ${user?.full_name || "Thermal Analyst"}`,
        }),
      });
      setNotification({
        type: "success",
        message: `Event ${selectedEvent.event_code} successfully verified (${action}) and committed to active learning audit records.`
      });
      setNotes("");
      await loadQueue();
    } catch (err: any) {
      setNotification({
        type: "error",
        message: "Failed to submit verification: " + (err?.message || err)
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950 font-sans">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-7xl mx-auto w-full">
          {/* Standardized Page Header */}
          <PageHeader
            category="HUMAN-IN-THE-LOOP ACTIVE LEARNING"
            title="Analyst Verification & Active Learning Workstation"
            description="Operational triage desk for confirming, reclassifying, or disputing satellite thermal observations. Human determinations visually outrank model suggestions and are preserved in verification_records to govern future retrained model candidates."
            icon={<CheckSquare className="w-6 h-6 text-blue-400" />}
            actions={
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-300 font-bold">
                  {queue.length} Events In Work Queue
                </span>
                <button
                  onClick={loadQueue}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                  title="Refresh Queue"
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-amber-400" : ""}`} />
                </button>
              </div>
            }
          />

          {/* Status Notification Banner */}
          {notification && (
            <div className={`p-3.5 rounded-xl border text-xs flex items-center justify-between font-mono ${
              notification.type === "success"
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                : "bg-red-500/10 border-red-500/30 text-red-300"
            }`}>
              <div className="flex items-center gap-2">
                {notification.type === "success" ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-400 shrink-0" />
                )}
                <span>{notification.message}</span>
              </div>
              <button
                onClick={() => setNotification(null)}
                className="text-slate-400 hover:text-white text-xs font-mono ml-4"
              >
                Dismiss
              </button>
            </div>
          )}

          {loading ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <CardSkeleton />
              <CardSkeleton />
              <CardSkeleton />
            </div>
          ) : queue.length === 0 ? (
            <EmptyState
              title="Verification Queue Clear"
              description="No thermal events currently await human analyst review. All items in the Tier 2 and Tier 3 triage queues have been resolved."
              actionLabel="Refresh Verification Queue"
              onAction={loadQueue}
            />
          ) : selectedEvent && (
            <div className="space-y-6">
              {/* Tri-Panel Workstation Layout */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
                {/* PANEL 1: LEFT (Cols 1-4) - Event Selection & Spatial Context */}
                <div className="lg:col-span-4 space-y-4">
                  {/* Active Queue Card List */}
                  <div className="p-4 rounded-2xl bg-agni-card border border-agni-border space-y-3 shadow-md">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                      <span className="text-xs font-bold text-slate-300 uppercase font-mono flex items-center gap-1.5">
                        <Activity className="w-3.5 h-3.5 text-amber-400" />
                        Triage Queue ({queue.length})
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">Select to review</span>
                    </div>

                    <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                      {queue.map((evt) => {
                        const isSelected = evt.id === selectedEvent.id;
                        return (
                          <div
                            key={evt.id}
                            onClick={() => handleSelectEvent(evt)}
                            className={`p-2.5 rounded-xl border text-xs cursor-pointer transition-all ${
                              isSelected
                                ? "bg-blue-500/15 border-blue-500 text-white font-bold ring-1 ring-blue-500/50 shadow-sm"
                                : "bg-slate-900/60 hover:bg-slate-800 border-slate-800 text-slate-300"
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-mono text-xs font-bold text-amber-400">{evt.event_code}</span>
                              <RiskBadge level={evt.risk?.risk_level || "LOW"} score={evt.risk?.risk_score} />
                            </div>
                            <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                              <span>{evt.state}</span>
                              <span className="text-orange-400">{formatFrp(evt.max_frp)}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Selected Event Spatial Context Dossier */}
                  <div className="p-4 rounded-2xl bg-agni-card border border-agni-border space-y-3 shadow-md">
                    <span className="text-xs font-bold text-slate-300 uppercase font-mono flex items-center gap-1.5 border-b border-slate-800 pb-2">
                      <MapPin className="w-3.5 h-3.5 text-cyan-400" />
                      Spatial & Sensor Context
                    </span>

                    <div className="space-y-2 text-xs font-mono">
                      <div className="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800 space-y-1">
                        <div className="text-[10px] text-slate-500 uppercase">COORDINATES & ADMINISTRATIVE</div>
                        <div className="text-white font-bold">{formatCoord(selectedEvent.latitude, selectedEvent.longitude, 5)}</div>
                        <div className="text-slate-300">{selectedEvent.state} {selectedEvent.district ? `• ${selectedEvent.district}` : ""}</div>
                      </div>

                      <div className="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800 space-y-1">
                        <div className="text-[10px] text-slate-500 uppercase">THERMAL RADIATIVE PROFILE</div>
                        <div className="flex items-center justify-between text-slate-300">
                          <span>Peak FRP:</span>
                          <span className="text-orange-400 font-bold">{formatFrp(selectedEvent.max_frp)}</span>
                        </div>
                        <div className="flex items-center justify-between text-slate-300">
                          <span>Mean FRP:</span>
                          <span className="text-slate-200">{formatFrp(selectedEvent.avg_frp)}</span>
                        </div>
                        <div className="flex items-center justify-between text-slate-300">
                          <span>Hotspot Passes:</span>
                          <span className="text-cyan-400 font-bold">{selectedEvent.detection_count || 1} detections</span>
                        </div>
                      </div>

                      <div className="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800 space-y-1">
                        <div className="text-[10px] text-slate-500 uppercase">FACILITY CADASTRE CONTEXT</div>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-300">Status:</span>
                          <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                            selectedEvent.facility_status === "CANDIDATE"
                              ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                              : selectedEvent.facility_status === "KNOWN"
                              ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                              : "bg-slate-800 text-slate-400"
                          }`}>
                            {selectedEvent.facility_status}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400">
                          {selectedEvent.nearest_facility_distance_m !== undefined && selectedEvent.nearest_facility_distance_m !== null
                            ? `${formatDistance(selectedEvent.nearest_facility_distance_m)} to nearest industrial plant`
                            : "No registered industrial facility in 10 km"}
                        </div>
                      </div>

                      <Link
                        href={`/dashboard/events/${selectedEvent.id}`}
                        target="_blank"
                        className="w-full py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-[11px] font-semibold border border-slate-700 flex items-center justify-center gap-1.5 transition-colors"
                      >
                        <span>Open 7-Layer Investigation Dossier</span>
                        <ExternalLink className="w-3 h-3 text-amber-400" />
                      </Link>
                    </div>
                  </div>
                </div>

                {/* PANEL 2: CENTER (Cols 5-8) - Model Classification & Evidence */}
                <div className="lg:col-span-4 space-y-4">
                  <div className="p-4 rounded-2xl bg-agni-card border border-agni-border space-y-3.5 shadow-md">
                    <span className="text-xs font-bold text-slate-300 uppercase font-mono flex items-center gap-1.5 border-b border-slate-800 pb-2">
                      <Cpu className="w-3.5 h-3.5 text-amber-400" />
                      Machine Learning Hypothesis & Evidence
                    </span>

                    {/* Model Prediction Box */}
                    <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                      <div className="text-[10px] text-slate-500 font-mono uppercase">ALGORITHMIC HYPOTHESIS</div>
                      <div className="text-base font-black text-amber-400">
                        {selectedEvent.prediction?.predicted_class || "Uncertain"}
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs font-mono">
                          <span className="text-slate-400">Calibrated Confidence:</span>
                          <span className="text-emerald-400 font-bold">
                            {formatPercent(selectedEvent.prediction?.confidence, 1, "80.0%")}
                          </span>
                        </div>
                        <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                          <div
                            className="h-full bg-emerald-500 rounded-full"
                            style={{ width: `${Math.min(100, (selectedEvent.prediction?.confidence || 0.8) * 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Multi-Factor Feature Evidence Vector */}
                    <div className="space-y-2 text-xs font-mono">
                      <div className="text-[10px] text-slate-500 uppercase">OBSERVATIONAL EVIDENCE VECTORS</div>

                      <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
                        <div>
                          <span className="text-slate-300 block">Persistence Score</span>
                          <span className="text-[10px] text-slate-500">Multi-day temporal continuity</span>
                        </div>
                        <span className="text-emerald-400 font-bold">
                          {formatNumber(selectedEvent.features?.persistence_score, 1, "5.0")}/10
                        </span>
                      </div>

                      <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
                        <div>
                          <span className="text-slate-300 block">Day / Night Ratio</span>
                          <span className="text-[10px] text-slate-500">24x7 industrial vs diurnal burning</span>
                        </div>
                        <span className="text-cyan-400 font-bold">
                          {formatNumber(selectedEvent.features?.day_night_ratio, 2, "1.00")}x
                        </span>
                      </div>

                      <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
                        <div>
                          <span className="text-slate-300 block">Baseline Deviation Ratio</span>
                          <span className="text-[10px] text-slate-500">Surge above historical background</span>
                        </div>
                        <span className="text-orange-400 font-bold">
                          {formatNumber(selectedEvent.features?.baseline_deviation_ratio, 2, "2.40")}σ
                        </span>
                      </div>

                      <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
                        <div>
                          <span className="text-slate-300 block">5-Factor Hazard Score</span>
                          <span className="text-[10px] text-slate-500">Intensity, norm, exposure, persist, context</span>
                        </div>
                        <span className="text-red-400 font-bold">
                          {formatNumber(selectedEvent.risk?.risk_score, 1, "58.0")}/100
                        </span>
                      </div>
                    </div>

                    <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-200/90 leading-relaxed font-mono">
                      <strong>ANALYST NOTE:</strong> Machine learning scores are advisory indicators. Human analyst verification is authoritative and final.
                    </div>
                  </div>
                </div>

                {/* PANEL 3: RIGHT (Cols 9-12) - Human Decision & Action Desk */}
                <div className="lg:col-span-4 space-y-4">
                  <div className="p-4 rounded-2xl bg-agni-card border-2 border-blue-500/50 space-y-4 shadow-xl ring-1 ring-blue-500/20">
                    <div className="border-b border-slate-800 pb-2 flex items-center justify-between">
                      <span className="text-xs font-bold text-white uppercase font-mono flex items-center gap-1.5">
                        <UserCheck className="w-4 h-4 text-blue-400" />
                        Human Analyst Determination
                      </span>
                      <span className="px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 text-[9px] font-bold font-mono">
                        AUTHORITATIVE
                      </span>
                    </div>

                    <div className="space-y-3 text-xs">
                      <div>
                        <label className="block font-semibold text-slate-200 mb-1 font-mono text-[11px]">
                          ASSIGNED GROUND-TRUTH CLASS:
                        </label>
                        <select
                          value={verifiedClass}
                          onChange={(e) => setVerifiedClass(e.target.value)}
                          className="w-full p-2.5 rounded-xl bg-slate-900 border border-blue-500/40 text-white font-bold text-xs focus:outline-none focus:border-blue-400"
                        >
                          <option value="Industrial Fire">Industrial Fire</option>
                          <option value="Gas Flare">Gas Flare</option>
                          <option value="Forest Fire">Forest Fire</option>
                          <option value="Agricultural Burning">Agricultural Burning</option>
                          <option value="Mining Activity">Mining Activity</option>
                          <option value="Other Thermal Source">Other Thermal Source</option>
                          <option value="Uncertain">Uncertain</option>
                        </select>
                      </div>

                      <div>
                        <label className="block font-semibold text-slate-200 mb-1 font-mono text-[11px]">
                          VERIFICATION RATIONALE / AUDIT NOTES:
                        </label>
                        <textarea
                          rows={3}
                          value={notes}
                          onChange={(e) => setNotes(e.target.value)}
                          placeholder="e.g. Confirmed flare stack from Sentinel-2 SWIR reflection; matched Gujarat PCB register..."
                          className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:border-blue-500 font-sans"
                        />
                      </div>

                      {/* Primary Human Action Buttons */}
                      <div className="space-y-2 pt-1 font-mono">
                        <button
                          onClick={() => handleVerify("CONFIRM")}
                          disabled={submitting}
                          className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold text-xs shadow-md transition-all flex items-center justify-center gap-2"
                        >
                          <CheckCircle2 className="w-4 h-4" />
                          <span>CONFIRM MODEL CLASSIFICATION</span>
                        </button>

                        <button
                          onClick={() => handleVerify("CORRECT")}
                          disabled={submitting}
                          className="w-full py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white font-bold text-xs shadow-md transition-all flex items-center justify-center gap-2"
                        >
                          <Sliders className="w-4 h-4" />
                          <span>OVERRIDE & RECLASSIFY LABEL</span>
                        </button>

                        <div className="grid grid-cols-2 gap-2 pt-1">
                          <button
                            onClick={() => handleVerify("FALSE_POSITIVE")}
                            disabled={submitting}
                            className="py-2 rounded-xl bg-red-600/20 hover:bg-red-600/30 text-red-300 border border-red-500/30 font-bold text-[11px] transition-all flex items-center justify-center gap-1"
                          >
                            <XCircle className="w-3.5 h-3.5 text-red-400" />
                            <span>False Glint</span>
                          </button>

                          <button
                            onClick={() => handleVerify("UNCERTAIN")}
                            disabled={submitting}
                            className="py-2 rounded-xl bg-sky-600/20 hover:bg-sky-600/30 text-sky-300 border border-sky-500/30 font-bold text-[11px] transition-all flex items-center justify-center gap-1"
                          >
                            <HelpCircle className="w-3.5 h-3.5 text-sky-400" />
                            <span>Flag Uncertain</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* BELOW: Active Learning Explanation & Audit Trail */}
              <div className="p-4 rounded-2xl bg-agni-card border border-agni-border space-y-2 text-xs font-mono">
                <span className="text-slate-300 font-bold uppercase flex items-center gap-2">
                  <Database className="w-4 h-4 text-emerald-400" />
                  Active Learning & Human-in-the-Loop Governance Protocol
                </span>
                <p className="text-slate-400 font-sans leading-relaxed text-[11px]">
                  All decisions executed in this workstation are committed into <code className="text-amber-400">verification_records</code> with cryptographic timestamps and the active analyst ID. These verified labels are prioritized during candidate dataset extraction to evaluate future retrained model candidates against the frozen 2026 temporal benchmark. In accordance with national safety invariants, automated alert dispatch remains gated (ENABLE_OPERATIONAL_DISPATCH_GATE = False) until supervisory authorization.
                </p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
