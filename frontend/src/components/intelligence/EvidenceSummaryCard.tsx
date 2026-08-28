import React from "react";
import { ThermalEvent } from "@/types";
import { Satellite, Shield, MapPin, Calendar, Clock, Activity, CheckCircle, Database } from "lucide-react";

interface EvidenceSummaryCardProps {
  event: ThermalEvent;
}

export default function EvidenceSummaryCard({ event }: EvidenceSummaryCardProps) {
  const isIndustrial = event.prediction?.predicted_class?.includes("Industrial") || event.prediction?.predicted_class === "Gas Flare";
  const hasKnownFac = event.facility_status === "KNOWN" || event.facility_status === "VERIFIED";

  return (
    <div className="p-4 rounded-xl bg-agni-card border border-agni-border space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
          <Shield className="w-4 h-4 text-amber-400" />
          Multi-Sensor Evidence Summary
        </h4>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
          Source Provenance
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        {/* Remote Sensing Signal */}
        <div className="p-3 rounded-lg bg-slate-900/70 border border-slate-800/80 space-y-1">
          <div className="text-slate-400 flex items-center gap-1.5 font-semibold text-[11px]">
            <Satellite className="w-3.5 h-3.5 text-cyan-400" />
            SATELLITE THERMAL OBSERVATION
          </div>
          <div className="text-slate-200 font-medium">
            NASA VIIRS NOAA-20 / MODIS
          </div>
          <div className="text-[11px] text-slate-400 font-mono">
            {event.detection_count} detections • Peak FRP: <strong className="text-amber-400">{event.max_frp.toFixed(1)} MW</strong>
          </div>
        </div>

        {/* Spatial Association */}
        <div className="p-3 rounded-lg bg-slate-900/70 border border-slate-800/80 space-y-1">
          <div className="text-slate-400 flex items-center gap-1.5 font-semibold text-[11px]">
            <MapPin className="w-3.5 h-3.5 text-amber-400" />
            GEOSPATIAL FACILITY CONTEXT
          </div>
          <div className="text-slate-200 font-medium">
            {hasKnownFac ? "Known Industrial Facility" : (event.facility_status === "CANDIDATE" ? "Candidate Industrial Source (Discovered)" : "Uncataloged Thermal Location")}
          </div>
          <div className="text-[11px] text-slate-400">
            {event.nearest_facility_distance_m !== undefined ? `Distance to facility boundary: ${event.nearest_facility_distance_m.toFixed(0)}m` : "No proximate registered facility"}
          </div>
        </div>

        {/* Temporal Persistence */}
        <div className="p-3 rounded-lg bg-slate-900/70 border border-slate-800/80 space-y-1">
          <div className="text-slate-400 flex items-center gap-1.5 font-semibold text-[11px]">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            TEMPORAL RECURRENCE DYNAMICS
          </div>
          <div className="text-slate-200 font-medium">
            {event.features && event.features.persistence_score > 3.0 ? "Persistent Multiday Emitter" : "Transient Episode"}
          </div>
          <div className="text-[11px] text-slate-400 font-mono">
            Persistence Index: <strong className="text-white">{event.features?.persistence_score?.toFixed(1) || "N/A"}</strong> / 10.0
          </div>
        </div>

        {/* LULC Ground Truth */}
        <div className="p-3 rounded-lg bg-slate-900/70 border border-slate-800/80 space-y-1">
          <div className="text-slate-400 flex items-center gap-1.5 font-semibold text-[11px]">
            <Database className="w-3.5 h-3.5 text-purple-400" />
            LAND COVER (LULC) CONTEXT
          </div>
          <div className="text-slate-200 font-medium">
            {event.landcover_class || "Industrial"}
          </div>
          <div className="text-[11px] text-slate-400">
            ISRO Bhuvan / ESA WorldCover 10m
          </div>
        </div>
      </div>
    </div>
  );
}
