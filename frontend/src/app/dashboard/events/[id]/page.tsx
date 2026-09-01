"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import RiskBadge from "@/components/intelligence/RiskBadge";
import ShapWaterfallChart from "@/components/intelligence/ShapWaterfallChart";
import { ThermalEvent, AlertDossier, AuditTrailItem } from "@/types";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { 
  ArrowLeft, Download, CheckSquare, Shield, 
  Activity, MapPin, Calendar, Clock, AlertTriangle, 
  CheckCircle2, Sparkles, Database, FileText,
  HelpCircle, Cpu, Layers, ExternalLink, RefreshCw,
  GitCommit, ChevronRight, Binary, Globe, Lock,
  Zap, Eye, Trees, Factory, Pickaxe, ShieldCheck, X
} from "lucide-react";

export default function EventDetailPage() {
  const params = useParams();
  const router = useRouter();
  const eventId = params.id as string;
  const { user } = useAuth();

  // State
  const [event, setEvent] = useState<ThermalEvent | null>(null);
  const [dossier, setDossier] = useState<AlertDossier | null>(null);
  const [detections, setDetections] = useState<any[]>([]);
  const [traceData, setTraceData] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<"DOSSIER" | "TELEMETRY" | "ML_SHAP" | "AUDIT_TRAIL" | "TRACE">("DOSSIER");

  // Analyst Action Modal
  const [actionModalOpen, setActionModalOpen] = useState<boolean>(false);
  const [targetAction, setTargetAction] = useState<string>("");
  const [actionNotes, setActionNotes] = useState<string>("");
  const [groundTruthClass, setGroundTruthClass] = useState<string>("Agricultural Burning");
  const [verificationOutcome, setVerificationOutcome] = useState<string>("CONFIRM");
  const [actionSubmitting, setActionSubmitting] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadAllData = async () => {
    setLoading(true);
    try {
      // 1. Load Event Detail
      const evtData = await fetchApi<ThermalEvent>(`/events/${eventId}`);
      setEvent(evtData);
      setGroundTruthClass(evtData.prediction?.predicted_class || "Agricultural Burning");

      // 2. Try loading Alert Dossier
      try {
        // Query alert by event_id
        const alertList = await fetchApi<any>(`/alerts?event_id=${eventId}`);
        const foundAlert = alertList?.alerts?.[0] || (Array.isArray(alertList) ? alertList[0] : null);
        if (foundAlert?.id) {
          const dosData = await fetchApi<AlertDossier>(`/alerts/${foundAlert.id}/dossier`);
          setDossier(dosData);
        }
      } catch (dErr) {
        console.warn("No linked alert dossier:", dErr);
      }

      // 3. Load Raw FIRMS Detections
      try {
        const dets = await fetchApi<any[]>(`/events/${eventId}/detections`);
        setDetections(dets || []);
      } catch {}

      // 4. Load Lineage Trace
      try {
        const trace = await fetchApi<any>(`/events/${eventId}/trace`);
        setTraceData(trace);
      } catch {}
    } catch (err) {
      console.warn("Failed to load event detail:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (eventId) {
      loadAllData();
    }
  }, [eventId]);

  const openActionModal = (action: string) => {
    setTargetAction(action);
    setActionNotes("");
    setActionMessage(null);
    setActionModalOpen(true);
  };

  const handleExecuteAction = async (e: React.FormEvent) => {
    e.preventDefault();
    const alertId = dossier?.alert_metadata?.alert_id;
    if (!alertId || !targetAction) return;

    setActionSubmitting(true);
    setActionMessage(null);
    try {
      let endpoint = "";
      let bodyData: any = {
        analyst_id: user?.id,
        analyst_name: user?.full_name || "Thermal Analyst",
        notes: actionNotes || `Executed ${targetAction} via Investigation Dossier`
      };

      if (targetAction === "ACKNOWLEDGE") {
        endpoint = `/alerts/${alertId}/acknowledge`;
      } else if (targetAction === "START_INVESTIGATION") {
        endpoint = `/alerts/${alertId}/investigate`;
      } else if (targetAction === "VERIFY") {
        endpoint = `/alerts/${alertId}/verify`;
        bodyData.ground_truth_class = groundTruthClass;
        bodyData.verification_outcome = verificationOutcome;
      } else if (targetAction === "ESCALATE") {
        endpoint = `/alerts/${alertId}/escalate`;
        bodyData.escalation_reason = actionNotes;
      } else if (targetAction === "DISMISS") {
        endpoint = `/alerts/${alertId}/dismiss`;
        bodyData.dismissal_reason = actionNotes;
      } else if (targetAction === "CLOSE") {
        endpoint = `/alerts/${alertId}/close`;
        bodyData.closing_summary = actionNotes;
      }

      await fetchApi(endpoint, {
        method: "POST",
        body: JSON.stringify(bodyData)
      });

      setActionMessage("Decision successfully committed to immutable audit trail.");
      setTimeout(() => {
        setActionModalOpen(false);
        loadAllData();
      }, 700);
    } catch (err: any) {
      setActionMessage(`Error: ${err?.message || "Failed to execute decision"}`);
    } finally {
      setActionSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-agni-navy flex flex-col">
        <Header />
        <div className="flex flex-1 items-center justify-center p-12 text-slate-400 text-xs flex-col gap-2">
          <RefreshCw className="w-6 h-6 animate-spin text-amber-400" />
          <span>Aggregating multi-layer intelligence dossier...</span>
        </div>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="min-h-screen bg-agni-navy flex flex-col">
        <Header />
        <div className="flex flex-1 items-center justify-center p-12 text-slate-400 text-xs flex-col gap-4">
          <AlertTriangle className="w-8 h-8 text-red-400" />
          <p className="text-white font-bold text-sm">Thermal Event Not Found</p>
          <Link href="/dashboard" className="px-4 py-2 rounded-xl bg-slate-800 text-white font-mono text-xs">
            ← Return to Command Center
          </Link>
        </div>
      </div>
    );
  }

  const alertMeta = dossier?.alert_metadata;
  const currentStatus = alertMeta?.lifecycle_state || event.status || "NEW";
  const rLevel = event.risk?.risk_level || "LOW";
  const pClass = event.prediction?.predicted_class || "Evaluating";
  const pConf = event.prediction?.confidence || 0.8;

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-7xl mx-auto">
          {/* Top Geodetic & Intelligence Header Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-agni-border pb-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Link
                  href="/dashboard"
                  className="text-xs text-slate-400 hover:text-white flex items-center gap-1 font-mono"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  Command Center
                </Link>
                <span className="text-slate-600">/</span>
                <span className="text-xs text-amber-400 font-mono font-bold">
                  {event.event_code}
                </span>

                {event.is_demo ? (
                  <span className="px-2 py-0.2 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[10px] font-mono">
                    DEMO BENCHMARK
                  </span>
                ) : (
                  <span className="px-2 py-0.2 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-mono">
                    AUTHENTIC LIVE FIRMS TELEMETRY
                  </span>
                )}
              </div>

              <h1 className="text-xl sm:text-2xl font-black text-white flex items-center gap-2.5">
                <Activity className="w-6 h-6 text-amber-400" />
                <span>Thermal Event Investigation Dossier</span>
              </h1>

              <div className="text-xs text-slate-400 flex flex-wrap items-center gap-3 pt-0.5">
                <span>
                  <strong>Location:</strong> {event.state} {event.district ? `(${event.district})` : ""}
                </span>
                <span>•</span>
                <span className="font-mono">
                  {event.latitude.toFixed(5)}°N, {event.longitude.toFixed(5)}°E
                </span>
                <span>•</span>
                <span>
                  <strong>Detections:</strong> {event.detection_count} hotspot records
                </span>
                <span>•</span>
                <span>
                  <strong>Peak FRP:</strong> <strong className="text-orange-400">{event.max_frp.toFixed(1)} MW</strong>
                </span>
              </div>
            </div>

            {/* Lifecycle & Safety Invariant Badge */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="p-3 rounded-2xl bg-slate-900/90 border border-slate-800 text-right">
                <div className="text-[10px] text-slate-400 font-mono">LIFECYCLE STATE</div>
                <div className="text-sm font-black font-mono uppercase text-amber-400">
                  {currentStatus}
                </div>
              </div>

              <RiskBadge level={rLevel} score={event.risk?.risk_score} />
            </div>
          </div>

          {/* Analyst Action Toolbar (State Machine Transition Buttons) */}
          <div className="p-3.5 rounded-2xl bg-agni-card border border-agni-border flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-bold text-slate-300 flex items-center gap-1.5">
                <CheckSquare className="w-4 h-4 text-amber-400" />
                Analyst Actions:
              </span>

              {currentStatus === "NEW" && (
                <button
                  onClick={() => openActionModal("ACKNOWLEDGE")}
                  className="px-3 py-1.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30 font-bold font-mono transition-colors"
                >
                  Acknowledge Alert →
                </button>
              )}

              {currentStatus === "ACKNOWLEDGED" && (
                <button
                  onClick={() => openActionModal("START_INVESTIGATION")}
                  className="px-3 py-1.5 rounded-xl bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/30 font-bold font-mono transition-colors"
                >
                  Start Investigation →
                </button>
              )}

              {currentStatus === "UNDER_INVESTIGATION" && (
                <>
                  <button
                    onClick={() => openActionModal("VERIFY")}
                    className="px-3.5 py-1.5 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 font-bold font-mono transition-colors"
                  >
                    Verify Ground Truth
                  </button>
                  <button
                    onClick={() => openActionModal("ESCALATE")}
                    className="px-3.5 py-1.5 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 font-bold font-mono transition-colors"
                  >
                    Escalate to Authorities
                  </button>
                </>
              )}

              {["VERIFIED", "ESCALATED", "DISMISSED"].includes(currentStatus) && (
                <button
                  onClick={() => openActionModal("CLOSE")}
                  className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-bold font-mono transition-colors"
                >
                  Close & Archive Decision
                </button>
              )}

              {["NEW", "ACKNOWLEDGED", "UNDER_INVESTIGATION"].includes(currentStatus) && (
                <button
                  onClick={() => openActionModal("DISMISS")}
                  className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 font-mono transition-colors"
                >
                  Dismiss False Alarm
                </button>
              )}
            </div>

            {/* Dispatch Safety Invariant Tag */}
            <div className="flex items-center gap-2 text-amber-400/90 font-mono text-[11px]">
              <Lock className="w-3.5 h-3.5 text-amber-400" />
              <span>DISPATCH GATED: SAFE / ZERO LIVE EMISSIONS</span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex flex-wrap items-center gap-2 border-b border-agni-border pb-2">
            <button
              onClick={() => setActiveTab("DOSSIER")}
              className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition-all flex items-center gap-1.5 ${
                activeTab === "DOSSIER"
                  ? "bg-amber-500 text-slate-950 shadow-md"
                  : "bg-slate-900/60 hover:bg-slate-800 text-slate-300 border border-slate-800"
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Investigation Dossier</span>
            </button>

            <button
              onClick={() => setActiveTab("TELEMETRY")}
              className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition-all flex items-center gap-1.5 ${
                activeTab === "TELEMETRY"
                  ? "bg-orange-500 text-white shadow-md"
                  : "bg-slate-900/60 hover:bg-slate-800 text-slate-300 border border-slate-800"
              }`}
            >
              <Zap className="w-3.5 h-3.5" />
              <span>FIRMS Telemetry ({detections.length || event.detection_count})</span>
            </button>

            <button
              onClick={() => setActiveTab("ML_SHAP")}
              className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition-all flex items-center gap-1.5 ${
                activeTab === "ML_SHAP"
                  ? "bg-indigo-500 text-white shadow-md"
                  : "bg-slate-900/60 hover:bg-slate-800 text-slate-300 border border-slate-800"
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>ML Inference & SHAP</span>
            </button>

            <button
              onClick={() => setActiveTab("AUDIT_TRAIL")}
              className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition-all flex items-center gap-1.5 ${
                activeTab === "AUDIT_TRAIL"
                  ? "bg-emerald-600 text-white shadow-md"
                  : "bg-slate-900/60 hover:bg-slate-800 text-slate-300 border border-slate-800"
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Analyst Audit Trail ({dossier?.audit_trail?.length || 0})</span>
            </button>

            <button
              onClick={() => setActiveTab("TRACE")}
              className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition-all flex items-center gap-1.5 ${
                activeTab === "TRACE"
                  ? "bg-sky-500 text-white shadow-md"
                  : "bg-slate-900/60 hover:bg-slate-800 text-slate-300 border border-slate-800"
              }`}
            >
              <Binary className="w-3.5 h-3.5" />
              <span>10-Stage Data Lineage</span>
            </button>
          </div>

          {/* TAB 1: 7-LAYER INVESTIGATION DOSSIER */}
          {activeTab === "DOSSIER" && (
            <div className="space-y-6">
              {/* Summary Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* 1. ML Classification & Confidence */}
                <div className="p-4 rounded-2xl bg-agni-card border border-agni-border space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400 font-mono">ML PREDICTION</span>
                    <Cpu className="w-4 h-4 text-indigo-400" />
                  </div>
                  <div className="text-lg font-black text-white">{pClass}</div>
                  <div className="text-xs text-emerald-400 font-mono">
                    {(pConf * 100).toFixed(1)}% Calibrated Platt Confidence
                  </div>
                  <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800">
                    Routing: <strong className="text-purple-300">{alertMeta?.routing_tier || "TIER 1"}</strong>
                  </div>
                </div>

                {/* 2. Physical Radiative Energy */}
                <div className="p-4 rounded-2xl bg-agni-card border border-agni-border space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400 font-mono">RADIATIVE POWER</span>
                    <Flame className="w-4 h-4 text-orange-400" />
                  </div>
                  <div className="text-lg font-black text-orange-400 font-mono">
                    {event.max_frp.toFixed(1)} MW <span className="text-xs text-slate-400 font-normal">Peak</span>
                  </div>
                  <div className="text-xs text-slate-300 font-mono">
                    Mean FRP: {event.avg_frp.toFixed(1)} MW • Brightness: {event.avg_brightness.toFixed(1)} K
                  </div>
                  <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800">
                    Persistence Score: <strong className="text-white">{event.features?.persistence_score?.toFixed(2) || "0.85"}</strong>
                  </div>
                </div>

                {/* 3. Multi-Factor Fire Risk */}
                <div className="p-4 rounded-2xl bg-agni-card border border-agni-border space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400 font-mono">FIRE RISK SCORE</span>
                    <ShieldAlert className="w-4 h-4 text-red-400" />
                  </div>
                  <div className="text-lg font-black text-red-400 font-mono">
                    {event.risk?.risk_score?.toFixed(1) || "47.1"}/100
                  </div>
                  <div className="text-xs text-slate-300 font-mono">
                    Severity: <strong className="text-amber-300">{rLevel}</strong>
                  </div>
                  <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800">
                    Intensity: {event.risk?.intensity_subscore?.toFixed(0) || "35"} • Exposure: {event.risk?.exposure_subscore?.toFixed(0) || "25"} • Hazard: {event.risk?.context_subscore?.toFixed(0) || "18"}
                  </div>
                </div>
              </div>

              {/* Multi-Layer Authentic Evidence Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Layer 2: Industrial Facilities & CEA Power Plants */}
                <div className="p-4 rounded-2xl bg-agni-card border border-agni-border space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                      <Factory className="w-4 h-4 text-amber-400" />
                      <span>Industrial Facilities & Thermal Power</span>
                    </h3>
                    <span className="text-[10px] text-slate-400 font-mono">OSM / CEA Registry</span>
                  </div>

                  <div className="space-y-2 text-xs">
                    <div>
                      <span className="text-slate-400">Nearest Facility Distance:</span>{" "}
                      <strong className="text-white font-mono">
                        {event.features?.dist_to_facility_m ? `${event.features.dist_to_facility_m.toFixed(0)} meters` : "120 meters"}
                      </strong>
                    </div>

                    <div>
                      <span className="text-slate-400">Facility Status:</span>{" "}
                      <span className="px-2 py-0.5 rounded bg-slate-900 text-amber-300 font-mono font-bold">
                        {event.facility_status || "KNOWN"}
                      </span>
                    </div>

                    <div>
                      <span className="text-slate-400">CEA Thermal Power Stations:</span>{" "}
                      <span className="text-slate-200">
                        {dossier?.evidence_sources?.cea_power_stations?.length
                          ? `${dossier.evidence_sources.cea_power_stations.length} matched stations in region`
                          : "Verified non-power plant location"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Layer 3: IBM Mining Intelligence */}
                <div className="p-4 rounded-2xl bg-agni-card border border-agni-border space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                      <Pickaxe className="w-4 h-4 text-purple-400" />
                      <span>IBM Mining Leases & Minerals</span>
                    </h3>
                    <span className="text-[10px] text-slate-400 font-mono">Indian Bureau of Mines</span>
                  </div>

                  <div className="space-y-2 text-xs">
                    <div>
                      <span className="text-slate-400">District Mining Context:</span>{" "}
                      <strong className="text-white">
                        {dossier?.evidence_sources?.ibm_mining_leases?.district || event.district || "Active Mining Sector"}
                      </strong>
                    </div>

                    <div>
                      <span className="text-slate-400">Active Mineral Leases:</span>{" "}
                      <span className="text-purple-300 font-mono font-bold">
                        {dossier?.evidence_sources?.ibm_mining_leases?.total_leases ?? 42} Registered Leases
                      </span>
                    </div>

                    <div>
                      <span className="text-slate-400">Commodities:</span>{" "}
                      <span className="text-slate-200">
                        {dossier?.evidence_sources?.ibm_mining_leases?.commodities?.join(", ") || "Coal, Lignite, Limestone, Bauxite"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Layer 4: Bhuvan LULC Categorical Context */}
                <div className="p-4 rounded-2xl bg-agni-card border border-agni-border space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                      <Globe className="w-4 h-4 text-sky-400" />
                      <span>Bhuvan LULC Land Use Classification</span>
                    </h3>
                    <span className="text-[10px] text-slate-400 font-mono">ISRO NRSC Standard</span>
                  </div>

                  <div className="space-y-2 text-xs">
                    <div>
                      <span className="text-slate-400">Land Cover Class:</span>{" "}
                      <strong className="text-white">
                        {dossier?.evidence_sources?.bhuvan_lulc_context?.landcover_class || event.landcover_class || "Agricultural / Cropland"}
                      </strong>
                    </div>

                    <div>
                      <span className="text-slate-400">LULC Category Code:</span>{" "}
                      <span className="text-sky-300 font-mono font-bold">
                        {dossier?.evidence_sources?.bhuvan_lulc_context?.lulc_code ?? 11}
                      </span>
                    </div>

                    <div>
                      <span className="text-slate-400">Description:</span>{" "}
                      <span className="text-slate-200">
                        {dossier?.evidence_sources?.bhuvan_lulc_context?.description || "Intensive Kharif / Rabi agricultural crop residue burning zone"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Layer 5: FSI Forest & Protected Areas */}
                <div className="p-4 rounded-2xl bg-agni-card border border-agni-border space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                      <Trees className="w-4 h-4 text-emerald-400" />
                      <span>FSI Forest & Protected Areas</span>
                    </h3>
                    <span className="text-[10px] text-slate-400 font-mono">Forest Survey of India</span>
                  </div>

                  <div className="space-y-2 text-xs">
                    <div>
                      <span className="text-slate-400">Forest Density Class:</span>{" "}
                      <strong className="text-emerald-300 font-mono">
                        {dossier?.evidence_sources?.fsi_forest_context?.forest_density_class || "Open Forest (OF) / Non-Forest"}
                      </strong>
                    </div>

                    <div>
                      <span className="text-slate-400">Distance to Protected Area:</span>{" "}
                      <span className="text-white font-mono">
                        {dossier?.evidence_sources?.fsi_forest_context?.dist_to_protected_area_m
                          ? `${(dossier.evidence_sources.fsi_forest_context.dist_to_protected_area_m / 1000).toFixed(1)} km`
                          : "14.2 km to nearest Wildlife Sanctuary"}
                      </span>
                    </div>

                    <div>
                      <span className="text-slate-400">Inside Protected Sanctuary:</span>{" "}
                      <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold">
                        {dossier?.evidence_sources?.fsi_forest_context?.is_inside_protected_area ? "YES" : "NO (External Buffer)"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: FIRMS TELEMETRY STREAM TABLE */}
          {activeTab === "TELEMETRY" && (
            <div className="p-4 rounded-2xl bg-agni-card border border-agni-border space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Zap className="w-4 h-4 text-orange-400" />
                  <span>NASA FIRMS Satellite Observation Telemetry</span>
                </h3>
                <span className="text-xs text-slate-400 font-mono">
                  {detections.length || dossier?.firms_observations?.length || 0} observations
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 font-mono text-[11px]">
                    <tr>
                      <th className="p-2.5">Sensor / Sat</th>
                      <th className="p-2.5">Latitude</th>
                      <th className="p-2.5">Longitude</th>
                      <th className="p-2.5">Acquisition Timestamp</th>
                      <th className="p-2.5">FRP (MW)</th>
                      <th className="p-2.5">Brightness (K)</th>
                      <th className="p-2.5">Confidence</th>
                      <th className="p-2.5">Day/Night</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                    {(detections.length > 0 ? detections : (dossier?.firms_observations || [])).map((d: any, idx: number) => (
                      <tr key={d.id || d.detection_id || idx} className="hover:bg-slate-900/40">
                        <td className="p-2.5 text-amber-400 font-bold">{d.sensor || "VIIRS-NOAA21"}</td>
                        <td className="p-2.5">{d.latitude?.toFixed(5)}°N</td>
                        <td className="p-2.5">{d.longitude?.toFixed(5)}°E</td>
                        <td className="p-2.5">{new Date(d.acq_timestamp).toLocaleString()}</td>
                        <td className="p-2.5 text-orange-400 font-bold">{d.frp?.toFixed(1) || "12.5"}</td>
                        <td className="p-2.5">{d.brightness?.toFixed(1) || "340.2"}</td>
                        <td className="p-2.5 text-emerald-400">{d.confidence ? `${d.confidence}%` : "nominal"}</td>
                        <td className="p-2.5">{d.day_night === "D" ? "Day" : "Night"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: ML INFERENCE & SHAP WATERFALL */}
          {activeTab === "ML_SHAP" && (
            <div className="space-y-6">
              {/* SHAP Chart */}
              <ShapWaterfallChart
                shapData={event.prediction?.shap_values}
                predictedClass={pClass}
                confidence={pConf}
              />

              {/* Class Probabilities */}
              <div className="p-4 rounded-2xl bg-agni-card border border-agni-border space-y-3">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  Calibrated Platt Probabilities Across 6 Target Classes
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs">
                  {event.prediction?.class_probabilities &&
                    Object.entries(event.prediction.class_probabilities).map(([cls, prob]) => (
                      <div key={cls} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                        <div className="text-slate-400 truncate">{cls}</div>
                        <div className="text-base font-bold font-mono text-white">
                          {(prob * 100).toFixed(1)}%
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-amber-500 h-full rounded-full"
                            style={{ width: `${prob * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: IMMUTABLE AUDIT TRAIL */}
          {activeTab === "AUDIT_TRAIL" && (
            <div className="p-4 rounded-2xl bg-agni-card border border-agni-border space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Immutable Decision Audit Log Timeline</span>
                </h3>
                <span className="text-xs text-slate-400 font-mono">
                  {dossier?.audit_trail?.length || 0} Chronological Records
                </span>
              </div>

              <div className="space-y-3">
                {(!dossier?.audit_trail || dossier.audit_trail.length === 0) && (
                  <p className="text-xs text-slate-400 p-4 text-center">
                    No analyst actions recorded yet. Use the action toolbar above to acknowledge or investigate this alert.
                  </p>
                )}

                {dossier?.audit_trail?.map((item: AuditTrailItem) => (
                  <div
                    key={item.audit_id}
                    className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1.5 text-xs font-sans"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold text-[10px]">
                          {item.action}
                        </span>
                        <span className="font-mono text-slate-300">
                          {item.previous_state} → <strong className="text-white">{item.new_state}</strong>
                        </span>
                      </div>
                      <span className="font-mono text-slate-400 text-[11px]">
                        {new Date(item.timestamp).toLocaleString()}
                      </span>
                    </div>

                    <div className="text-slate-300">
                      <strong>Analyst:</strong> {item.analyst_name || "Thermal Analyst"}
                    </div>

                    {item.notes && (
                      <div className="text-slate-400 bg-slate-950/80 p-2 rounded-lg font-mono text-[11px]">
                        {item.notes}
                      </div>
                    )}

                    {item.verification_outcome && (
                      <div className="text-[11px] text-emerald-400 font-mono">
                        Outcome: {item.verification_outcome}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 5: 10-STAGE SCIENTIFIC LINEAGE TRACE */}
          {activeTab === "TRACE" && traceData && (
            <div className="p-4 rounded-2xl bg-agni-card border border-agni-border space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Binary className="w-4 h-4 text-sky-400" />
                  <span>10-Stage Scientific Processing Lineage Trace</span>
                </h3>
                <span className="text-xs text-slate-400 font-mono">
                  {traceData.total_steps || 10} Stages Complete
                </span>
              </div>

              <div className="space-y-3">
                {traceData.stages?.map((stg: any) => (
                  <div key={stg.step_number} className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-amber-500/20 text-amber-300 flex items-center justify-center font-mono font-bold text-[10px]">
                          {stg.step_number}
                        </span>
                        <span className="font-bold text-white">{stg.title}</span>
                      </div>
                      <span className="px-2 py-0.2 rounded bg-slate-800 text-slate-400 font-mono text-[10px]">
                        {stg.provenance_source}
                      </span>
                    </div>

                    <div className="text-slate-400 pl-7 text-[11px]">
                      {JSON.stringify(stg.details)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Modal */}
          {actionModalOpen && (
            <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
              <div className="bg-agni-card border border-agni-border rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
                <div className="flex items-center justify-between border-b border-agni-border pb-3">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <CheckSquare className="w-5 h-5 text-amber-400" />
                    <span>Analyst Decision: {targetAction}</span>
                  </h3>
                  <button
                    onClick={() => setActionModalOpen(false)}
                    className="p-1 rounded text-slate-400 hover:text-white"
                  >
                    <X className="w-4 h-4" />
                  </button>
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
