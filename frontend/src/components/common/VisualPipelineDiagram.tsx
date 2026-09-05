"use client";

import React, { useState } from "react";
import { 
  Satellite, Flame, Layers, Cpu, ShieldAlert, 
  UserCheck, FileText, ArrowRight, CheckCircle2, ChevronDown
} from "lucide-react";

interface PipelineStep {
  id: string;
  stepNumber: string;
  title: string;
  subtitle: string;
  badge: string;
  icon: any;
  color: string;
  description: string;
  evidence: string[];
  metrics: { label: string; value: string }[];
}

export default function VisualPipelineDiagram() {
  const [activeStepIndex, setActiveStepIndex] = useState<number>(0);

  const steps: PipelineStep[] = [
    {
      id: "observation",
      stepNumber: "01",
      title: "Satellite Acquisition",
      subtitle: "Multi-Sensor Thermal Radiance",
      badge: "SATELLITE INGEST",
      icon: Satellite,
      color: "text-cyan-400 border-cyan-500/30 bg-cyan-500/10",
      description: "NASA FIRMS operational downlinks from VIIRS (SNPP, NOAA-20, NOAA-21) at 375m resolution and MODIS at 1km resolution ingested in 15-minute intervals.",
      evidence: [
        "Fire Radiative Power (MW)",
        "Brightness Temperature (Kelvin)",
        "Geodetic Coordinates & Scan Angle",
        "Solar Zenith Day/Night Flag"
      ],
      metrics: [
        { label: "Cycle Interval", value: "15 min" },
        { label: "Sensors", value: "VIIRS + MODIS" }
      ]
    },
    {
      id: "clustering",
      stepNumber: "02",
      title: "Spatiotemporal DBSCAN",
      subtitle: "Cluster Aggregation & Filtering",
      badge: "SPATIAL CLUSTERING",
      icon: Flame,
      color: "text-amber-400 border-amber-500/30 bg-amber-500/10",
      description: "Dense thermal observation points are aggregated into unified spatiotemporal clusters using DBSCAN with 2.0 km radius and 24-hour temporal window.",
      evidence: [
        "Centroid Latitude & Longitude",
        "Point Count in Cluster",
        "Peak and Mean FRP Calculation",
        "Cluster Spatial Convex Hull"
      ],
      metrics: [
        { label: "Spatial Epsilon", value: "2.0 km" },
        { label: "Time Window", value: "24 Hours" }
      ]
    },
    {
      id: "enrichment",
      stepNumber: "03",
      title: "GIS Context Enrichment",
      subtitle: "Multi-Source Spatial Overlay",
      badge: "POSTGIS ENRICHMENT",
      icon: Layers,
      color: "text-blue-400 border-blue-500/30 bg-blue-500/10",
      description: "PostGIS spatial joins intersect event centroids with 35,684 OSM industrial plants, CEA power stations, 414 IBM mining leases, and ISRO Bhuvan land use rasters.",
      evidence: [
        "Nearest Industrial Facility & Distance",
        "Mining Lease Boundary Proximity",
        "State/District Administrative Containment",
        "Eco-Sensitive Zone (ESZ) 10km Buffer"
      ],
      metrics: [
        { label: "Spatial Layers", value: "9 PostGIS Layers" },
        { label: "Facilities", value: "35,684 OSM" }
      ]
    },
    {
      id: "classification",
      stepNumber: "04",
      title: "7-Class XGBoost Inference",
      subtitle: "Probabilistic Source Segregation",
      badge: "CALIBRATED ML",
      icon: Cpu,
      color: "text-purple-400 border-purple-500/30 bg-purple-500/10",
      description: "Balanced Platt-calibrated XGBoost classifier evaluates 18 spatiotemporal features to segregate industrial fires and flares from agricultural or forest burning.",
      evidence: [
        "Calibrated Multi-Class Probabilities",
        "SHAP TreeExplainer Feature Contributors",
        "Shannon Entropy Confidence Score",
        "Baseline FRP Deviation Ratio"
      ],
      metrics: [
        { label: "Taxonomy", value: "7 Classes" },
        { label: "Features", value: "18 Dimensions" }
      ]
    },
    {
      id: "risk",
      stepNumber: "05",
      title: "Transparent Multi-Factor Risk",
      subtitle: "Rule-Based Hazard Scoring (0–100)",
      badge: "RISK MATRIX",
      icon: ShieldAlert,
      color: "text-rose-400 border-rose-500/30 bg-rose-500/10",
      description: "Formula evaluates Thermal Intensity (30%), Anomaly Deviation (25%), Distance to Human Settlements (20%), Environmental Sensitivity (15%), and Persistence (10%).",
      evidence: [
        "Categorical Risk: LOW / MODERATE / HIGH / CRITICAL",
        "Proximity to High-Population Settlements",
        "Chronic Thermal Recurrence Pattern",
        "Audit Reasons for Hazard Classification"
      ],
      metrics: [
        { label: "Max Score", value: "100 Pts" },
        { label: "Risk Tiers", value: "4 Levels" }
      ]
    },
    {
      id: "verification",
      stepNumber: "06",
      title: "Human-In-The-Loop Verification",
      subtitle: "Analyst Decision Authority",
      badge: "ANALYST HITL",
      icon: UserCheck,
      color: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10",
      description: "Certified operational analysts inspect the evidence dossier, review SHAP explainability, and validate or override model predictions before dispatch escalation.",
      evidence: [
        "Analyst Confirmation or Reclassification",
        "Investigation Dossier Timestamp",
        "Cryptographic Audit Log Entry",
        "Immutable State Machine Transition"
      ],
      metrics: [
        { label: "Dispatch Gate", value: "FALSE (Safe)" },
        { label: "Queues", value: "3 Tiers" }
      ]
    },
    {
      id: "dossier",
      stepNumber: "07",
      title: "Certified Intelligence Output",
      subtitle: "PDF Dossier & Agency Dissemination",
      badge: "DECISION SUPPORT",
      icon: FileText,
      color: "text-amber-400 border-amber-500/30 bg-amber-500/10",
      description: "Generates authenticated PDF intelligence dossiers and standardized GeoJSON feature collections for state pollution boards, district emergency cells, and industry.",
      evidence: [
        "Tamper-Evident SHA-256 Report Verification",
        "Multi-Page High-Resolution GIS Cartography",
        "Complete Regulatory Compliance Lineage",
        "Agency REST API & GeoJSON Data Feed"
      ],
      metrics: [
        { label: "Format", value: "PDF + GeoJSON" },
        { label: "API Sync", value: "REST v1" }
      ]
    }
  ];

  const currentStep = steps[activeStepIndex];

  return (
    <div className="w-full rounded-2xl bg-slate-950/80 border border-slate-800/90 p-6 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <div className="text-[10px] font-mono text-amber-400 uppercase tracking-widest font-bold">
            END-TO-END OPERATIONAL ARCHITECTURE
          </div>
          <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight mt-0.5">
            Geospatial Thermal Intelligence Pipeline Flow
          </h2>
        </div>
        <div className="text-xs font-mono text-slate-400">
          Step <span className="text-amber-400 font-bold">{currentStep.stepNumber}</span> of 07:{" "}
          <span className="text-slate-200">{currentStep.title}</span>
        </div>
      </div>

      {/* Horizontal Pipeline Steps Track */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
        {steps.map((s, idx) => {
          const StepIcon = s.icon;
          const isActive = idx === activeStepIndex;
          const isPassed = idx < activeStepIndex;

          return (
            <button
              key={s.id}
              onClick={() => setActiveStepIndex(idx)}
              className={`p-3 rounded-xl border text-left transition-all relative flex flex-col justify-between ${
                isActive
                  ? "bg-slate-900 border-amber-500/50 shadow-md shadow-amber-500/5 ring-1 ring-amber-500/30"
                  : isPassed
                  ? "bg-slate-900/50 border-slate-800 hover:border-slate-700"
                  : "bg-slate-950 border-slate-800/60 hover:border-slate-700/60 opacity-70"
              }`}
            >
              <div className="flex items-center justify-between w-full mb-2">
                <span className={`text-[10px] font-mono font-bold ${isActive ? "text-amber-400" : "text-slate-500"}`}>
                  {s.stepNumber}
                </span>
                <StepIcon className={`w-3.5 h-3.5 ${isActive ? "text-amber-400" : "text-slate-400"}`} />
              </div>
              <div className="text-xs font-bold text-slate-200 leading-tight truncate">
                {s.title}
              </div>
              <div className="text-[10px] text-slate-400 truncate mt-0.5">
                {s.badge}
              </div>
            </button>
          );
        })}
      </div>

      {/* Detailed Active Step Inspector */}
      <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl border ${currentStep.color}`}>
              <currentStep.icon className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  {currentStep.badge}
                </span>
                <span className="text-xs text-slate-400">{currentStep.subtitle}</span>
              </div>
              <h3 className="text-base sm:text-lg font-bold text-white mt-1">
                {currentStep.title}
              </h3>
            </div>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            {currentStep.description}
          </p>

          <div className="space-y-2 pt-1">
            <div className="text-[11px] font-mono font-semibold text-slate-400 uppercase tracking-wider">
              Extracted Evidence & Indicators:
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {currentStep.evidence.map((item, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-slate-300 bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                  <CheckCircle2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <span className="truncate">{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Operational Specification Stats */}
        <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col justify-between space-y-4">
          <div>
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider font-bold mb-3">
              Specification Benchmarks
            </div>
            <div className="space-y-3">
              {currentStep.metrics.map((m, i) => (
                <div key={i} className="flex items-center justify-between border-b border-slate-800/60 pb-2">
                  <span className="text-xs text-slate-400">{m.label}</span>
                  <span className="text-xs font-mono font-bold text-amber-400">{m.value}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
            <button
              onClick={() => setActiveStepIndex((prev) => (prev > 0 ? prev - 1 : steps.length - 1))}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition-colors"
            >
              Previous Step
            </button>
            <button
              onClick={() => setActiveStepIndex((prev) => (prev < steps.length - 1 ? prev + 1 : 0))}
              className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-slate-950 text-xs font-bold transition-colors flex items-center gap-1.5"
            >
              <span>Next Stage</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
