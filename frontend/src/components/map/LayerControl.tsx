"use client";

import React, { useState } from "react";
import { 
  Layers, Eye, EyeOff, Factory, Zap, 
  Pickaxe, Trees, MapPin, Flame, Sliders,
  RotateCcw, Check, X, Shield, FileCheck, Loader2
} from "lucide-react";

export interface GISLayerState {
  thermalEvents: boolean;
  industrialFacilities: boolean;
  powerStations: boolean;
  mining: boolean;
  protectedAreas: boolean;
  lulc: boolean;
  stateBoundaries: boolean;
  districtBoundaries: boolean;
  parivesh: boolean;
}

export type LayerOpacityState = Record<keyof GISLayerState, number>;

export const DEFAULT_GIS_LAYERS: GISLayerState = {
  thermalEvents: true,
  industrialFacilities: true,
  powerStations: true,
  mining: true,
  protectedAreas: true,
  lulc: true,
  stateBoundaries: true,
  districtBoundaries: true,
  parivesh: true,
};

export const DEFAULT_LAYER_OPACITIES: LayerOpacityState = {
  thermalEvents: 0.95,
  industrialFacilities: 0.85,
  powerStations: 0.9,
  mining: 0.85,
  protectedAreas: 0.7,
  lulc: 0.65,
  stateBoundaries: 0.6,
  districtBoundaries: 0.5,
  parivesh: 0.85,
};

interface LayerControlProps {
  layers: GISLayerState;
  opacities?: LayerOpacityState;
  onToggleLayer: (layerKey: keyof GISLayerState) => void;
  onChangeOpacity?: (layerKey: keyof GISLayerState, opacity: number) => void;
  onToggleAll?: (enable: boolean) => void;
  onResetDefaults?: () => void;
  counts?: Record<string, number>;
  loadingLayers?: Partial<Record<keyof GISLayerState, boolean>>;
}

export default function LayerControl({ 
  layers, 
  opacities = DEFAULT_LAYER_OPACITIES,
  onToggleLayer, 
  onChangeOpacity,
  onToggleAll,
  onResetDefaults,
  counts,
  loadingLayers = {}
}: LayerControlProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeOpacityKey, setActiveOpacityKey] = useState<keyof GISLayerState | null>(null);

  const layerItems: Array<{
    key: keyof GISLayerState;
    label: string;
    sublabel: string;
    icon: any;
    color: string;
    countDefault: number;
    countKey: string;
    provenance: string;
  }> = [
    {
      key: "thermalEvents",
      label: "Thermal Events & Risk",
      sublabel: "Active Multi-Pixel Hotspots",
      icon: Flame,
      color: "#ef4444",
      countDefault: 223,
      countKey: "thermal_events",
      provenance: "NASA FIRMS (VIIRS/MODIS)",
    },
    {
      key: "industrialFacilities",
      label: "Industrial Facilities",
      sublabel: "National Manufacturing Registry",
      icon: Factory,
      color: "#38bdf8",
      countDefault: 35684,
      countKey: "industrial_facilities",
      provenance: "OSM Industrial Cadastre",
    },
    {
      key: "powerStations",
      label: "CEA Power Stations",
      sublabel: "Thermal, Hydro & Gas Utilities",
      icon: Zap,
      color: "#f59e0b",
      countDefault: 1633,
      countKey: "power_stations",
      provenance: "Central Electricity Authority",
    },
    {
      key: "mining",
      label: "IBM Mining Intelligence",
      sublabel: "Auctioned Blocks & Leases",
      icon: Pickaxe,
      color: "#a855f7",
      countDefault: 119,
      countKey: "mining",
      provenance: "Indian Bureau of Mines",
    },
    {
      key: "protectedAreas",
      label: "Protected Areas & Forests",
      sublabel: "National Parks & Eco-Sensitive Zones",
      icon: Trees,
      color: "#10b981",
      countDefault: 11,
      countKey: "protected_areas",
      provenance: "WII / FSI ISFR",
    },
    {
      key: "lulc",
      label: "Bhuvan LULC Land Cover",
      sublabel: "Thematic Pilot Extent (50m)",
      icon: MapPin,
      color: "#84cc16",
      countDefault: 15,
      countKey: "lulc",
      provenance: "ISRO Bhuvan (Pilot Subset)",
    },
    {
      key: "stateBoundaries",
      label: "State / UT Boundaries",
      sublabel: "36 Administrative Territories",
      icon: Layers,
      color: "#94a3b8",
      countDefault: 36,
      countKey: "admin_states",
      provenance: "Survey of India / Bharat Atlas",
    },
    {
      key: "districtBoundaries",
      label: "District Boundaries",
      sublabel: "736 District Administrative Borders",
      icon: Layers,
      color: "#64748b",
      countDefault: 736,
      countKey: "admin_districts",
      provenance: "Survey of India / Bharat Atlas",
    },
    {
      key: "parivesh",
      label: "PARIVESH Clearances",
      sublabel: "Environmental Project Locations",
      icon: FileCheck,
      color: "#06b6d4",
      countDefault: 622,
      countKey: "parivesh",
      provenance: "MoEFCC PARIVESH Portal",
    },
  ];

  const activeCount = Object.values(layers).filter(Boolean).length;

  return (
    <div className="absolute top-4 right-4 z-20 font-sans">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900/95 hover:bg-slate-800 border border-slate-700/80 text-xs font-semibold text-slate-100 shadow-2xl backdrop-blur-md transition-all hover:scale-105"
        id="btn-map-layers-toggle"
      >
        <Layers className="w-4 h-4 text-amber-400" />
        <span className="font-bold tracking-wider">MAP LAYERS</span>
        <span className="px-1.5 py-0.2 rounded-full bg-amber-500/20 text-amber-300 font-mono text-[10px] font-bold border border-amber-500/30">
          {activeCount} / {layerItems.length}
        </span>
      </button>

      {isOpen && (
        <div className="mt-2 w-84 sm:w-96 bg-slate-950/95 border border-slate-800 rounded-2xl shadow-2xl p-3.5 backdrop-blur-xl animate-in fade-in slide-in-from-top-2 text-xs">
          {/* Header & Master Controls */}
          <div className="flex items-center justify-between pb-2.5 mb-2.5 border-b border-slate-800">
            <div>
              <div className="font-bold text-white tracking-wider text-xs uppercase flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-amber-400" />
                <span>Authoritative GIS Layers</span>
              </div>
              <div className="text-[10px] text-slate-400">PostgreSQL / PostGIS 3.4 Spatial Stack</div>
            </div>

            {/* Quick Actions: All ON, All OFF, Reset */}
            <div className="flex items-center gap-1.5 text-[11px] font-mono">
              {onToggleAll && (
                <>
                  <button
                    onClick={() => onToggleAll(true)}
                    className="px-2 py-0.5 rounded bg-slate-850 hover:bg-slate-800 text-amber-300 border border-slate-700 font-bold transition-colors"
                    title="Enable All Layers"
                  >
                    All ON
                  </button>
                  <button
                    onClick={() => onToggleAll(false)}
                    className="px-2 py-0.5 rounded bg-slate-850 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-700 transition-colors"
                    title="Disable All Layers"
                  >
                    All OFF
                  </button>
                </>
              )}
              {onResetDefaults && (
                <button
                  onClick={onResetDefaults}
                  className="p-1 rounded bg-slate-850 hover:bg-slate-800 text-slate-400 hover:text-amber-400 border border-slate-700 transition-colors"
                  title="Reset to Default Configuration"
                >
                  <RotateCcw className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>

          {/* Scrollable Layer List */}
          <div className="space-y-1.5 max-h-96 overflow-y-auto pr-1">
            {layerItems.map((item) => {
              const active = layers[item.key];
              const opacity = opacities[item.key] ?? 1.0;
              const isLoading = Boolean(loadingLayers[item.key]);
              const recordCount = counts?.[item.countKey] ?? item.countDefault;
              const Icon = item.icon;
              const isSliderOpen = activeOpacityKey === item.key;

              return (
                <div
                  key={item.key}
                  className={`rounded-xl border transition-all ${
                    active
                      ? "bg-slate-900/90 border-slate-700/80 text-white"
                      : "bg-slate-950/40 border-slate-850 text-slate-500"
                  }`}
                >
                  <div className="p-2.5 flex items-center justify-between gap-2">
                    {/* Layer Icon & Information */}
                    <div 
                      className="flex items-center gap-2.5 flex-1 min-w-0 cursor-pointer"
                      onClick={() => onToggleLayer(item.key)}
                    >
                      <div
                        className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 shadow-sm"
                        style={{ backgroundColor: `${item.color}22`, border: `1px solid ${item.color}44` }}
                      >
                        <Icon className="w-3.5 h-3.5" style={{ color: item.color }} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5">
                          <span className={`font-semibold text-xs truncate leading-tight ${active ? "text-slate-100" : "text-slate-500"}`}>
                            {item.label}
                          </span>
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800/80 text-amber-400 shrink-0">
                            {recordCount.toLocaleString()}
                          </span>
                        </div>
                        <div className="text-[10px] text-slate-400 truncate mt-0.5 flex items-center gap-1">
                          <span>{item.sublabel}</span>
                          <span>•</span>
                          <span className="text-slate-500 text-[9px]">{item.provenance}</span>
                        </div>
                      </div>
                    </div>

                    {/* Actions: Loading / Opacity Slider Toggle / Visibility Toggle */}
                    <div className="flex items-center gap-1.5 shrink-0">
                      {isLoading ? (
                        <Loader2 className="w-4 h-4 text-amber-400 animate-spin" />
                      ) : (
                        active && onChangeOpacity && (
                          <button
                            onClick={() => setActiveOpacityKey(isSliderOpen ? null : item.key)}
                            className={`p-1 rounded hover:bg-slate-800 transition-colors ${
                              isSliderOpen ? "text-amber-400" : "text-slate-400"
                            }`}
                            title={`Opacity: Math.round(opacity * 100)%`}
                          >
                            <Sliders className="w-3.5 h-3.5" />
                          </button>
                        )
                      )}

                      <button
                        onClick={() => onToggleLayer(item.key)}
                        className={`p-1 rounded transition-colors ${
                          active ? "text-emerald-400 hover:text-emerald-300" : "text-slate-600 hover:text-slate-400"
                        }`}
                        title={active ? "Hide Layer" : "Show Layer"}
                      >
                        {active ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* Inline Opacity Slider */}
                  {isSliderOpen && active && onChangeOpacity && (
                    <div className="px-3 pb-2.5 pt-1 border-t border-slate-800/80 flex items-center justify-between gap-3 text-[11px] font-mono animate-in fade-in">
                      <span className="text-slate-400 text-[10px]">Opacity</span>
                      <input
                        type="range"
                        min="0.1"
                        max="1.0"
                        step="0.05"
                        value={opacity}
                        onChange={(e) => onChangeOpacity(item.key, parseFloat(e.target.value))}
                        className="flex-1 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
                      />
                      <span className="text-amber-300 text-[10px] w-8 text-right font-bold">
                        {Math.round(opacity * 100)}%
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Footer note */}
          <div className="mt-3 pt-2 border-t border-slate-800 flex items-center justify-between text-[10px] text-slate-500">
            <span>Viewport-aware lazy loading</span>
            <span className="text-amber-500/80 font-mono">EPSG:4326 (WGS 84)</span>
          </div>
        </div>
      )}
    </div>
  );
}
