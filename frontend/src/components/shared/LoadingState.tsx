"use client";

import React from "react";
import { Loader2 } from "lucide-react";

export function Spinner({ size = "md", label }: { size?: "sm" | "md" | "lg"; label?: string }) {
  const sizeClasses = {
    sm: "w-3.5 h-3.5",
    md: "w-5 h-5",
    lg: "w-8 h-8",
  }[size];

  return (
    <div className="flex flex-col items-center justify-center gap-2 text-amber-400 p-4 font-mono text-xs">
      <Loader2 className={`${sizeClasses} animate-spin`} />
      {label && <span className="text-slate-400 text-[11px]">{label}</span>}
    </div>
  );
}

export function StatSkeleton({ count = 1 }: { count?: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 animate-pulse space-y-2.5 font-mono"
        >
          <div className="flex items-center justify-between">
            <div className="h-3 w-20 bg-slate-800 rounded" />
            <div className="h-4 w-4 bg-slate-800/60 rounded" />
          </div>
          <div className="h-7 w-28 bg-slate-700/80 rounded" />
          <div className="h-2.5 w-32 bg-slate-800/60 rounded" />
        </div>
      ))}
    </>
  );
}

export function CardSkeleton({ lines = 3, count = 1 }: { lines?: number; count?: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, cIdx) => (
        <div
          key={cIdx}
          className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 animate-pulse space-y-3"
        >
          <div className="flex items-center justify-between">
            <div className="h-4 w-32 bg-slate-800 rounded" />
            <div className="h-4 w-16 bg-slate-800/60 rounded" />
          </div>
          <div className="space-y-2 pt-1">
            {Array.from({ length: lines }).map((_, i) => (
              <div
                key={i}
                className="h-3 bg-slate-800/50 rounded"
                style={{ width: `${85 - i * 15}%` }}
              />
            ))}
          </div>
        </div>
      ))}
    </>
  );
}

export function TableSkeleton({ rows = 6, cols = 5 }: { rows?: number; cols?: number }) {
  return (
    <div className="w-full rounded-xl bg-slate-900/40 border border-slate-800/80 overflow-hidden animate-pulse font-mono">
      <div className="h-10 bg-slate-800/70 border-b border-slate-800 flex items-center px-4 gap-4">
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="h-3.5 bg-slate-700/60 rounded flex-1" />
        ))}
      </div>
      <div className="divide-y divide-slate-800/50">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="h-11 px-4 flex items-center gap-4">
            {Array.from({ length: cols }).map((_, c) => (
              <div
                key={c}
                className="h-3 bg-slate-800/60 rounded flex-1"
                style={{ opacity: 1 - r * 0.12 }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function MapSkeleton() {
  return (
    <div className="w-full h-full min-h-[420px] rounded-xl bg-slate-950 border border-slate-800 flex flex-col items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px] opacity-30" />
      <div className="relative z-10 flex flex-col items-center gap-3 p-6 text-center font-mono">
        <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center animate-spin">
          <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
        </div>
        <div className="space-y-1">
          <div className="text-xs font-bold text-slate-200 tracking-wider">
            SYNCHRONIZING CARTOGRAPHIC LAYERS
          </div>
          <div className="text-[10px] text-slate-500">
            Fetching PostGIS 3.4 polygons and VIIRS 375m detections...
          </div>
        </div>
      </div>
    </div>
  );
}
