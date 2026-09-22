"use client";

import React from "react";
import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";
import EpistemicBadge, { EpistemicState } from "./EpistemicBadge";

export interface KPIProps {
  label: string;
  value: string | number;
  unit?: string;
  subtext?: string;
  icon?: LucideIcon;
  trend?: {
    value: string | number;
    direction: "up" | "down" | "neutral";
    label?: string;
  };
  epistemicState?: EpistemicState;
  variant?: "default" | "critical" | "high" | "moderate" | "safe";
  className?: string;
}

export default function KPI({
  label,
  value,
  unit,
  subtext,
  icon: Icon,
  trend,
  epistemicState,
  variant = "default",
  className = "",
}: KPIProps) {
  const variantStyles = {
    default: "border-agni-border bg-slate-900/70 hover:border-slate-700",
    critical: "border-red-500/40 bg-red-950/20 text-red-300",
    high: "border-orange-500/40 bg-orange-950/20 text-orange-300",
    moderate: "border-amber-500/40 bg-amber-950/20 text-amber-300",
    safe: "border-emerald-500/40 bg-emerald-950/20 text-emerald-300",
  }[variant];

  return (
    <div
      className={`p-4 rounded-xl border transition-all ${variantStyles} ${className} flex flex-col justify-between`}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-[11px] font-mono tracking-wider uppercase text-slate-400 font-semibold truncate">
          {label}
        </span>
        <div className="flex items-center gap-1.5 shrink-0">
          {epistemicState && <EpistemicBadge state={epistemicState} size="xs" />}
          {Icon && (
            <div className="w-6 h-6 rounded bg-slate-800/80 border border-slate-700/80 flex items-center justify-center text-slate-300">
              <Icon className="w-3.5 h-3.5" />
            </div>
          )}
        </div>
      </div>

      <div className="flex items-baseline gap-1.5 my-0.5">
        <span className="text-2xl font-bold font-mono tracking-tight text-white telemetry-val">
          {value}
        </span>
        {unit && (
          <span className="text-xs font-mono text-slate-400 font-medium">{unit}</span>
        )}
      </div>

      {(subtext || trend) && (
        <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2 pt-2 border-t border-slate-800/80">
          {subtext && <span className="truncate">{subtext}</span>}
          {trend && (
            <span
              className={`flex items-center gap-1 font-mono font-semibold text-[10px] shrink-0 ml-auto ${
                trend.direction === "up"
                  ? "text-red-400"
                  : trend.direction === "down"
                  ? "text-emerald-400"
                  : "text-slate-400"
              }`}
            >
              {trend.direction === "up" ? (
                <TrendingUp className="w-3 h-3" />
              ) : trend.direction === "down" ? (
                <TrendingDown className="w-3 h-3" />
              ) : null}
              <span>{trend.value}</span>
              {trend.label && <span className="text-slate-500 font-normal">({trend.label})</span>}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
