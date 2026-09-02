"use client";

import React, { useState } from "react";
import { Layers, ChevronDown, ChevronUp, Flame, Factory, Zap, Pickaxe, Trees, MapPin } from "lucide-react";

export default function MapLegend() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="absolute bottom-6 left-4 z-20 font-sans">
      <div className="bg-agni-card/95 backdrop-blur-md border border-agni-border rounded-xl shadow-2xl overflow-hidden transition-all duration-300 w-64">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-3.5 py-2.5 flex items-center justify-between text-xs font-semibold text-slate-200 hover:bg-slate-800/60 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Layers className="w-3.5 h-3.5 text-amber-400" />
            <span className="tracking-wide">TACTICAL GIS LEGEND</span>
          </div>
          {isOpen ? <ChevronDown className="w-3.5 h-3.5 text-slate-400" /> : <ChevronUp className="w-3.5 h-3.5 text-slate-400" />}
        </button>

        {isOpen && (
          <div className="p-3 border-t border-slate-800 space-y-3 text-[11px] text-slate-300 animate-in fade-in slide-in-from-bottom-2">
            {/* Thermal Risk Tiers */}
            <div className="space-y-1.5">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Thermal Risk Levels
              </div>
              <div className="grid grid-cols-2 gap-1.5 font-mono text-[10px]">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-sm shadow-red-500/50 animate-pulse" />
                  <span className="text-red-400 font-bold">CRITICAL</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-orange-500 shadow-sm shadow-orange-500/50" />
                  <span className="text-orange-400 font-bold">HIGH</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-yellow-400" />
                  <span className="text-yellow-300">MODERATE</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  <span className="text-emerald-400">LOW</span>
                </div>
              </div>
            </div>

            {/* Spatial Intelligence Layers */}
            <div className="space-y-1.5 border-t border-slate-800/80 pt-2">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                Multi-Source Context Layers
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Factory className="w-3 h-3 text-cyan-400" />
                    <span>Industrial Facilities</span>
                  </div>
                  <span className="w-2 h-2 rounded bg-cyan-400" />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Zap className="w-3 h-3 text-amber-400" />
                    <span>CEA Power Stations</span>
                  </div>
                  <span className="w-2 h-2 rounded bg-amber-400" />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Pickaxe className="w-3 h-3 text-purple-400" />
                    <span>IBM Mining Blocks</span>
                  </div>
                  <span className="w-2 h-2 rounded bg-purple-400" />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Trees className="w-3 h-3 text-emerald-400" />
                    <span>Protected Areas (WII/FSI)</span>
                  </div>
                  <span className="w-2 h-2 rounded bg-emerald-500/60 border border-emerald-400" />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <MapPin className="w-3 h-3 text-lime-400" />
                    <span>ISRO Bhuvan LULC</span>
                  </div>
                  <span className="w-2 h-2 rounded bg-lime-500/50 border border-lime-400" />
                </div>
              </div>
            </div>

            {/* Administrative Hierarchy */}
            <div className="space-y-1 border-t border-slate-800/80 pt-2 text-[10px] text-slate-400 font-mono">
              <div className="flex items-center justify-between">
                <span>State Boundary</span>
                <span className="w-4 h-0.5 bg-slate-300" />
              </div>
              <div className="flex items-center justify-between">
                <span>District Boundary</span>
                <span className="w-4 h-0.5 border-b border-dashed border-slate-400" />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
