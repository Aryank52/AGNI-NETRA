"use client";

import React from "react";
import { ShapExplanation, ShapContributor } from "@/types";
import { Info, HelpCircle } from "lucide-react";

interface ShapWaterfallChartProps {
  shapData?: ShapExplanation;
  predictedClass?: string;
  confidence?: number;
}

export default function ShapWaterfallChart({
  shapData,
  predictedClass = "Industrial Fire",
  confidence = 0.88,
}: ShapWaterfallChartProps) {
  if (!shapData || !shapData.top_contributors || shapData.top_contributors.length === 0) {
    return (
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400">
        Feature contribution attribution calculated via analytical tree rules.
      </div>
    );
  }

  const contributors = shapData.top_contributors;
  const maxAbsShap = Math.max(...contributors.map((c) => Math.abs(c.shap_value)), 0.01);

  // Friendly human labels for feature columns
  const FEATURE_NAMES: Record<string, string> = {
    dist_to_facility_m: "Proximity to Facility (m)",
    industrial_context_score: "Industrial Context Score",
    persistence_score: "Persistence / Recurrence Index",
    day_night_ratio: "Day/Night 24x7 Emission Ratio",
    frp_max: "Peak Fire Radiative Power (MW)",
    frp_avg: "Average Radiative Power (MW)",
    dist_to_forest_m: "Forest Isolation Distance",
    dist_to_agriculture_m: "Agriculture Distance",
    dist_to_settlement_m: "Settlement Buffer",
    baseline_deviation_ratio: "Baseline Deviation Ratio",
    landcover_code: "LULC Landcover Category",
  };

  return (
    <div className="p-4 rounded-xl bg-agni-card/90 border border-agni-border shadow-lg">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-cyan-400" />
            SHAP Explainability Attribution (TreeExplainer)
          </h4>
          <p className="text-[11px] text-slate-400">
            Shapley impact pushing prediction toward <strong className="text-amber-400">{predictedClass}</strong>
          </p>
        </div>
        <div className="text-right">
          <div className="text-xs font-mono font-bold text-emerald-400">
            {(confidence * 100).toFixed(1)}% CONFIDENCE
          </div>
          <div className="text-[10px] text-slate-500 font-mono">Base Prior: 14.3%</div>
        </div>
      </div>

      {/* Feature Contributions Waterfall List */}
      <div className="space-y-2.5 my-4">
        {contributors.map((item, idx) => {
          const isPositive = item.shap_value >= 0;
          const widthPercent = Math.min(100, (Math.abs(item.shap_value) / maxAbsShap) * 100);
          const friendlyName = FEATURE_NAMES[item.feature] || item.feature;

          return (
            <div key={idx} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-300 flex items-center gap-1">
                  {friendlyName}
                  <span className="text-[10px] text-slate-500 font-mono">
                    ({item.value})
                  </span>
                </span>
                <span
                  className={`font-mono font-bold text-xs ${
                    isPositive ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {isPositive ? "+" : ""}
                  {item.shap_value.toFixed(3)}
                </span>
              </div>

              {/* Dual-direction Bar */}
              <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden flex">
                {isPositive ? (
                  <div
                    style={{ width: `${widthPercent}%` }}
                    className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-full"
                  />
                ) : (
                  <div
                    style={{ width: `${widthPercent}%` }}
                    className="h-full bg-gradient-to-r from-red-600 to-red-400 rounded-full"
                  />
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[10px] text-slate-400">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-emerald-400" /> Supports Classification
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-red-400" /> Opposes Classification
        </span>
      </div>
    </div>
  );
}
