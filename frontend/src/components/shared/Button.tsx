"use client";

import React from "react";
import { Loader2 } from "lucide-react";

export type ButtonVariant = "primary" | "secondary" | "danger" | "outline" | "ghost";
export type ButtonSize = "xs" | "sm" | "md" | "lg";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
}

export default function Button({
  children,
  variant = "secondary",
  size = "md",
  loading = false,
  disabled = false,
  icon,
  iconRight,
  className = "",
  ...props
}: ButtonProps) {
  const baseClasses =
    "inline-flex items-center justify-center font-medium rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-amber-500/40 disabled:opacity-50 disabled:cursor-not-allowed shrink-0 select-none";

  const variantClasses = {
    primary:
      "bg-amber-500 hover:bg-amber-400 active:bg-amber-600 text-slate-950 font-bold shadow-sm shadow-amber-500/20",
    secondary:
      "bg-slate-800/90 hover:bg-slate-700 text-slate-200 border border-slate-700 hover:border-slate-600 active:bg-slate-800",
    danger:
      "bg-red-950/40 hover:bg-red-900/50 text-red-300 border border-red-500/40 hover:border-red-500/60 active:bg-red-950",
    outline:
      "bg-transparent hover:bg-slate-800/60 text-slate-300 hover:text-white border border-slate-700 hover:border-amber-500/50",
    ghost: "bg-transparent hover:bg-slate-800/50 text-slate-400 hover:text-slate-200",
  }[variant];

  const sizeClasses = {
    xs: "text-[10px] px-2 py-1 gap-1",
    sm: "text-xs px-2.5 py-1.5 gap-1.5",
    md: "text-xs px-3.5 py-2 gap-2",
    lg: "text-sm px-4.5 py-2.5 gap-2.5",
  }[size];

  return (
    <button
      disabled={disabled || loading}
      className={`${baseClasses} ${variantClasses} ${sizeClasses} ${className}`}
      {...props}
    >
      {loading ? (
        <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" />
      ) : (
        icon && <span className="shrink-0">{icon}</span>
      )}
      {children}
      {!loading && iconRight && <span className="shrink-0">{iconRight}</span>}
    </button>
  );
}
