"use client";

import React from "react";
import { CheckCircle2, Clock, Lock, Ban, Activity, ShieldCheck, HelpCircle } from "lucide-react";

export type SystemStatus =
  | "ACTIVE"
  | "RESOLVED"
  | "VERIFIED"
  | "PENDING"
  | "CANDIDATE"
  | "BLOCKED"
  | "DISABLED"
  | "DORMANT"
  | string;

interface StatusBadgeProps {
  status: SystemStatus;
  label?: string;
  size?: "xs" | "sm" | "md";
  showIcon?: boolean;
  className?: string;
}

export default function StatusBadge({
  status,
  label,
  size = "sm",
  showIcon = true,
  className = "",
}: StatusBadgeProps) {
  const normStatus = (status || "PENDING").toUpperCase();

  let colorClasses = "bg-slate-800 text-slate-300 border-slate-700";
  let Icon = HelpCircle;
  let pulse = false;

  switch (normStatus) {
    case "ACTIVE":
      colorClasses = "bg-emerald-500/15 text-emerald-400 border-emerald-500/40";
      Icon = Activity;
      pulse = true;
      break;
    case "VERIFIED":
      colorClasses = "bg-blue-500/15 text-blue-300 border-blue-500/40";
      Icon = ShieldCheck;
      break;
    case "RESOLVED":
      colorClasses = "bg-slate-800 text-slate-300 border-slate-700";
      Icon = CheckCircle2;
      break;
    case "PENDING":
      colorClasses = "bg-amber-500/15 text-amber-300 border-amber-500/40";
      Icon = Clock;
      break;
    case "CANDIDATE":
      colorClasses = "bg-purple-500/15 text-purple-300 border-purple-500/40";
      Icon = Clock;
      break;
    case "BLOCKED":
      colorClasses = "bg-red-500/15 text-red-400 border-red-500/40 font-bold";
      Icon = Lock;
      break;
    case "DISABLED":
      colorClasses = "bg-slate-800/80 text-slate-400 border-slate-700";
      Icon = Ban;
      break;
    case "DORMANT":
      colorClasses = "bg-slate-900 text-slate-500 border-slate-800";
      Icon = Clock;
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
      className={`inline-flex items-center rounded border font-mono tracking-wider transition-colors ${colorClasses} ${sizeClasses} ${className}`}
    >
      {pulse && (
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping mr-0.5" />
      )}
      {showIcon && <Icon className={`${iconSizes} shrink-0`} />}
      <span>{label || normStatus}</span>
    </span>
  );
}
