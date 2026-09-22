"use client";

import React from "react";
import { Search, X, Filter, SlidersHorizontal, RotateCcw } from "lucide-react";
import Button from "./Button";

export interface FilterBarValues {
  state: string;
  district: string;
  riskLevel: string;
  searchQuery: string;
  horizon?: string;
}

export interface FilterBarProps {
  values: FilterBarValues;
  onChange: (newValues: Partial<FilterBarValues>) => void;
  onReset?: () => void;
  statesList?: Array<{ state_name: string }>;
  districtsList?: Array<{ district_name: string }>;
  showHorizon?: boolean;
  horizons?: Array<{ id: string; label: string }>;
  totalMatches?: number;
  className?: string;
}

const DEFAULT_HORIZONS = [
  { id: "24h", label: "Last 24 Hours" },
  { id: "7d", label: "7 Days" },
  { id: "30d", label: "30 Days" },
  { id: "all", label: "6-Year Archive (2020-2025)" },
];

export default function FilterBar({
  values,
  onChange,
  onReset,
  statesList = [],
  districtsList = [],
  showHorizon = false,
  horizons = DEFAULT_HORIZONS,
  totalMatches,
  className = "",
}: FilterBarProps) {
  return (
    <div
      className={`p-3 rounded-xl border border-agni-border bg-slate-900/90 backdrop-blur font-mono text-xs flex flex-wrap items-center justify-between gap-3 shadow-md ${className}`}
    >
      <div className="flex flex-wrap items-center gap-2.5 flex-1 min-w-[280px]">
        {/* Search Input */}
        <div className="relative flex-1 min-w-[180px] max-w-xs">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={values.searchQuery}
            onChange={(e) => onChange({ searchQuery: e.target.value })}
            placeholder="Search facility, event code, coordinates..."
            className="w-full pl-8 pr-7 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 text-xs placeholder:text-slate-500 focus:outline-none focus:border-amber-500 font-sans"
          />
          {values.searchQuery && (
            <button
              type="button"
              onClick={() => onChange({ searchQuery: "" })}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* State Selector */}
        <div className="min-w-[130px]">
          <select
            value={values.state}
            onChange={(e) => onChange({ state: e.target.value, district: "ALL" })}
            className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-amber-500"
          >
            <option value="ALL">All 36 States/UTs</option>
            {statesList.map((st) => (
              <option key={st.state_name} value={st.state_name}>
                {st.state_name}
              </option>
            ))}
          </select>
        </div>

        {/* District Selector */}
        {districtsList.length > 0 && values.state !== "ALL" && (
          <div className="min-w-[130px]">
            <select
              value={values.district}
              onChange={(e) => onChange({ district: e.target.value })}
              className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-amber-500"
            >
              <option value="ALL">All Districts</option>
              {districtsList.map((dt) => (
                <option key={dt.district_name} value={dt.district_name}>
                  {dt.district_name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Risk Level */}
        <div className="min-w-[110px]">
          <select
            value={values.riskLevel}
            onChange={(e) => onChange({ riskLevel: e.target.value })}
            className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-amber-500"
          >
            <option value="ALL">All Risk Levels</option>
            <option value="CRITICAL">Critical Threat</option>
            <option value="HIGH">High Risk</option>
            <option value="MODERATE">Moderate Risk</option>
            <option value="LOW">Low Hazard</option>
          </select>
        </div>

        {/* Horizon */}
        {showHorizon && (
          <div className="min-w-[120px]">
            <select
              value={values.horizon || "24h"}
              onChange={(e) => onChange({ horizon: e.target.value })}
              className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-amber-500"
            >
              {horizons.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.label}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3 shrink-0">
        {typeof totalMatches === "number" && (
          <span className="text-[11px] text-slate-400">
            Matching: <strong className="text-amber-400 font-mono">{totalMatches}</strong>
          </span>
        )}

        {onReset && (
          <button
            type="button"
            onClick={onReset}
            title="Reset Filters"
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-transparent hover:border-slate-700 transition-all flex items-center gap-1"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="text-[10px]">Reset</span>
          </button>
        )}
      </div>
    </div>
  );
}
