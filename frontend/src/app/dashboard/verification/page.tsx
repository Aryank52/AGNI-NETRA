"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import RiskBadge from "@/components/intelligence/RiskBadge";
import { ThermalEvent } from "@/types";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { formatNumber, formatFrp, formatPercent, formatCoord } from "@/lib/formatters";
import { 
  CheckSquare, Shield, CheckCircle2, 
  XCircle, HelpCircle, ChevronRight, MessageSquare
} from "lucide-react";

export default function VerificationPage() {
  const { user } = useAuth();
  const [queue, setQueue] = useState<ThermalEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeModalEvent, setActiveModalEvent] = useState<ThermalEvent | null>(null);
  const [verifiedClass, setVerifiedClass] = useState("Industrial Fire");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadQueue = async () => {
    try {
      const data = await fetchApi<ThermalEvent[]>("/verification/queue");
      setQueue(data);
    } catch (err) {
      console.warn("Failed to load verification queue:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const handleVerify = async (action: string) => {
    if (!activeModalEvent) return;
    setSubmitting(true);
    try {
      await fetchApi("/verification", {
        method: "POST",
        body: JSON.stringify({
          event_id: activeModalEvent.id,
          verified_label: verifiedClass,
          verification_action: action,
          notes: notes || `Verified by ${user?.full_name || "Analyst"}`,
        }),
      });
      alert(`Event ${activeModalEvent.event_code} verified (${action}) and fed back to model training!`);
      setActiveModalEvent(null);
      await loadQueue();
    } catch (err) {
      alert("Failed to submit verification: " + err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-6xl mx-auto">
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-agni-border pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 font-bold">
                  HUMAN-IN-THE-LOOP ACTIVE LEARNING
                </span>
                <span className="text-xs text-slate-400">Analyst Verification Queue</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5 mt-1">
                <CheckSquare className="w-6 h-6 text-blue-400" />
                Thermal Event Verification & Feedback Loop
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Confirm, correct, or mark uncertain predictions. Verified labels are automatically preserved in <code className="text-amber-400">verification_records</code> to retrain future model versions.
              </p>
            </div>

            <span className="text-xs font-mono px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-300">
              {queue.length} Events Awaiting Review
            </span>
          </div>

          {/* Queue List */}
          <div className="space-y-4">
            {queue.map((evt) => (
              <div
                key={evt.id}
                className="p-5 rounded-2xl bg-agni-card border border-agni-border hover:border-blue-500/40 transition-all space-y-3 shadow-lg"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm font-bold text-amber-400">{evt.event_code}</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {evt.state} {evt.district ? `(${evt.district})` : ""}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                      {evt.facility_status} CONTEXT
                    </span>
                  </div>

                  <RiskBadge level={evt.risk?.risk_level || "LOW"} score={evt.risk?.risk_score} />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs font-mono">
                  <div>
                    <div className="text-[10px] text-slate-500">AI PREDICTION</div>
                    <div className="text-white font-bold">{evt.prediction?.predicted_class || "Uncertain"}</div>
                    <div className="text-[10px] text-amber-400 font-bold">
                      {formatPercent(evt.prediction?.confidence, 1, "80.0%")} Confidence
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] text-slate-500">PEAK RADIATIVE POWER</div>
                    <div className="text-white font-bold">{formatFrp(evt.max_frp)}</div>
                    <div className="text-[10px] text-slate-400">{evt.detection_count} Observations</div>
                  </div>

                  <div>
                    <div className="text-[10px] text-slate-500">PERSISTENCE</div>
                    <div className="text-emerald-400 font-bold">
                      {formatNumber(evt.features?.persistence_score, 1, "N/A")} / 10.0
                    </div>
                    <div className="text-[10px] text-slate-400">Day/Night: {formatNumber(evt.features?.day_night_ratio, 2, "1.00")}x</div>
                  </div>

                  <div>
                    <div className="text-[10px] text-slate-500">ACTION REQUIRED</div>
                    <div className="text-cyan-400 font-bold">
                      {evt.facility_status === "CANDIDATE" ? "Validate Candidate Source" : "Review Ambiguity"}
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
                  <span className="text-[11px] text-slate-400">
                    Location: {formatCoord(evt.latitude, evt.longitude, 4)}
                  </span>

                  <div className="flex items-center gap-2">
                    <Link
                      href={`/dashboard/events/${evt.id}`}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                    >
                      Inspect Dossier
                    </Link>
                    <button
                      onClick={() => {
                        setActiveModalEvent(evt);
                        setVerifiedClass(evt.prediction?.predicted_class || "Industrial Fire");
                      }}
                      className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md shadow-blue-500/20 flex items-center gap-1.5"
                    >
                      <CheckSquare className="w-3.5 h-3.5" />
                      <span>Verify Label</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Verification Modal */}
          {activeModalEvent && (
            <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 z-50 animate-in fade-in">
              <div className="w-full max-w-lg bg-agni-card border border-agni-border rounded-2xl p-6 shadow-2xl space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-white font-mono">
                    Verify Event: {activeModalEvent.event_code}
                  </h3>
                  <button
                    onClick={() => setActiveModalEvent(null)}
                    className="text-slate-400 hover:text-white"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-4 text-xs">
                  <div>
                    <label className="block font-semibold text-slate-300 mb-1">
                      Assigned Ground-Truth Classification
                    </label>
                    <select
                      value={verifiedClass}
                      onChange={(e) => setVerifiedClass(e.target.value)}
                      className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
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
                    <label className="block font-semibold text-slate-300 mb-1">
                      Analyst Ground Verification Notes
                    </label>
                    <textarea
                      rows={3}
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="e.g. Cross-verified with Sentinel-2 SWIR band and state pollution control board telemetry..."
                      className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-amber-500"
                    />
                  </div>

                  <div className="grid grid-cols-3 gap-2 pt-2">
                    <button
                      onClick={() => handleVerify("CONFIRM")}
                      disabled={submitting}
                      className="py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold shadow-md transition-all flex items-center justify-center gap-1"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Confirm</span>
                    </button>
                    <button
                      onClick={() => handleVerify("CORRECT")}
                      disabled={submitting}
                      className="py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold shadow-md transition-all flex items-center justify-center gap-1"
                    >
                      <span>Correct Label</span>
                    </button>
                    <button
                      onClick={() => handleVerify("FALSE_POSITIVE")}
                      disabled={submitting}
                      className="py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold shadow-md transition-all flex items-center justify-center gap-1"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>False Sensor</span>
                    </button>
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
