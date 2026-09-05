"use client";

import React from "react";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  badge?: string;
  badgeColor?: string;
  icon?: LucideIcon;
  iconColor?: string;
  trend?: string;
  trendDirection?: "up" | "down" | "neutral";
  className?: string;
}

export default function StatCard({
  label,
  value,
  subtext,
  badge,
  badgeColor = "bg-slate-800 text-slate-400 border-slate-700",
  icon: Icon,
  iconColor = "text-amber-400",
  trend,
  trendDirection = "neutral",
  className = "",
}: StatCardProps) {
  const getTrendColor = () => {
    if (trendDirection === "up") return "text-emerald-400";
    if (trendDirection === "down") return "text-cyan-400";
    return "text-slate-400";
  };

  return (
    <div
      className={`p-4 rounded-xl bg-slate-900/70 border border-slate-800/90 shadow-sm hover:border-slate-700/80 transition-all flex flex-col justify-between ${className}`}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider font-semibold">
          {label}
        </span>
        <div className="flex items-center gap-1.5">
          {badge && (
            <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border font-bold ${badgeColor}`}>
              {badge}
            </span>
          )}
          {Icon && <Icon className={`w-4 h-4 ${iconColor}`} />}
        </div>
      </div>

      <div className="flex items-baseline justify-between gap-2 my-1">
        <span className="text-xl sm:text-2xl font-black text-white font-mono tracking-tight">
          {value}
        </span>
        {trend && (
          <span className={`text-[10px] font-mono font-bold ${getTrendColor()}`}>
            {trend}
          </span>
        )}
      </div>

      {subtext && (
        <div className="text-[11px] text-slate-400 leading-tight truncate mt-1">
          {subtext}
        </div>
      )}
    </div>
  );
}
