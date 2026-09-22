"use client";

import React from "react";

export interface TabItem<T = string> {
  id: T;
  label: string;
  count?: number;
  badge?: string;
  icon?: React.ReactNode;
}

export interface TabsProps<T = string> {
  tabs: TabItem<T>[];
  activeTab: T;
  onChange: (tabId: T) => void;
  variant?: "pills" | "underline";
  size?: "sm" | "md";
  className?: string;
}

export default function Tabs<T extends string = string>({
  tabs,
  activeTab,
  onChange,
  variant = "pills",
  size = "md",
  className = "",
}: TabsProps<T>) {
  if (variant === "underline") {
    return (
      <div className={`border-b border-slate-800 flex items-center gap-2 overflow-x-auto ${className}`}>
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => onChange(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-mono font-medium border-b-2 transition-all whitespace-nowrap ${
                isActive
                  ? "border-amber-400 text-amber-300 font-semibold"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
              }`}
            >
              {tab.icon && <span className="shrink-0">{tab.icon}</span>}
              <span>{tab.label}</span>
              {typeof tab.count === "number" && (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${
                    isActive
                      ? "bg-amber-500/20 text-amber-300 font-bold"
                      : "bg-slate-800 text-slate-400"
                  }`}
                >
                  {tab.count}
                </span>
              )}
              {tab.badge && (
                <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 font-mono">
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    );
  }

  // Default: pills
  const sizeClasses = {
    sm: "p-0.5 gap-1 text-[11px]",
    md: "p-1 gap-1.5 text-xs",
  }[size];

  const itemSizeClasses = {
    sm: "px-2.5 py-1",
    md: "px-3 py-1.5",
  }[size];

  return (
    <div
      className={`inline-flex items-center rounded-lg bg-slate-950/80 border border-slate-800/90 overflow-x-auto ${sizeClasses} ${className}`}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            className={`flex items-center gap-2 rounded-md font-mono transition-all whitespace-nowrap ${itemSizeClasses} ${
              isActive
                ? "bg-amber-500 text-slate-950 font-bold shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
            }`}
          >
            {tab.icon && <span className="shrink-0">{tab.icon}</span>}
            <span>{tab.label}</span>
            {typeof tab.count === "number" && (
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                  isActive
                    ? "bg-slate-950/30 text-slate-950 font-bold"
                    : "bg-slate-800 text-slate-300"
                }`}
              >
                {tab.count}
              </span>
            )}
            {tab.badge && (
              <span
                className={`text-[9px] px-1.5 py-0.2 rounded font-mono ${
                  isActive
                    ? "bg-slate-950/20 text-slate-950"
                    : "bg-slate-800 text-slate-300"
                }`}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
