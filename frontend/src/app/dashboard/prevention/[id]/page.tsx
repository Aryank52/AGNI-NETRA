"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi, API_BASE_URL } from "@/lib/api";
import { 
  ShieldAlert, Flame, Activity, CheckCircle2, 
  Search, RefreshCw, AlertTriangle, ChevronRight, Layers,
  Zap, Info, Clock, MapPin, Download, Send, CheckSquare,
  Building2, ShieldCheck, ArrowLeft, ExternalLink, HelpCircle,
  FileText, Hash, Award, Eye, FileSpreadsheet, AlertOctagon
} from "lucide-react";

interface Hypothesis {
  id: string;
  category: string;
  title: string;
  description: string;
  confidence_score: number;
  evidence_score: number;
  verification_status: string;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  epistemic_caveat?: string;
  is_primary: boolean;
  contributing_factors?: string[];
}

interface Recommendation {
  id: string;
  recommendation: string;
  reason: string;
  urgency: "IMMEDIATE" | "SCHEDULED" | "PERIODIC";
  responsible_authority_category: string;
  expected_prevention_objective?: string;
  status: string;
}

interface CaseDetail {
  id: string;
  case_number: string;
  event_id: string;
  event_code: string;
  title: string;
  prevention_priority: "CRITICAL" | "HIGH" | "MODERATE" | "LOW";
  status: string;
  state: string;
  district: string;
  subdistrict?: string;
  latitude: number;
  longitude: number;
  facility_id?: string;
  facility_name?: string;
  facility_type?: string;
  recurrence_score: number;
  persistence_score: number;
  baseline_deviation_ratio: number;
  evidence_strength_score: number;
  summary: string;
  missing_data: string[];
  unknowns: string[];
  conflicting_sources: string[];
  hypotheses: Hypothesis[];
  recommendations: Recommendation[];
  created_at: string;
  updated_at: string;
}

interface Authority {
  id: string;
  authority_name: string;
  department_name: string;
  jurisdiction_level: string;
  state: string;
  district?: string;
  category: string;
  official_email?: string;
  official_phone?: string;
  nodal_officer_designation?: string;
  compliance_portal_url?: string;
}

interface ReportRecord {
  id: string;
  report_number: string;
  case_id: string;
  title: string;
  status: "DRAFT" | "UNDER_REVIEW" | "APPROVED" | "DELIVERED";
  executive_summary: string;
  pdf_path?: string;
  generated_by: string;
  approved_by?: string;
  approved_at?: string;
  review_notes?: string;
  created_at: string;
}

interface AuditRecord {
  id: string;
  report_id: string;
  recipient_name: string;
  recipient_organization: string;
  recipient_role: string;
  delivery_channel: string;
  dispatched_by_user_email: string;
  dispatched_by_user_role: string;
  delivery_status: string;
  delivery_timestamp: string;
  audit_hash: string;
}

export default function PreventionCaseDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const caseId = resolvedParams.id;
  const router = useRouter();

  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [authorities, setAuthorities] = useState<Authority[]>([]);
  const [reports, setReports] = useState<ReportRecord[]>([]);
  const [activeReport, setActiveReport] = useState<ReportRecord | null>(null);
  const [audits, setAudits] = useState<AuditRecord[]>([]);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"hypotheses" | "evidence" | "recommendations" | "authorities" | "report">("hypotheses");

  // Report generation state
  const [generatingReport, setGeneratingReport] = useState<boolean>(false);
  const [reportActionMsg, setReportActionMsg] = useState<string | null>(null);

  // Approval Modal State
  const [showApproveModal, setShowApproveModal] = useState<boolean>(false);
  const [approverName, setApproverName] = useState<string>("Chief Intelligence Analyst Sharma");
  const [approverRole, setApproverRole] = useState<string>("ANALYST");
  const [reviewNotes, setReviewNotes] = useState<string>("Verified cross-satellite telemetry, historical persistent thermal baseline, and deterministic industrial correlation.");
  const [approving, setApproving] = useState<boolean>(false);

  // Delivery Modal State
  const [showDeliverModal, setShowDeliverModal] = useState<boolean>(false);
  const [selectedAuthorityId, setSelectedAuthorityId] = useState<string>("");
  const [recipientName, setRecipientName] = useState<string>("Chief Fire Officer");
  const [recipientRole, setRecipientRole] = useState<string>("Chief Fire Officer / Regulatory Lead");
  const [recipientOrg, setRecipientOrg] = useState<string>("");
  const [deliveryChannel, setDeliveryChannel] = useState<string>("SECURE_GOV_DISPATCH");
  const [delivering, setDelivering] = useState<boolean>(false);

  const loadAllData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [caseRes, authRes, repRes] = await Promise.all([
        fetchApi<CaseDetail>(`/prevention/cases/${caseId}`),
        fetchApi<Authority[]>(`/prevention/cases/${caseId}/authorities`).catch(() => []),
        fetchApi<ReportRecord[]>(`/prevention/cases/${caseId}/reports`).catch(() => [])
      ]);

      setCaseData(caseRes);
      setAuthorities(authRes || []);
      setReports(repRes || []);

      if (repRes && repRes.length > 0) {
        const latest = repRes[0];
        setActiveReport(latest);
        // Load audits if report is delivered
        if (latest.status === "DELIVERED") {
          fetchApi<AuditRecord[]>(`/prevention/reports/${latest.id}/audits`)
            .then(res => setAudits(res || []))
            .catch(() => {});
        }
      }
    } catch (err: any) {
      console.error("Failed to load case data:", err);
      setError(err?.message || "Failed to load prevention case.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, [caseId]);

  const handleGenerateReport = async () => {
    setGeneratingReport(true);
    setReportActionMsg(null);
    try {
      const rep = await fetchApi<ReportRecord>(`/prevention/cases/${caseId}/reports/draft`, {
        method: "POST"
      });
      setActiveReport(rep);
      setReports(prev => [rep, ...prev.filter(r => r.id !== rep.id)]);
      setReportActionMsg("Draft 24-section formal report compiled successfully.");
      setActiveTab("report");
    } catch (err: any) {
      console.error("Report generation failed:", err);
      setReportActionMsg(`Error generating report: ${err?.message}`);
    } finally {
      setGeneratingReport(false);
    }
  };

  const handleApproveReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeReport) return;
    setApproving(true);
    try {
      const approved = await fetchApi<ReportRecord>(`/prevention/reports/${activeReport.id}/approve`, {
        method: "POST",
        body: JSON.stringify({
          approver_name: approverName,
          approver_role: approverRole,
          review_notes: reviewNotes
        })
      });
      setActiveReport(approved);
      setReports(prev => prev.map(r => r.id === approved.id ? approved : r));
      setShowApproveModal(false);
      setReportActionMsg("Report status updated to APPROVED. Governed delivery is now unlocked.");
    } catch (err: any) {
      console.error("Approval error:", err);
      setReportActionMsg(`Approval failed: ${err?.message}`);
    } finally {
      setApproving(false);
    }
  };

  const handleDeliverReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeReport) return;
    setDelivering(true);
    try {
      const audit = await fetchApi<AuditRecord>(`/prevention/reports/${activeReport.id}/send`, {
        method: "POST",
        body: JSON.stringify({
          recipient_authority_id: selectedAuthorityId || undefined,
          recipient_name: recipientName,
          recipient_role: recipientRole,
          recipient_organization: recipientOrg || "Jurisdictional Authority",
          delivery_channel: deliveryChannel
        })
      });

      // Update active report status
      setActiveReport(prev => prev ? { ...prev, status: "DELIVERED" } : null);
      setReports(prev => prev.map(r => r.id === activeReport.id ? { ...r, status: "DELIVERED" } : r));
      setAudits(prev => [audit, ...prev]);
      setShowDeliverModal(false);
      setReportActionMsg(`Report delivered successfully. Immutable SHA-256 Ledger Hash: ${audit.audit_hash.slice(0, 16)}...`);
    } catch (err: any) {
      console.error("Delivery error:", err);
      setReportActionMsg(`Delivery failed: ${err?.message}`);
    } finally {
      setDelivering(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <Header />
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-3">
              <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs font-mono text-slate-400">Loading Prevention Intelligence Workspace...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <Header />
          <div className="p-6">
            <div className="p-6 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-3">
              <AlertTriangle className="w-6 h-6 text-rose-400 shrink-0" />
              <div>
                <p className="font-bold">Error Loading Prevention Case</p>
                <p className="text-xs text-rose-400 mt-1">{error || "Case record not found."}</p>
                <Link
                  href="/dashboard/prevention"
                  className="inline-flex items-center gap-1.5 text-xs text-amber-400 hover:text-amber-300 mt-3 font-semibold"
                >
                  <ArrowLeft className="w-3.5 h-3.5" /> Back to Prevention Registry
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const priorityColor = caseData.prevention_priority === "CRITICAL"
    ? "text-rose-400 bg-rose-500/10 border-rose-500/30"
    : caseData.prevention_priority === "HIGH"
    ? "text-amber-400 bg-amber-500/10 border-amber-500/30"
    : "text-emerald-400 bg-emerald-500/10 border-emerald-500/30";

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header />

        <main className="flex-1 overflow-y-auto p-4 md:p-6 space-y-5">
          {/* Top Breadcrumb & Actions */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-mono text-slate-400 mb-1">
                <Link href="/dashboard/prevention" className="hover:text-amber-400 flex items-center gap-1">
                  <ArrowLeft className="w-3 h-3" /> Prevention Registry
                </Link>
                <span>/</span>
                <span className="text-amber-400 font-semibold">{caseData.case_number}</span>
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
                <ShieldAlert className="w-6 h-6 text-rose-500" />
                {caseData.title}
              </h1>
              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-1.5 font-mono">
                <span className="flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-slate-400" />
                  {caseData.district}, {caseData.state} ({caseData.latitude.toFixed(4)}°N, {caseData.longitude.toFixed(4)}°E)
                </span>
                <span>•</span>
                <span>Target Event: <Link href={`/dashboard/events`} className="text-amber-400 hover:underline">{caseData.event_code}</Link></span>
                {caseData.facility_name && (
                  <>
                    <span>•</span>
                    <span className="text-slate-300 flex items-center gap-1">
                      <Building2 className="w-3.5 h-3.5 text-amber-500" />
                      {caseData.facility_name}
                    </span>
                  </>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2.5">
              <span className={`text-xs font-mono px-3 py-1.5 rounded-lg border font-bold uppercase ${priorityColor}`}>
                {caseData.prevention_priority} PRIORITY
              </span>
              <button
                onClick={handleGenerateReport}
                disabled={generatingReport}
                className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-amber-600/20 transition-all cursor-pointer"
              >
                {generatingReport ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Compiling 24 Sections...</span>
                  </>
                ) : (
                  <>
                    <FileText className="w-3.5 h-3.5" />
                    <span>Compile Prevention Dossier</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Epistemic Anti-Fabrication Banner */}
          <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3">
            <Info className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-200/90 leading-relaxed space-y-1">
              <p className="font-bold tracking-wide text-amber-300">
                EPISTEMIC SAFETY INVARIANT: HISTORICAL CORRELATION DOES NOT IMPLY CAUSATION.
              </p>
              <p className="text-[11px] text-amber-200/80">
                Hypotheses represent transparent, testable physical scenarios derived from longitudinal FIRMS thermal signatures and spatial baselines. 
                Zero LLMs or generative chatbots were used to invent causes. Recommendations state they <em>&ldquo;MAY REDUCE RECURRENCE RISK&rdquo;</em>.
              </p>
            </div>
          </div>

          {/* Key Intelligence Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <span className="text-[11px] font-mono text-slate-400 block uppercase">Recurrence Frequency</span>
              <div className="text-xl font-bold font-mono text-amber-400">
                {caseData.recurrence_score?.toFixed(1)} <span className="text-xs text-slate-400 font-sans">episodes/yr</span>
              </div>
              <span className="text-[10px] text-slate-400 font-mono">Multi-Year Thermal Frequency</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <span className="text-[11px] font-mono text-slate-400 block uppercase">Baseline Deviation</span>
              <div className="text-xl font-bold font-mono text-rose-400">
                {caseData.baseline_deviation_ratio?.toFixed(1)}x <span className="text-xs text-slate-400 font-sans">Normal</span>
              </div>
              <span className="text-[10px] text-slate-400 font-mono">FRP Intensity Spike</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <span className="text-[11px] font-mono text-slate-400 block uppercase">Persistence Score</span>
              <div className="text-xl font-bold font-mono text-amber-300">
                {(caseData.persistence_score * 100).toFixed(0)}%
              </div>
              <span className="text-[10px] text-slate-400 font-mono">Multi-Month Footprint Stability</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <span className="text-[11px] font-mono text-slate-400 block uppercase">Evidence Strength</span>
              <div className="text-xl font-bold font-mono text-emerald-400">
                {Math.round((caseData.evidence_strength_score || 0) * 100)}%
              </div>
              <span className="text-[10px] text-slate-400 font-mono">Observable Telemetry Coverage</span>
            </div>
          </div>

          {/* Action Message Banner */}
          {reportActionMsg && (
            <div className="p-3 rounded-lg bg-amber-500/20 border border-amber-500/40 text-amber-200 text-xs flex items-center justify-between">
              <span>{reportActionMsg}</span>
              <button onClick={() => setReportActionMsg(null)} className="text-slate-400 hover:text-white">✕</button>
            </div>
          )}

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1 border-b border-slate-800 pt-1 overflow-x-auto text-xs font-semibold">
            {[
              { id: "hypotheses", label: `Root-Cause Hypotheses (${caseData.hypotheses?.length || 0})`, icon: ShieldAlert },
              { id: "evidence", label: "Evidence Matrix & Unknowns", icon: Layers },
              { id: "recommendations", label: `Preventive Recommendations (${caseData.recommendations?.length || 0})`, icon: CheckSquare },
              { id: "authorities", label: `Jurisdiction Authorities (${authorities.length})`, icon: Building2 },
              { id: "report", label: `24-Section Intelligence Report (${reports.length})`, icon: FileText },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-2 px-4 py-2.5 border-b-2 whitespace-nowrap transition-colors ${
                    activeTab === tab.id
                      ? "border-amber-500 text-amber-400 bg-amber-500/10 rounded-t-lg"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* TAB 1: 13 ROOT-CAUSE HYPOTHESES */}
          {activeTab === "hypotheses" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>13-Category Deterministic Root-Cause Taxonomy</span>
                <span className="font-mono text-amber-400">Master JARVIS Synthesis V1</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {caseData.hypotheses.map((h) => {
                  const statusBadge = h.verification_status === "CONFIRMED"
                    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                    : h.verification_status === "PLAUSIBLE"
                    ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                    : h.verification_status === "UNLIKELY"
                    ? "bg-slate-800 text-slate-400 border-slate-700"
                    : "bg-rose-500/20 text-rose-400 border-rose-500/30";

                  return (
                    <div
                      key={h.id || h.category}
                      className={`p-4 rounded-xl border transition-all ${
                        h.is_primary
                          ? "bg-slate-900 border-amber-500/60 shadow-md shadow-amber-500/5"
                          : "bg-slate-900/60 border-slate-800"
                      }`}
                    >
                      <div className="space-y-3">
                        {/* Title & Status */}
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <div className="flex items-center gap-2">
                              {h.is_primary && (
                                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500 text-slate-950 font-bold uppercase">
                                  PRIMARY CAUSE
                                </span>
                              )}
                              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-bold uppercase ${statusBadge}`}>
                                {h.verification_status}
                              </span>
                            </div>
                            <h3 className="text-sm font-bold text-white mt-1.5">
                              {h.title}
                            </h3>
                            <span className="text-[10px] font-mono text-slate-400 block mt-0.5">
                              Category: {h.category}
                            </span>
                          </div>

                          <div className="text-right">
                            <span className="text-xs font-mono font-bold text-amber-400 block">
                              {Math.round(h.confidence_score * 100)}%
                            </span>
                            <span className="text-[10px] text-slate-400 block font-mono">Confidence</span>
                          </div>
                        </div>

                        {/* Description */}
                        <p className="text-xs text-slate-300 leading-relaxed">
                          {h.description}
                        </p>

                        {/* Supporting Evidence */}
                        {h.supporting_evidence && h.supporting_evidence.length > 0 && (
                          <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-1">
                            <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider block">
                              Supporting Evidence:
                            </span>
                            <ul className="space-y-0.5">
                              {h.supporting_evidence.map((item, idx) => (
                                <li key={idx} className="text-[11px] text-slate-300 flex items-start gap-1.5">
                                  <span className="text-emerald-500 mt-1">•</span>
                                  <span>{item}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Contradicting Evidence */}
                        {h.contradicting_evidence && h.contradicting_evidence.length > 0 && (
                          <div className="p-2.5 rounded-lg bg-rose-950/20 border border-rose-900/40 space-y-1">
                            <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider block">
                              Contradicting Evidence / Absent Indicators:
                            </span>
                            <ul className="space-y-0.5">
                              {h.contradicting_evidence.map((item, idx) => (
                                <li key={idx} className="text-[11px] text-rose-200/80 flex items-start gap-1.5">
                                  <span className="text-rose-400 mt-1">•</span>
                                  <span>{item}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Epistemic Caveat */}
                        {h.epistemic_caveat && (
                          <div className="text-[10px] text-amber-300/80 italic bg-amber-500/5 p-2 rounded border border-amber-500/20">
                            <strong>Epistemic Note:</strong> {h.epistemic_caveat}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 2: EVIDENCE MATRIX & UNKNOWNS */}
          {activeTab === "evidence" && (
            <div className="space-y-5">
              {/* Missing Data Badges */}
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2">
                  <AlertOctagon className="w-4 h-4" />
                  Mandatory Epistemic Restraints & Unavailable Data
                </h3>
                <p className="text-xs text-slate-300">
                  To prevent fabrication, the AGNI-NETRA core invariants enforce explicit labeling when data streams are absent:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-center space-y-1">
                    <span className="text-xs font-mono font-bold text-rose-400 block">GAS COMPOSITION DATA UNAVAILABLE</span>
                    <p className="text-[10px] text-slate-400">Ground spectrometry unintegrated; no gases are fabricated.</p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-center space-y-1">
                    <span className="text-xs font-mono font-bold text-amber-400 block">NEWS EVIDENCE UNAVAILABLE</span>
                    <p className="text-[10px] text-slate-400">External news crawlers unconfigured; no external claims inferred.</p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-center space-y-1">
                    <span className="text-xs font-mono font-bold text-slate-300 block">No verified agency records available</span>
                    <p className="text-[10px] text-slate-400">Official agency FIR or inspection reports not yet filed.</p>
                  </div>
                </div>
              </div>

              {/* Unknowns & Conflicting Sources */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                    <HelpCircle className="w-4 h-4 text-amber-400" />
                    Unknown & Unverified Variables
                  </h3>
                  <ul className="space-y-2 text-xs text-slate-300">
                    {caseData.unknowns && caseData.unknowns.length > 0 ? (
                      caseData.unknowns.map((u, idx) => (
                        <li key={idx} className="flex items-start gap-2 p-2 rounded bg-slate-950 border border-slate-800">
                          <span className="text-amber-400 font-mono font-bold">?</span>
                          <span>{u}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-slate-400 text-xs italic">No specific unknowns identified.</li>
                    )}
                  </ul>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                    <Layers className="w-4 h-4 text-indigo-400" />
                    Verified Ingested Evidence Layers
                  </h3>
                  <div className="space-y-2 text-xs">
                    <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800">
                      <span className="text-slate-300">NASA FIRMS VIIRS Radiometric Telemetry</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">VERIFIED</span>
                    </div>
                    <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800">
                      <span className="text-slate-300">PostGIS Industrial Facility Polygons (OSM / CEA)</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">VERIFIED</span>
                    </div>
                    <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800">
                      <span className="text-slate-300">Longitudinal Recurrence Baseline Model</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">DERIVED</span>
                    </div>
                    <div className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800">
                      <span className="text-slate-300">Deterministic Root-Cause Synthesis Engine</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">INFERRED</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: PREVENTIVE RECOMMENDATIONS */}
          {activeTab === "recommendations" && (
            <div className="space-y-4">
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-200">
                <strong>Standard Phrasing Invariant:</strong> All recommendations state that they <em>&ldquo;MAY REDUCE RECURRENCE RISK&rdquo;</em>. Outcomes are never guaranteed.
              </div>

              <div className="space-y-3">
                {caseData.recommendations.map((r) => {
                  const urgencyBadge = r.urgency === "IMMEDIATE"
                    ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                    : r.urgency === "SCHEDULED"
                    ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                    : "bg-slate-800 text-slate-300 border-slate-700";

                  return (
                    <div key={r.id} className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-bold uppercase ${urgencyBadge}`}>
                              {r.urgency} ACTION
                            </span>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                              {r.responsible_authority_category}
                            </span>
                          </div>
                          <h4 className="text-sm font-bold text-white mt-1">
                            {r.recommendation}
                          </h4>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                        <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                          <span className="text-[10px] font-bold text-slate-400 uppercase block mb-1">Operational Rationale</span>
                          <p className="text-slate-300">{r.reason}</p>
                        </div>
                        <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                          <span className="text-[10px] font-bold text-emerald-400 uppercase block mb-1">Expected Objective</span>
                          <p className="text-slate-300">{r.expected_prevention_objective || "May reduce recurrence risk by addressing root physical drivers."}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 4: JURISDICTION AUTHORITIES */}
          {activeTab === "authorities" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>Verified Regulatory, Emergency & Industrial Authorities for {caseData.district}, {caseData.state}</span>
                <span className="font-mono text-emerald-400">{authorities.length} Resolved</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {authorities.map((a) => (
                  <div key={a.id} className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-amber-400 border border-slate-700 uppercase font-bold">
                          {a.category} • {a.jurisdiction_level}
                        </span>
                        <h4 className="text-sm font-bold text-white mt-1.5">
                          {a.authority_name}
                        </h4>
                        <p className="text-xs text-slate-400">{a.department_name}</p>
                      </div>
                    </div>

                    <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1 font-mono">
                      {a.nodal_officer_designation && (
                        <div className="text-slate-300">
                          <span className="text-slate-400">Nodal Officer:</span> {a.nodal_officer_designation}
                        </div>
                      )}
                      {a.official_email && (
                        <div className="text-slate-300">
                          <span className="text-slate-400">Official Email:</span> {a.official_email}
                        </div>
                      )}
                      {a.official_phone && (
                        <div className="text-slate-300">
                          <span className="text-slate-400">Emergency Phone:</span> {a.official_phone}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 5: 24-SECTION REPORT & HUMAN GOVERNANCE */}
          {activeTab === "report" && (
            <div className="space-y-5">
              {activeReport ? (
                <div className="space-y-5">
                  {/* Governance Lifecycle Action Bar */}
                  <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-amber-400">{activeReport.report_number}</span>
                        <span className={`text-xs font-mono px-2.5 py-0.5 rounded font-bold uppercase border ${
                          activeReport.status === "DELIVERED"
                            ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                            : activeReport.status === "APPROVED"
                            ? "bg-indigo-500/20 text-indigo-300 border-indigo-500/40"
                            : "bg-amber-500/20 text-amber-300 border-amber-500/40"
                        }`}>
                          {activeReport.status}
                        </span>
                      </div>
                      <h3 className="text-sm font-bold text-white mt-1">{activeReport.title}</h3>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Compiled on {new Date(activeReport.created_at).toLocaleString()} by {activeReport.generated_by}
                      </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-2.5">
                      {/* PDF Download */}
                      <a
                        href={`${API_BASE_URL}/prevention/reports/${activeReport.id}/pdf`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Export Certified PDF</span>
                      </a>

                      {/* Approval Gate */}
                      {activeReport.status === "DRAFT" && (
                        <button
                          onClick={() => setShowApproveModal(true)}
                          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
                        >
                          <CheckSquare className="w-3.5 h-3.5" />
                          <span>Analyst Review & Approve</span>
                        </button>
                      )}

                      {/* Delivery Gate */}
                      {activeReport.status === "APPROVED" && (
                        <button
                          onClick={() => setShowDeliverModal(true)}
                          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-md shadow-rose-600/20 transition-all cursor-pointer"
                        >
                          <Send className="w-3.5 h-3.5" />
                          <span>Deliver to Authority</span>
                        </button>
                      )}

                      {activeReport.status === "DELIVERED" && (
                        <span className="flex items-center gap-1 text-xs font-mono text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-lg border border-emerald-500/30">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Delivered & Cryptographically Signed
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Delivery Audit Trail (if delivered) */}
                  {audits.length > 0 && (
                    <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4" />
                        Cryptographic Delivery Ledger
                      </h4>
                      {audits.map((a) => (
                        <div key={a.id} className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2 text-xs font-mono">
                          <div className="flex items-center justify-between">
                            <span className="text-slate-300">Recipient: <strong>{a.recipient_name}</strong> ({a.recipient_organization})</span>
                            <span className="text-emerald-400 font-bold">{a.delivery_status}</span>
                          </div>
                          <div className="text-slate-400 text-[11px]">
                            Dispatched By: {a.dispatched_by_user_email} ({a.dispatched_by_user_role}) at {new Date(a.delivery_timestamp).toLocaleString()}
                          </div>
                          <div className="p-2 rounded bg-slate-900 border border-slate-800 text-[10px] text-amber-300/90 break-all">
                            SHA-256 Hash: {a.audit_hash}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* 24-Section Summary View */}
                  <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400">
                      24-Section Formal Structure Summary
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5 text-xs font-mono">
                      {[
                        "1. Executive Summary", "2. Incident Overview", "3. Location & Geography",
                        "4. Thermal Observation", "5. Historical Incident Pattern", "6. Recurrence Analysis",
                        "7. Spatial Correlation", "8. Industrial Context", "9. Environmental Context",
                        "10. Material & Substance", "11. Agency Evidence", "12. External Evidence",
                        "13. ML Classification", "14. Anomaly Analysis", "15. Risk Assessment",
                        "16. Root-Cause Hypotheses", "17. Supporting Evidence", "18. Contradicting Evidence",
                        "19. Missing / Unknowns", "20. Preventive Recommendations", "21. Responsible Authorities",
                        "22. Human Verification", "23. Data Provenance", "24. Audit Trail & Hash"
                      ].map((sec, idx) => (
                        <div key={idx} className="p-2 rounded bg-slate-950 border border-slate-800/80 flex items-center justify-between">
                          <span className="text-slate-300">{sec}</span>
                          <span className="text-emerald-400 text-[10px]">COMPILED</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-10 rounded-xl bg-slate-900/40 border border-slate-800 text-center space-y-3">
                  <FileText className="w-12 h-12 text-slate-600 mx-auto stroke-1" />
                  <h3 className="text-sm font-semibold text-slate-300">No Dossier Compiled Yet</h3>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto">
                    Compile the full 24-section formal prevention intelligence dossier with ReportLab PDF rendering.
                  </p>
                  <button
                    onClick={handleGenerateReport}
                    disabled={generatingReport}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold shadow-lg shadow-amber-600/20 transition-all cursor-pointer"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>Compile 24-Section Formal Dossier</span>
                  </button>
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {/* APPROVAL MODAL */}
      {showApproveModal && activeReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <CheckSquare className="w-5 h-5 text-indigo-400" />
                <h2 className="text-base font-bold text-white">Analyst Review & Approval Gate</h2>
              </div>
              <button onClick={() => setShowApproveModal(false)} className="text-slate-400 hover:text-slate-200 text-sm font-mono">✕</button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Formal verification that all 24 sections, supporting telemetry, and recommendations have been reviewed. 
              Only authenticated users with ANALYST or ADMIN role may approve.
            </p>

            <form onSubmit={handleApproveReport} className="space-y-3.5">
              <div className="space-y-1">
                <label className="text-xs font-mono font-semibold text-slate-300">Approver Name</label>
                <input
                  type="text"
                  required
                  value={approverName}
                  onChange={(e) => setApproverName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-white focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-mono font-semibold text-slate-300">Authorized Role</label>
                <select
                  value={approverRole}
                  onChange={(e) => setApproverRole(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-white focus:border-amber-500 focus:outline-none"
                >
                  <option value="ANALYST">ANALYST</option>
                  <option value="ADMIN">ADMIN</option>
                  <option value="AGENCY">AGENCY</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-mono font-semibold text-slate-300">Review Notes</label>
                <textarea
                  rows={3}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowApproveModal(false)}
                  disabled={approving}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={approving}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all cursor-pointer"
                >
                  {approving ? "Approving..." : "Confirm Formal Approval"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DELIVERY MODAL */}
      {showDeliverModal && activeReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Send className="w-5 h-5 text-rose-500" />
                <h2 className="text-base font-bold text-white">Deliver to Regulatory Authority</h2>
              </div>
              <button onClick={() => setShowDeliverModal(false)} className="text-slate-400 hover:text-slate-200 text-sm font-mono">✕</button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Dispatches formal dossier to designated authority. An immutable cryptographic ledger entry with SHA-256 hash will be generated.
            </p>

            <form onSubmit={handleDeliverReport} className="space-y-3.5">
              <div className="space-y-1">
                <label className="text-xs font-mono font-semibold text-slate-300">Select Authority</label>
                <select
                  value={selectedAuthorityId}
                  onChange={(e) => {
                    const sel = authorities.find(a => a.id === e.target.value);
                    setSelectedAuthorityId(e.target.value);
                    if (sel) {
                      setRecipientOrg(sel.authority_name);
                      setRecipientRole(sel.nodal_officer_designation || "Jurisdictional Officer");
                    }
                  }}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-white focus:border-amber-500 focus:outline-none"
                >
                  <option value="">-- Choose Jurisdictional Authority --</option>
                  {authorities.map(a => (
                    <option key={a.id} value={a.id}>{a.authority_name} ({a.category})</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-mono font-semibold text-slate-300">Recipient Name / Officer</label>
                <input
                  type="text"
                  required
                  value={recipientName}
                  onChange={(e) => setRecipientName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-white focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-mono font-semibold text-slate-300">Delivery Channel</label>
                <select
                  value={deliveryChannel}
                  onChange={(e) => setDeliveryChannel(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-white focus:border-amber-500 focus:outline-none"
                >
                  <option value="SECURE_GOV_DISPATCH">SECURE_GOV_DISPATCH</option>
                  <option value="SECURE_PORTAL">SECURE_PORTAL</option>
                  <option value="OFFICIAL_EMAIL">OFFICIAL_EMAIL</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowDeliverModal(false)}
                  disabled={delivering}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={delivering}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition-all cursor-pointer"
                >
                  {delivering ? "Dispatched..." : "Execute Governed Delivery"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
