"use client";

import React from "react";
import { Eye, Calculator, Sparkles, HelpCircle, AlertOctagon, GitCompare } from "lucide-react";

export type EpistemicState =
  | "OBSERVED"
  | "DERIVED"
  | "INFERRED"
  | "UNKNOWN"
  | "MISSING"
  | "CONFLICTING"
  | string;

interface EpistemicBadgeProps {
  state: EpistemicState;
  label?: string;
  size?: "xs" | "sm" | "md";
  showIcon?: boolean;
  className?: string;
}

export default function EpistemicBadge({
  state,
  label,
  size = "sm",
  showIcon = true,
  className = "",
}: EpistemicBadgeProps) {
  const normState = (state || "UNKNOWN").toUpperCase();

  let colorClasses = "bg-slate-800 text-slate-300 border-slate-700";
  let Icon = HelpCircle;
  let defaultLabel = normState;

  switch (normState) {
    case "OBSERVED":
      colorClasses = "bg-emerald-500/15 text-emerald-400 border-emerald-500/40";
      Icon = Eye;
      break;
    case "DERIVED":
      colorClasses = "bg-cyan-500/15 text-cyan-300 border-cyan-500/40";
      Icon = Calculator;
      break;
    case "INFERRED":
      colorClasses = "bg-purple-500/15 text-purple-300 border-purple-500/40";
      Icon = Sparkles;
      break;
    case "UNKNOWN":
      colorClasses = "bg-slate-800/80 text-slate-400 border-slate-700/80";
      Icon = HelpCircle;
      break;
    case "MISSING":
      colorClasses = "bg-rose-500/15 text-rose-400 border-rose-500/40";
      Icon = AlertOctagon;
      break;
    case "CONFLICTING":
      colorClasses = "bg-amber-500/15 text-amber-400 border-amber-500/40";
      Icon = GitCompare;
      break;
  }

  const sizeClasses = {
    xs: "text-[9px] px-1.5 py-0.2 gap-1",
    sm: "text-[10px] px-2 py-0.5 gap-1.5",
    md: "text-xs px-2.5 py-1 gap-1.5 font-medium",
  }[size];

  const iconSizes = {
    xs: "w-2.5 h-2.5",
    sm: "w-3 h-3",
    md: "w-3.5 h-3.5",
  }[size];

  return (
    <span
      title={`Epistemic Classification: ${normState}`}
      className={`inline-flex items-center rounded border font-mono tracking-wider transition-colors ${colorClasses} ${sizeClasses} ${className}`}
    >
      {showIcon && <Icon className={`${iconSizes} shrink-0`} />}
      <span>{label || defaultLabel}</span>
    </span>
  );
}
