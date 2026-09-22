"use client";

import React, { useState } from "react";
import { 
  CheckCircle2, XCircle, AlertTriangle, ShieldCheck, 
  Lock, Loader2, FileText, Send 
} from "lucide-react";
import Button from "./Button";
import StatusBadge from "./StatusBadge";

export interface VerificationSubmitData {
  outcome: "CONFIRM" | "REJECT" | "ESCALATE" | "QUARANTINED";
  groundTruthClass: string;
  confidenceScore: number;
  notes: string;
}

export interface VerificationPanelProps {
  eventCode: string;
  initialClass?: string;
  initialOutcome?: "CONFIRM" | "REJECT" | "ESCALATE" | "QUARANTINED";
  onSubmit: (data: VerificationSubmitData) => Promise<void>;
  loading?: boolean;
  onCancel?: () => void;
  className?: string;
}

const CLASSIFICATION_CLASSES = [
  "Industrial Fire",
  "Gas Flare",
  "Agricultural Burning",
  "Controlled Forest Fire",
  "Coal Mining Thermal Anomaly",
  "Urban / Landfill Hazard",
  "False Positive / Glint",
];

export default function VerificationPanel({
  eventCode,
  initialClass = "Industrial Fire",
  initialOutcome = "CONFIRM",
  onSubmit,
  loading = false,
  onCancel,
  className = "",
}: VerificationPanelProps) {
  const [outcome, setOutcome] = useState<"CONFIRM" | "REJECT" | "ESCALATE" | "QUARANTINED">(initialOutcome);
  const [groundTruthClass, setGroundTruthClass] = useState<string>(initialClass);
  const [confidenceScore, setConfidenceScore] = useState<number>(95);
  const [notes, setNotes] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setSuccessMessage(null);
    try {
      await onSubmit({
        outcome,
        groundTruthClass,
        confidenceScore: confidenceScore / 100,
        notes,
      });
      setSuccessMessage(`Event ${eventCode} verification successfully registered.`);
    } catch (err: any) {
      // Handled by parent or caller
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className={`p-4 rounded-xl border border-agni-border bg-slate-900/95 font-mono text-xs space-y-4 shadow-xl ${className}`}
    >
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-amber-400" />
          <h3 className="font-bold text-sm tracking-wide text-white">
            ANALYST VERIFICATION TRIAGE
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status="BLOCKED" label="DISPATCH GATE: BLOCKED" size="xs" />
        </div>
      </div>

      <div className="p-2.5 rounded-lg bg-red-950/20 border border-red-500/30 text-[11px] text-red-300 space-y-1">
        <div className="flex items-center gap-1.5 font-bold">
          <Lock className="w-3.5 h-3.5 text-red-400 shrink-0" />
          <span>STATUTORY SAFETY GOVERNANCE INVARIANT</span>
        </div>
        <p className="text-[10px] text-slate-400 leading-snug">
          Operational dispatch is gated (`ENABLE_OPERATIONAL_DISPATCH_GATE = False`). 
          Human confirmation records a legally defensible audit record into PostGIS but does NOT trigger automated emergency sirens or agency deployments.
        </p>
      </div>

      {successMessage ? (
        <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{successMessage}</span>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Verification Outcome */}
          <div className="space-y-1.5">
            <label className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">
              Verification Outcome
            </label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { id: "CONFIRM", label: "Confirm Anomaly", color: "text-emerald-300 border-emerald-500/40 bg-emerald-950/20" },
                { id: "REJECT", label: "Reject / False Positive", color: "text-slate-300 border-slate-700 bg-slate-800/40" },
                { id: "ESCALATE", label: "Escalate to Senior", color: "text-amber-300 border-amber-500/40 bg-amber-950/20" },
                { id: "QUARANTINED", label: "Quarantine Telemetry", color: "text-rose-300 border-rose-500/40 bg-rose-950/20" },
              ].map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setOutcome(opt.id as any)}
                  className={`p-2 rounded-lg border text-left text-xs transition-all flex items-center justify-between ${
                    outcome === opt.id
                      ? `${opt.color} ring-1 ring-amber-400 font-bold`
                      : "border-slate-800 bg-slate-900 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  <span>{opt.label}</span>
                  {outcome === opt.id && <CheckCircle2 className="w-3.5 h-3.5 text-amber-400" />}
                </button>
              ))}
            </div>
          </div>

          {/* Ground Truth Override */}
          <div className="space-y-1.5">
            <label className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">
              Attributed Class (Ground Truth)
            </label>
            <select
              value={groundTruthClass}
              onChange={(e) => setGroundTruthClass(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-amber-500"
            >
              {CLASSIFICATION_CLASSES.map((cls) => (
                <option key={cls} value={cls}>
                  {cls}
                </option>
              ))}
            </select>
          </div>

          {/* Analyst Confidence Slider */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-slate-400 uppercase tracking-wider font-semibold">
                Analyst Judgment Confidence
              </span>
              <span className="text-amber-400 font-bold">{confidenceScore}%</span>
            </div>
            <input
              type="range"
              min="50"
              max="100"
              value={confidenceScore}
              onChange={(e) => setConfidenceScore(parseInt(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
            />
          </div>

          {/* Verification Notes */}
          <div className="space-y-1.5">
            <label className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">
              Auditable Analyst Notes & Justification
            </label>
            <textarea
              required
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Detail visual corroboration, cadastral verification, and plume cross-checks..."
              className="w-full p-2.5 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 text-xs placeholder:text-slate-600 focus:outline-none focus:border-amber-500 leading-relaxed font-sans"
            />
          </div>

          <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-800">
            {onCancel && (
              <Button type="button" variant="outline" size="sm" onClick={onCancel}>
                Cancel
              </Button>
            )}
            <Button
              type="submit"
              variant="primary"
              size="sm"
              loading={submitting || loading}
              icon={<Send className="w-3.5 h-3.5" />}
            >
              Sign & Commit Verification
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
