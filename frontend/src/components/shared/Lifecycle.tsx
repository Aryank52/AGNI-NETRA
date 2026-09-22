"use client";

import React from "react";
import { Check, Circle, Activity, AlertCircle, Clock } from "lucide-react";

export type PipelineStage =
  | "IDLE"
  | "OBSERVED"
  | "INVESTIGATING"
  | "EVIDENCE_COLLECTED"
  | "UNCERTAINTY_QUANTIFIED"
  | "WAITING_FOR_HUMAN"
  | "COMPLETED"
  | string;

export interface LifecycleProps {
  currentStage: PipelineStage;
  className?: string;
}

const CANONICAL_STAGES: { id: PipelineStage; label: string; shortLabel: string }[] = [
  { id: "IDLE", label: "Idle State", shortLabel: "IDLE" },
  { id: "OBSERVED", label: "Telemetry Observed", shortLabel: "OBSERVED" },
  { id: "INVESTIGATING", label: "Agent Investigating", shortLabel: "INVESTIGATE" },
  { id: "EVIDENCE_COLLECTED", label: "Evidence Collected", shortLabel: "EVIDENCE" },
  { id: "UNCERTAINTY_QUANTIFIED", label: "Uncertainty Quantified", shortLabel: "UNCERTAINTY" },
  { id: "WAITING_FOR_HUMAN", label: "Waiting for Human Action", shortLabel: "HITL GATE" },
  { id: "COMPLETED", label: "Mission Completed", shortLabel: "COMPLETED" },
];

export default function Lifecycle({ currentStage, className = "" }: LifecycleProps) {
  const normCurrent = (currentStage || "IDLE").toUpperCase();
  const currentIndex = CANONICAL_STAGES.findIndex((s) => s.id === normCurrent);

  return (
    <div className={`w-full py-2.5 px-3 rounded-xl bg-slate-950/60 border border-slate-800/90 ${className}`}>
      <div className="flex items-center justify-between gap-1 overflow-x-auto">
        {CANONICAL_STAGES.map((stage, idx) => {
          const isPassed = currentIndex > idx;
          const isCurrent = currentIndex === idx;
          const isPending = currentIndex < idx;

          return (
            <React.Fragment key={stage.id}>
              <div
                className={`flex items-center gap-1.5 shrink-0 px-2 py-1 rounded-md transition-all font-mono text-[10px] ${
                  isCurrent
                    ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold"
                    : isPassed
                    ? "text-emerald-400 font-medium"
                    : "text-slate-500 opacity-60"
                }`}
                title={stage.label}
              >
                <div
                  className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 ${
                    isCurrent
                      ? "bg-amber-400 text-slate-950 font-bold"
                      : isPassed
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                      : "bg-slate-800 text-slate-500"
                  }`}
                >
                  {isPassed ? (
                    <Check className="w-2.5 h-2.5 stroke-[3]" />
                  ) : isCurrent ? (
                    <Activity className="w-2.5 h-2.5 animate-pulse" />
                  ) : (
                    <span className="text-[9px]">{idx + 1}</span>
                  )}
                </div>
                <span className="whitespace-nowrap">{stage.shortLabel}</span>
              </div>

              {idx < CANONICAL_STAGES.length - 1 && (
                <div
                  className={`h-0.5 flex-1 min-w-[12px] max-w-[32px] rounded-full shrink-0 ${
                    isPassed ? "bg-emerald-500/40" : "bg-slate-800"
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
