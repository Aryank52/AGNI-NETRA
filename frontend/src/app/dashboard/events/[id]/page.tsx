"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import RiskBadge from "@/components/intelligence/RiskBadge";
import ShapWaterfallChart from "@/components/intelligence/ShapWaterfallChart";
import EvidenceSummaryCard from "@/components/intelligence/EvidenceSummaryCard";
import { ThermalEvent, User } from "@/types";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { 
  ArrowLeft, Download, CheckSquare, Shield, 
  Activity, MapPin, Calendar, Clock, AlertTriangle, 
  CheckCircle2, Sparkles, Database, FileText,
  HelpCircle, Cpu, Layers, ExternalLink, RefreshCw
} from "lucide-react";

export default function EventDetailPage() {
  const params = useParams();
  const router = useRouter();
  const eventId = params.id as string;
  const { user } = useAuth();

  const [event, setEvent] = useState<ThermalEvent | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifModalOpen, setVerifModalOpen] = useState(false);
  const [verifAction, setVerifAction] = useState("CONFIRM");
  const [verifiedLabel, setVerifiedLabel] = useState("Industrial Fire");
  const [verifNotes, setVerifNotes] = useState("");
  const [verifSubmitting, setVerifSubmitting] = useState(false);
  const [verifSuccess, setVerifSuccess] = useState(false);

  const loadEvent = async () => {
    try {
      const data = await fetchApi<ThermalEvent>(`/events/${eventId}`);
      setEvent(data);
      setVerifiedLabel(data.prediction?.predicted_class || "Industrial Fire");
    } catch (err) {
      console.warn("Failed to fetch event detail:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (eventId) {
      loadEvent();
    }
  }, [eventId]);

  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setVerifSubmitting(true);
    try {
      await fetchApi("/verification", {
        method: "POST",
        body: JSON.stringify({
          event_id: eventId,
          verified_label: verifiedLabel,
          verification_action: verifAction,
          notes: verifNotes,
        }),
      });
      setVerifSuccess(true);
      setTimeout(() => {
        setVerifModalOpen(false);
        setVerifSuccess(false);
        loadEvent();
      }, 1200);
    } catch (err) {
      alert("Failed to submit verification: " + err);
    } finally {
      setVerifSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-agni-navy flex items-center justify-center text-slate-400 font-mono text-sm">
        <RefreshCw className="w-5 h-5 animate-spin mr-2 text-amber-400" />
        Loading AGNI-NETRA AI Intelligence Dossier...
      </div>
    );
  }

  if (!event) {
    return (
      <div className="min-h-screen bg-agni-navy flex flex-col items-center justify-center text-slate-300 space-y-4">
        <div className="text-xl font-bold">Event Dossier Not Found</div>
        <Link href="/dashboard" className="text-amber-400 hover:underline text-sm">
          ← Return to GIS Command Map
        </Link>
      </div>
    );
  }

  const pClass = event.prediction?.predicted_class || "Uncertain";
  const confidence = event.prediction?.confidence || 0.85;
  const uncertainty = (1.0 - confidence) * 0.8; // Normalized uncertainty display
  const modelVersion = "v1.0.0-xgboost";
  const isCandidate = event.facility_status === "CANDIDATE";

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-6xl mx-auto">
          {/* Back Button & Actions Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-agni-border pb-4">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Command Map</span>
            </Link>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setVerifModalOpen(true)}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white font-bold text-xs shadow-lg shadow-blue-500/20 flex items-center gap-2 transition-all"
              >
                <CheckSquare className="w-4 h-4" />
                <span>Analyst Verification (HITL)</span>
              </button>

              <a
                href={`http://localhost:8000/api/v1/reports/event/${event.id}/download`}
                target="_blank"
                rel="noreferrer"
                className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 flex items-center gap-2 transition-all"
              >
                <Download className="w-4 h-4 text-slate-950" />
                <span>Download PDF Dossier</span>
              </a>
            </div>
          </div>

          {/* Dossier Header Banner with Provenance */}
          <div className="p-6 rounded-2xl bg-agni-card border border-agni-border shadow-xl space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-extrabold text-white tracking-wide font-mono">
                    {event.event_code}
                  </h1>
                  <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    {event.state} {event.district ? `• ${event.district}` : ""}
                  </span>
                  {event.is_demo ? (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      SAMPLE CALIBRATION DATA
                    </span>
                  ) : (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      LIVE NRT TELEMETRY
                    </span>
                  )}
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                    event.status === "VERIFIED"
                      ? "bg-blue-500/20 text-blue-300 border-blue-500/30"
                      : "bg-slate-800 text-slate-400 border-slate-700"
                  }`}>
                    STATUS: {event.status}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Coordinates: {event.latitude.toFixed(5)}°N, {event.longitude.toFixed(5)}°E • First seen: {new Date(event.first_seen).toLocaleString()} • Last seen: {new Date(event.last_seen).toLocaleString()}
                </p>
              </div>

              <div className="flex items-center gap-3">
                <RiskBadge level={event.risk?.risk_level || "LOW"} score={event.risk?.risk_score} />
              </div>
            </div>

            {/* AI Classification & Uncertainty Intelligence Matrix */}
            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 grid grid-cols-1 sm:grid-cols-5 gap-4 text-xs font-mono">
              <div>
                <div className="text-[10px] text-slate-500 uppercase">AI Classification</div>
                <div className="text-base font-extrabold text-amber-400 font-sans">{pClass}</div>
                <div className="text-[10px] text-emerald-400 font-bold">{(confidence * 100).toFixed(1)}% Confidence</div>
              </div>

              <div>
                <div className="text-[10px] text-slate-500 uppercase">Uncertainty Score</div>
                <div className="text-base font-extrabold text-cyan-300">
                  {uncertainty.toFixed(3)}
                </div>
                <div className="text-[10px] text-slate-400 font-sans">
                  {uncertainty < 0.25 ? "Low Uncertainty" : uncertainty < 0.50 ? "Moderate" : "High (HITL Flag)"}
                </div>
              </div>

              <div>
                <div className="text-[10px] text-slate-500 uppercase">Peak FRP</div>
                <div className="text-base font-extrabold text-white">{event.max_frp.toFixed(1)} MW</div>
                <div className="text-[10px] text-slate-400">Mean: {event.avg_frp.toFixed(1)} MW</div>
              </div>

              <div>
                <div className="text-[10px] text-slate-500 uppercase">Persistence Metric</div>
                <div className="text-base font-extrabold text-emerald-400">
                  {event.features?.persistence_score?.toFixed(1) || "N/A"} / 10.0
                </div>
                <div className="text-[10px] text-slate-400">{event.detection_count} Satellite Passes</div>
              </div>

              <div>
                <div className="text-[10px] text-slate-500 uppercase">Facility Context</div>
                <div className="text-base font-extrabold text-white">
                  {event.nearest_facility_distance_m !== undefined ? `${event.nearest_facility_distance_m.toFixed(0)}m` : "Uncataloged"}
                </div>
                <div className="text-[10px] text-purple-300 font-bold">{isCandidate ? "CANDIDATE DISCOVERY" : event.facility_status}</div>
              </div>
            </div>

            {/* Model Architecture & Provenance Strip */}
            <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-slate-400">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-amber-400" />
                  <strong>Model:</strong> {modelVersion} (XGBoost 7-Class + SHAP)
                </span>
                <span className="flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-cyan-400" />
                  <strong>Sources:</strong> NASA FIRMS VIIRS/MODIS • ISRO Bhuvan (10m) • OSM
                </span>
              </div>
              <div>
                <span>LULC: <strong className="text-white">{event.landcover_class}</strong></span>
              </div>
            </div>
          </div>

          {/* Explainable AI SHAP Waterfall Chart */}
          <ShapWaterfallChart
            shapData={event.prediction?.shap_values}
            predictedClass={pClass}
            confidence={confidence}
          />

          {/* Two-Column Intelligence Grid: Risk & Multi-Sensor Provenance */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Risk Drivers Breakdown */}
            <div className="p-5 rounded-2xl bg-agni-card border border-agni-border space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
                <Shield className="w-4 h-4 text-red-400" />
                AGNI-NETRA Risk Evaluation Matrix
              </h3>
              <p className="text-[11px] text-slate-400">
                Transparent multi-factor formula evaluating thermal intensity, baseline deviation, and surrounding exposure.
              </p>

              <div className="space-y-2 pt-2">
                {event.risk?.risk_reasons?.map((reason, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5 shrink-0" />
                    <span>{reason}</span>
                  </div>
                ))}
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800 grid grid-cols-3 gap-2 text-[11px] font-mono text-center">
                <div className="p-2 rounded bg-slate-900 border border-slate-800">
                  <div className="text-slate-500">INTENSITY</div>
                  <div className="font-bold text-white">{event.risk?.intensity_subscore?.toFixed(0) || 60}/100</div>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-slate-800">
                  <div className="text-slate-500">ABNORMALITY</div>
                  <div className="font-bold text-amber-400">{event.risk?.abnormality_subscore?.toFixed(0) || 20}/100</div>
                </div>
                <div className="p-2 rounded bg-slate-900 border border-slate-800">
                  <div className="text-slate-500">EXPOSURE</div>
                  <div className="font-bold text-red-400">{event.risk?.exposure_subscore?.toFixed(0) || 40}/100</div>
                </div>
              </div>
            </div>

            {/* Evidence Card */}
            <EvidenceSummaryCard event={event} />
          </div>

          {/* HITL Analyst Verification Modal */}
          {verifModalOpen && (
            <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 z-50 animate-in fade-in">
              <div className="w-full max-w-lg bg-agni-card border border-agni-border rounded-2xl p-6 shadow-2xl space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
                    <CheckSquare className="w-4 h-4 text-blue-400" />
                    Human-in-the-Loop Verification
                  </h3>
                  <button
                    onClick={() => setVerifModalOpen(false)}
                    className="text-slate-400 hover:text-white text-xs font-bold"
                  >
                    ✕
                  </button>
                </div>

                {verifSuccess ? (
                  <div className="p-6 text-center space-y-2 text-emerald-400">
                    <CheckCircle2 className="w-10 h-10 mx-auto animate-bounce" />
                    <div className="font-bold text-sm">Verification Stored Successfully!</div>
                    <p className="text-xs text-slate-400">Fed back into active learning pipeline.</p>
                  </div>
                ) : (
                  <form onSubmit={handleVerifySubmit} className="space-y-4 text-xs">
                    <div>
                      <label className="block font-semibold text-slate-300 mb-1">
                        Verification Action
                      </label>
                      <select
                        value={verifAction}
                        onChange={(e) => setVerifAction(e.target.value)}
                        className="w-full p-2 rounded-xl bg-slate-900 border border-slate-700 text-white"
                      >
                        <option value="CONFIRM">Confirm AI Prediction</option>
                        <option value="OVERRIDE">Correct / Override Classification</option>
                        <option value="MARK_UNCERTAIN">Mark Uncertain / Needs Ground Survey</option>
                        <option value="REJECT">Flag as False Positive Sensor Glint</option>
                      </select>
                    </div>

                    <div>
                      <label className="block font-semibold text-slate-300 mb-1">
                        Verified Ground Truth Class
                      </label>
                      <select
                        value={verifiedLabel}
                        onChange={(e) => setVerifiedLabel(e.target.value)}
                        className="w-full p-2 rounded-xl bg-slate-900 border border-slate-700 text-white font-medium"
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
                        Analyst Observation Notes
                      </label>
                      <textarea
                        rows={3}
                        value={verifNotes}
                        onChange={(e) => setVerifNotes(e.target.value)}
                        placeholder="Enter domain notes (e.g. Cross-referenced with Sentinel-2 SWIR band and local CPCB station)..."
                        className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500"
                      />
                    </div>

                    <div className="flex items-center justify-end gap-3 pt-2">
                      <button
                        type="button"
                        onClick={() => setVerifModalOpen(false)}
                        className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={verifSubmitting}
                        className="px-5 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white font-bold shadow-md shadow-blue-500/20"
                      >
                        {verifSubmitting ? "Submitting..." : "Submit Verification Record"}
                      </button>
                    </div>
                  </form>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
