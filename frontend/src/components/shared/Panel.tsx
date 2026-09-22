"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp, Loader2, AlertTriangle } from "lucide-react";

export interface PanelProps {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  badge?: React.ReactNode;
  icon?: React.ReactNode;
  actions?: React.ReactNode;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  loading?: boolean;
  error?: string | null;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
  headerClassName?: string;
}

export default function Panel({
  title,
  subtitle,
  badge,
  icon,
  actions,
  collapsible = false,
  defaultCollapsed = false,
  loading = false,
  error = null,
  children,
  className = "",
  bodyClassName = "p-4",
  headerClassName = "p-3.5",
}: PanelProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  return (
    <div
      className={`rounded-xl border border-agni-border bg-slate-900/80 shadow-md relative overflow-hidden flex flex-col transition-all ${className}`}
    >
      {(title || subtitle || actions || badge || collapsible) && (
        <div
          className={`flex items-center justify-between border-b border-slate-800/80 bg-slate-950/40 select-none ${headerClassName}`}
        >
          <div className="flex items-center gap-2.5 min-w-0">
            {icon && <span className="text-amber-400 shrink-0">{icon}</span>}
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                {typeof title === "string" ? (
                  <h3 className="text-xs font-bold font-mono tracking-wider uppercase text-slate-200 truncate">
                    {title}
                  </h3>
                ) : (
                  title
                )}
                {badge && <span className="shrink-0">{badge}</span>}
              </div>
              {subtitle && (
                <p className="text-[11px] text-slate-400 truncate mt-0.5">{subtitle}</p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 ml-2">
            {actions && <div>{actions}</div>}
            {collapsible && (
              <button
                type="button"
                onClick={() => setCollapsed(!collapsed)}
                className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                aria-label={collapsed ? "Expand panel" : "Collapse panel"}
              >
                {collapsed ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronUp className="w-4 h-4" />
                )}
              </button>
            )}
          </div>
        </div>
      )}

      {error ? (
        <div className="p-4 bg-red-950/20 border-t border-red-500/30 text-red-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-red-400" />
          <span>{error}</span>
        </div>
      ) : !collapsed ? (
        <div className={`relative flex-1 ${bodyClassName}`}>
          {loading && (
            <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-[1px] flex items-center justify-center z-10">
              <Loader2 className="w-5 h-5 text-amber-400 animate-spin" />
            </div>
          )}
          {children}
        </div>
      ) : null}
    </div>
  );
}
