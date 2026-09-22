"use client";

import React from "react";
import { AlertTriangle, RefreshCw, HelpCircle } from "lucide-react";
import Button from "./Button";

export interface ErrorStateProps {
  title?: string;
  message?: string;
  errorDetail?: string | null;
  onRetry?: () => void;
  retrying?: boolean;
  className?: string;
}

export default function ErrorState({
  title = "Telemetry Service Unavailable",
  message = "Failed to communicate with AGNI-NETRA core service. The remaining modules and offline cache remain active.",
  errorDetail,
  onRetry,
  retrying = false,
  className = "",
}: ErrorStateProps) {
  return (
    <div
      className={`p-6 rounded-xl border border-red-500/40 bg-red-950/20 text-slate-200 font-mono text-xs space-y-3 shadow-md ${className}`}
    >
      <div className="flex items-center gap-2.5 text-red-400 font-bold">
        <AlertTriangle className="w-5 h-5 shrink-0" />
        <h4 className="text-sm tracking-wide">{title}</h4>
      </div>

      <p className="text-slate-300 text-xs font-sans leading-relaxed">{message}</p>

      {errorDetail && (
        <pre className="p-2.5 rounded bg-slate-950/80 border border-slate-800 text-[11px] text-red-300 overflow-x-auto max-h-28 font-mono">
          {errorDetail}
        </pre>
      )}

      {onRetry && (
        <div className="pt-1">
          <Button
            variant="danger"
            size="sm"
            onClick={onRetry}
            loading={retrying}
            icon={<RefreshCw className={`w-3.5 h-3.5 ${retrying ? "animate-spin" : ""}`} />}
          >
            Retry Telemetry Query
          </Button>
        </div>
      )}
    </div>
  );
}
