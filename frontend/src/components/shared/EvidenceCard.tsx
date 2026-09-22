"use client";

import React from "react";
import { CheckCircle2, XCircle, AlertCircle, Database, ExternalLink } from "lucide-react";
import EpistemicBadge, { EpistemicState } from "./EpistemicBadge";

export type EvidencePolarity = "SUPPORTING" | "CONTRADICTING" | "MISSING" | string;

export interface EvidenceItem {
  id?: string;
  claim: string;
  polarity: EvidencePolarity;
  source: string;
  epistemicState?: EpistemicState;
  confidence?: number;
  weight?: number;
  timestamp?: string;
  notes?: string;
}

export interface EvidenceCardProps {
  evidence: EvidenceItem;
  className?: string;
}

export default function EvidenceCard({ evidence, className = "" }: EvidenceCardProps) {
  const normPolarity = (evidence.polarity || "SUPPORTING").toUpperCase();

  let polarityClasses = "border-emerald-500/30 bg-emerald-950/15 text-emerald-300";
  let PolarityIcon = CheckCircle2;
  let polarityLabel = "SUPPORTING";

  if (normPolarity === "CONTRADICTING") {
    polarityClasses = "border-rose-500/40 bg-rose-950/20 text-rose-300";
    PolarityIcon = XCircle;
    polarityLabel = "CONTRADICTING";
  } else if (normPolarity === "MISSING") {
    polarityClasses = "border-amber-500/40 bg-amber-950/20 text-amber-300";
    PolarityIcon = AlertCircle;
    polarityLabel = "MISSING";
  }

  return (
    <div
      className={`p-3.5 rounded-xl border transition-all text-xs font-mono space-y-2 ${polarityClasses} ${className}`}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 font-bold tracking-wider text-[10px]">
          <PolarityIcon className="w-3.5 h-3.5 shrink-0" />
          <span>{polarityLabel} EVIDENCE</span>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {evidence.epistemicState && (
            <EpistemicBadge state={evidence.epistemicState} size="xs" />
          )}
          {typeof evidence.confidence === "number" && (
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-900/80 border border-slate-700/60 font-mono text-slate-300">
              Conf: {(evidence.confidence * 100).toFixed(0)}%
            </span>
          )}
        </div>
      </div>

      <p className="text-slate-200 font-sans text-xs leading-relaxed font-normal">
        {evidence.claim}
      </p>

      <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1.5 border-t border-current/20">
        <div className="flex items-center gap-1 truncate max-w-[70%]">
          <Database className="w-3 h-3 shrink-0 opacity-70" />
          <span className="truncate">{evidence.source}</span>
        </div>
        {evidence.timestamp && (
          <span className="shrink-0 text-slate-500">{evidence.timestamp}</span>
        )}
      </div>
    </div>
  );
}
