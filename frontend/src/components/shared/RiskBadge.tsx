"use client";

import React from "react";
import { ShieldAlert, AlertTriangle, ShieldCheck, Flame } from "lucide-react";

export type RiskLevel = "CRITICAL" | "HIGH" | "MODERATE" | "LOW" | string;

interface RiskBadgeProps {
  level: RiskLevel;
  score?: number | null;
  size?: "xs" | "sm" | "md" | "lg";
  showIcon?: boolean;
  className?: string;
}

export default function RiskBadge({
  level,
  score,
  size = "sm",
  showIcon = true,
  className = "",
}: RiskBadgeProps) {
  const normLevel = (level || "LOW").toUpperCase();

  let colorClasses = "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
  let Icon = ShieldCheck;

  if (normLevel === "CRITICAL") {
    colorClasses = "bg-red-500/15 text-red-400 border-red-500/40 font-bold";
    Icon = Flame;
  } else if (normLevel === "HIGH") {
    colorClasses = "bg-orange-500/15 text-orange-400 border-orange-500/40 font-semibold";
    Icon = ShieldAlert;
  } else if (normLevel === "MODERATE") {
    colorClasses = "bg-amber-500/15 text-amber-300 border-amber-500/40 font-medium";
    Icon = AlertTriangle;
  }

  const sizeClasses = {
    xs: "text-[9px] px-1.5 py-0.5 gap-1",
    sm: "text-[11px] px-2 py-0.5 gap-1.5",
    md: "text-xs px-2.5 py-1 gap-1.5 font-semibold",
    lg: "text-sm px-3 py-1.5 gap-2 font-bold",
  }[size];

  const iconSizes = {
    xs: "w-2.5 h-2.5",
    sm: "w-3 h-3",
    md: "w-3.5 h-3.5",
    lg: "w-4 h-4",
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-md border font-mono tracking-wider transition-colors ${colorClasses} ${sizeClasses} ${className}`}
    >
      {showIcon && <Icon className={`${iconSizes} shrink-0`} />}
      <span>{normLevel}</span>
      {typeof score === "number" && !isNaN(score) && (
        <span className="opacity-90 pl-1 border-l border-current/30 font-bold">
          {score.toFixed(1)}
        </span>
      )}
    </span>
  );
}
