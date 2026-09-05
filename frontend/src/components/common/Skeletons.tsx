"use client";

import React from "react";

export function StatSkeleton() {
  return (
    <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 animate-pulse space-y-2">
      <div className="h-3 w-20 bg-slate-800 rounded"></div>
      <div className="h-7 w-28 bg-slate-700/80 rounded"></div>
      <div className="h-2.5 w-32 bg-slate-800/60 rounded"></div>
    </div>
  );
}

export function CardSkeleton({ lines = 3, count = 1 }: { lines?: number; count?: number }) {
  const cards = Array.from({ length: count }).map((_, cIdx) => (
    <div key={cIdx} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 animate-pulse space-y-3">
      <div className="flex items-center justify-between">
        <div className="h-4 w-32 bg-slate-800 rounded"></div>
        <div className="h-4 w-16 bg-slate-800/60 rounded"></div>
      </div>
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className="h-3 bg-slate-800/50 rounded"
            style={{ width: `${85 - i * 15}%` }}
          ></div>
        ))}
      </div>
    </div>
  ));

  if (count === 1) return cards[0];
  return <>{cards}</>;
}

export function TableSkeleton({ rows = 5, cols = 5 }: { rows?: number; cols?: number }) {
  return (
    <div className="w-full rounded-xl bg-slate-900/50 border border-slate-800/80 overflow-hidden animate-pulse">
      <div className="h-10 bg-slate-800/60 border-b border-slate-800 flex items-center px-4 gap-4">
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="h-3.5 bg-slate-700/60 rounded flex-1"></div>
        ))}
      </div>
      <div className="divide-y divide-slate-800/50">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="h-12 px-4 flex items-center gap-4">
            {Array.from({ length: cols }).map((_, c) => (
              <div
                key={c}
                className="h-3 bg-slate-800/60 rounded flex-1"
                style={{ opacity: 1 - r * 0.12 }}
              ></div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function MapLoadingSkeleton() {
  return (
    <div className="w-full h-full min-h-[400px] rounded-xl bg-slate-950 border border-slate-800 flex flex-col items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px] opacity-40"></div>
      <div className="relative z-10 flex flex-col items-center gap-3 p-6 text-center">
        <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center animate-spin">
          <div className="w-3 h-3 rounded-full bg-amber-400"></div>
        </div>
        <div className="space-y-1">
          <div className="text-xs font-mono font-bold text-slate-200 tracking-wider">INITIALIZING GIS CARTOGRAPHY</div>
          <div className="text-[11px] text-slate-400">Loading MapLibre vector tiles and PostGIS spatial layers...</div>
        </div>
      </div>
    </div>
  );
}
