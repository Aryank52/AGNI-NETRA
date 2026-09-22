"use client";

import React from "react";
import { AlertOctagon, Info, ShieldAlert, WifiOff } from "lucide-react";
import EpistemicBadge from "./EpistemicBadge";

export interface DegradedStateProps {
  providerName: string;
  reason?: string;
  status?: "NOT_CONFIGURED" | "DEGRADED" | "OFFLINE_CACHE" | "BLOCKED";
  epistemicState?: "MISSING" | "UNKNOWN";
  className?: string;
}

export default function DegradedState({
  providerName,
  reason = "International spaceborne feed is not configured. Zero synthetic data is substituted under sovereign data truth policies.",
  status = "NOT_CONFIGURED",
  epistemicState = "MISSING",
  className = "",
}: DegradedStateProps) {
  return (
    <div
      className={`p-3.5 rounded-xl border border-amber-500/40 bg-amber-950/15 text-xs font-mono flex flex-col gap-2 ${className}`}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-amber-300 font-bold">
          <AlertOctagon className="w-4 h-4 shrink-0 text-amber-400" />
          <span>DATA TRUTH DISCLOSURE: {providerName}</span>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <EpistemicBadge state={epistemicState} size="xs" />
          <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-900 border border-slate-700 text-slate-300 font-bold">
            {status}
          </span>
        </div>
      </div>

      <p className="text-slate-300 font-sans text-xs leading-relaxed">{reason}</p>

      <div className="text-[10px] text-slate-500 pt-1 border-t border-amber-500/20 flex items-center justify-between">
        <span>Sovereign India Scope Guarantee: Real observations only</span>
        <span className="text-amber-400 font-semibold">NO SYNTHETIC SUBSTITUTION</span>
      </div>
    </div>
  );
}
