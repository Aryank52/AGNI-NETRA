import React from "react";

interface RiskBadgeProps {
  level: "CRITICAL" | "HIGH" | "MODERATE" | "LOW" | string;
  score?: number;
  showScore?: boolean;
}

export default function RiskBadge({ level, score, showScore = true }: RiskBadgeProps) {
  const normalizedLevel = (level || "LOW").toUpperCase();

  const styles: Record<string, { bg: string; text: string; border: string; glow: string }> = {
    CRITICAL: {
      bg: "bg-red-500/20",
      text: "text-red-400",
      border: "border-red-500/40",
      glow: "shadow-[0_0_10px_rgba(239,68,68,0.3)]",
    },
    HIGH: {
      bg: "bg-orange-500/20",
      text: "text-orange-400",
      border: "border-orange-500/40",
      glow: "shadow-[0_0_8px_rgba(249,115,22,0.25)]",
    },
    MODERATE: {
      bg: "bg-amber-500/20",
      text: "text-amber-400",
      border: "border-amber-500/40",
      glow: "",
    },
    LOW: {
      bg: "bg-emerald-500/20",
      text: "text-emerald-400",
      border: "border-emerald-500/40",
      glow: "",
    },
  };

  const currentStyle = styles[normalizedLevel] || styles.LOW;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase tracking-wide border ${currentStyle.bg} ${currentStyle.text} ${currentStyle.border} ${currentStyle.glow}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
      <span>{normalizedLevel}</span>
      {showScore && score !== undefined && score !== null && !isNaN(Number(score)) && (
        <span className="opacity-80">({Number(score).toFixed(1)})</span>
      )}
    </span>
  );
}
