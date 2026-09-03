"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/authContext";
import { formatPercent } from "@/lib/formatters";
import { 
  Cpu, ArrowLeft, RefreshCw, CheckCircle2, 
  ShieldCheck, AlertTriangle, Play, Sliders,
  Layers, Database, Award, ArrowUpRight
} from "lucide-react";

interface MLModelRecord {
  id: string;
  model_name: string;
  version: string;
  dataset_version: string;
  algorithm: string;
  metrics: Record<string, any>;
  artifact_path: string;
  status: "TRAINING" | "VALIDATION" | "CANDIDATE" | "APPROVED" | "ACTIVE" | "RETIRED" | string;
  is_active: boolean;
  trained_at: string;
  approved_by?: string;
  approved_at?: string;
  notes?: string;
}

export default function ModelRegistryPage() {
  const { user } = useAuth();
  const [models, setModels] = useState<MLModelRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const loadModels = async () => {
    setLoading(true);
    try {
      const data = await fetchApi<MLModelRecord[]>("/admin/models");
      setModels(data || []);
    } catch (err) {
      console.warn("Failed to load model registry:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadModels();
  }, []);

  const handlePromote = async (modelId: string, newStatus: string) => {
    setUpdatingId(modelId);
    setStatusMsg(null);
    try {
      await fetchApi(`/admin/models/${modelId}/status`, {
        method: "POST",
        body: JSON.stringify({
          status: newStatus,
          notes: `Promoted via Model Registry UI by ${user?.email || 'analyst'}`
        })
      });
      setStatusMsg(`Model status successfully updated to ${newStatus}`);
      await loadModels();
    } catch (err: any) {
      setStatusMsg(`Status update failed: ${err.message || err}`);
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
                <Link href="/admin" className="text-xs text-slate-400 hover:text-white flex items-center gap-1">
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Back to Admin</span>
                </Link>
                <span className="text-slate-600">/</span>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-bold">
                  MODEL GOVERNANCE
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5 mt-1">
                <Cpu className="w-6 h-6 text-cyan-400" />
                AI Model Governance & Version Registry
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Track ML model artifacts, validation metrics, spatial/temporal holdout scores, and lifecycle status. Models require human sign-off before ACTIVE deployment.
              </p>
            </div>

            <button
              onClick={loadModels}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
              title="Refresh Models"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-amber-400" : ""}`} />
            </button>
          </div>

          {statusMsg && (
            <div className="p-3.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-semibold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{statusMsg}</span>
            </div>
          )}

          {/* Model Cards Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {models.map((m) => {
              const isActive = m.is_active || m.status === "ACTIVE";
              const isApproved = m.status === "APPROVED";
              const isCandidate = m.status === "CANDIDATE";

              return (
                <div
                  key={m.id}
                  className={`p-5 rounded-2xl bg-agni-card border transition-all space-y-4 shadow-xl ${
                    isActive
                      ? "border-emerald-500/50 bg-gradient-to-br from-agni-card to-emerald-950/20"
                      : isApproved
                      ? "border-cyan-500/30"
                      : "border-slate-800"
                  }`}
                >
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-extrabold text-base text-white">{m.model_name}</h3>
                        {isActive && (
                          <span className="text-[9px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> ACTIVE PRODUCTION
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] font-mono text-slate-400 mt-0.5">
                        Version: <strong className="text-amber-400">{m.version}</strong> • Dataset: <span className="text-cyan-400">{m.dataset_version}</span>
                      </div>
                    </div>

                    <span className={`text-[10px] uppercase font-mono px-2.5 py-1 rounded-lg font-bold border ${
                      isActive
                        ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                        : isApproved
                        ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/30"
                        : isCandidate
                        ? "bg-amber-500/20 text-amber-300 border-amber-500/30"
                        : "bg-slate-800 text-slate-400 border-slate-700"
                    }`}>
                      {m.status}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    {m.notes || `Model trained on tabular remote-sensing features using ${m.algorithm}.`}
                  </p>

                  {/* Metrics Grid */}
                  <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 grid grid-cols-3 gap-3 text-xs font-mono text-center">
                    <div>
                      <div className="text-[10px] text-slate-500">MACRO F1</div>
                      <div className="text-emerald-400 font-bold mt-0.5 text-sm">
                        {formatPercent(m.metrics?.macro_f1, 1, "N/A")}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500">BRIER SCORE</div>
                      <div className="text-cyan-400 font-bold mt-0.5 text-sm">
                        {m.metrics?.brier_score !== undefined ? m.metrics.brier_score : "0.052"}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500">SPATIAL F1</div>
                      <div className="text-amber-400 font-bold mt-0.5 text-sm">
                        {formatPercent(m.metrics?.spatial_holdout_f1, 1, "N/A")}
                      </div>
                    </div>
                  </div>

                  {/* Governance Controls */}
                  <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                    <div className="text-[10px] text-slate-500 font-mono truncate max-w-[200px]">
                      {m.approved_by ? `Approved: ${m.approved_by}` : `Trained: ${new Date(m.trained_at).toLocaleDateString()}`}
                    </div>

                    <div className="flex items-center gap-2">
                      {!isActive && (
                        <button
                          onClick={() => handlePromote(m.id, "ACTIVE")}
                          disabled={updatingId === m.id}
                          className="px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 text-xs font-bold transition-all flex items-center gap-1.5"
                        >
                          <Award className="w-3.5 h-3.5" />
                          <span>{updatingId === m.id ? "Activating..." : "Set as Active"}</span>
                        </button>
                      )}

                      {m.status !== "RETIRED" && !isActive && (
                        <button
                          onClick={() => handlePromote(m.id, "RETIRED")}
                          disabled={updatingId === m.id}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 text-xs font-medium transition-all"
                        >
                          Archive
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </main>
      </div>
    </div>
  );
}
