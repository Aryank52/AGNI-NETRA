"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/authContext";
import { 
  Map, Factory, Search, Activity, 
  AlertOctagon, CheckSquare, BarChart3, 
  FileText, ShieldCheck, Cpu, Settings,
  Flame, Bell, Compass, Building2, Eye,
  Sliders, Database, ShieldAlert, BookOpen, Globe, Layers, Radio,
  Pickaxe, GraduationCap, Shield, Terminal, Scale
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  // 1. OPERATIONS
  const operationsNav = [
    { label: "Command Center", href: "/dashboard", icon: Map, badge: "LIVE" },
    { label: "Live Intelligence", href: "/dashboard/events", icon: Flame, badge: "NRT" },
    { label: "Thermal Events", href: "/dashboard/anomalies", icon: AlertOctagon, badge: "RADAR" },
    { label: "Alerts Queue", href: "/dashboard/alerts", icon: Bell, badge: "QUEUE" },
    { label: "Analyst Verification", href: "/dashboard/verification", icon: CheckSquare, badge: "HITL" },
  ];

  // 2. INTELLIGENCE
  const intelligenceNav = [
    { label: "JARVIS Command", href: "/jarvis", icon: Terminal, badge: "AI OPS" },
    { label: "Historical Baselines", href: "/dashboard/baselines", icon: Layers, badge: "HIST" },
    { label: "Prevention Intelligence", href: "/dashboard/prevention", icon: ShieldAlert, badge: "NEW" },
    { label: "Multi-Horizon Analytics", href: "/dashboard/analytics", icon: BarChart3, badge: "TRENDS" },
    { label: "Risk Assessment", href: "/dashboard/risk", icon: Shield, badge: "FORMULA" },
  ];

  // 3. GIS & ASSETS
  const gisNav = [
    { label: "Live Geospatial Map", href: "/dashboard", icon: Globe, badge: "GIS" },
    { label: "Industrial Atlas", href: "/dashboard/atlas", icon: Building2, badge: "ATLAS" },
    { label: "Facility Directory", href: "/dashboard/facilities", icon: Factory },
    { label: "Candidate Discovery", href: "/dashboard/candidates", icon: Search, badge: "USP" },
    { label: "Persistent Sources", href: "/dashboard/persistent-sources", icon: Activity, badge: "PERSIST" },
  ];

  // 4. SIMULATION
  const simulationNav = [
    { label: "AGNI-SAT Digital Twin", href: "/dashboard/mission-control", icon: Radio, badge: "SIM" },
  ];

  // 5. REPORTING
  const reportingNav = [
    { label: "Intelligence Reports", href: "/dashboard/reports", icon: FileText },
    { label: "Compliance Reports", href: "/dashboard/reports?tab=compliance", icon: Scale, badge: "AUDIT" },
  ];

  // 6. SYSTEM (Admin)
  const systemNav = [
    { label: "Ingestion Health", href: "/admin/data-sources", icon: Database, badge: "INGEST" },
    { label: "Data Truth & Lineage", href: "/admin/data-truth", icon: Layers, badge: "TRUTH" },
    { label: "ML Governance", href: "/admin/models", icon: Cpu, badge: "REGISTRY" },
    { label: "Audit & Security", href: "/admin/datasets", icon: ShieldCheck, badge: "AUDIT" },
    { label: "System Health", href: "/admin", icon: Settings, badge: "OPS" },
  ];

  // 7. AGENCY EMERGENCY RESPONSE (Agency Specific)
  const agencyEmergencyResponse = [
    { label: "Response Center", href: "/portal/agency", icon: ShieldAlert, badge: "OPS" },
    { label: "Active Alerts", href: "/dashboard/alerts", icon: Bell, badge: "LIVE" },
    { label: "Priority Incidents", href: "/dashboard/events", icon: Flame, badge: "URGENT" },
    { label: "Operational Map", href: "/dashboard", icon: Map, badge: "GIS" },
    { label: "Regional Baselines", href: "/dashboard/baselines", icon: Layers, badge: "STATE" },
    { label: "Incident Reports", href: "/dashboard/reports", icon: FileText, badge: "ARCHIVE" },
  ];

  // 8. PUBLIC SAFETY (Public Specific)
  const publicSafetyNav = [
    { label: "Safety Status Overview", href: "/portal/public", icon: Eye, badge: "STATUS" },
    { label: "Current Hazard Alerts", href: "/portal/public#alerts", icon: Bell, badge: "ADVISORY" },
    { label: "Public Safety Map", href: "/portal/public#map", icon: Map, badge: "REGIONAL" },
    { label: "Citizen Safety Guidance", href: "/portal/public#guidance", icon: ShieldCheck, badge: "GUIDE" },
  ];

  const renderNavGroup = (title: string, items: any[]) => (
    <div className="mb-4">
      <div className="px-3 mb-1.5 text-[10px] font-bold tracking-wider text-slate-400 uppercase font-mono flex items-center justify-between">
        <span>{title}</span>
      </div>
      <nav className="space-y-0.5">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href.split("?")[0].split("#")[0]));

          return (
            <Link
              key={item.label}
              href={item.href}
              className={`flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? "bg-amber-500/15 text-amber-300 border border-amber-500/40 font-semibold"
                  : "text-slate-300 hover:bg-slate-800/80 hover:text-white border border-transparent"
              }`}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <Icon className={`w-3.5 h-3.5 shrink-0 ${isActive ? "text-amber-400" : "text-slate-400"}`} />
                <span className="truncate">{item.label}</span>
              </div>
              {item.badge && (
                <span className={`text-[8px] uppercase font-mono px-1.5 py-0.2 rounded font-bold shrink-0 ml-1.5 ${
                  item.badge === "OPS" || item.badge === "RESPONSE" || item.badge === "URGENT"
                    ? "bg-red-500/20 text-red-300 border border-red-500/30"
                    : item.badge === "INTEL" || item.badge === "HITL"
                    ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                    : item.badge === "STATUS" || item.badge === "GUIDE" || item.badge === "PUBLIC"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : item.badge === "ADMIN" || item.badge === "GOV" || item.badge === "REGISTRY"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                    : item.badge === "ATLAS"
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                    : "bg-slate-700/50 text-slate-300 border border-slate-600/40"
                }`}>
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>
    </div>
  );

  const role = user?.role || "ANALYST";

  return (
    <aside className="w-64 bg-agni-slate/95 border-r border-agni-border flex flex-col justify-between py-4 px-3 shrink-0 hidden md:flex h-full min-h-0 overflow-y-auto">
      <div>
        {/* Role-Specific Navigation Groups */}
        {role === "AGENCY" ? (
          <>
            {renderNavGroup("Emergency Response", agencyEmergencyResponse)}
          </>
        ) : role === "PUBLIC" ? (
          <>
            {renderNavGroup("Public Safety", publicSafetyNav)}
          </>
        ) : role === "ADMIN" ? (
          <>
            {renderNavGroup("Operations", operationsNav)}
            {renderNavGroup("Intelligence", intelligenceNav)}
            {renderNavGroup("GIS & Cadastre", gisNav)}
            {renderNavGroup("Simulation", simulationNav)}
            {renderNavGroup("Reporting", reportingNav)}
            {renderNavGroup("System Administration", systemNav)}
          </>
        ) : (
          /* Default: ANALYST */
          <>
            {renderNavGroup("Operations", operationsNav)}
            {renderNavGroup("Intelligence", intelligenceNav)}
            {renderNavGroup("GIS & Cadastre", gisNav)}
            {renderNavGroup("Simulation", simulationNav)}
            {renderNavGroup("Reporting", reportingNav)}
          </>
        )}

        {/* Role-Aware Operational Status Notice */}
        {role === "AGENCY" ? (
          <div className="mt-4 px-3 py-2.5 rounded-xl bg-red-950/20 border border-red-500/30 space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-xs font-bold text-red-300">
                <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
                <span>Response Readiness</span>
              </div>
              <span className="text-[9px] font-mono px-1 rounded bg-red-500/20 text-red-400 border border-red-500/30">
                LEVEL 1
              </span>
            </div>
            <p className="text-[10px] text-slate-400 leading-tight">
              Emergency operations protocol active. Alert triage synchronized with CPCB & State Disaster Authorities.
            </p>
          </div>
        ) : role === "PUBLIC" ? (
          <div className="mt-4 px-3 py-2.5 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-300">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>Public Safety Verified</span>
              </div>
              <span className="text-[9px] font-mono px-1 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                CITIZEN
              </span>
            </div>
            <p className="text-[10px] text-slate-400 leading-tight">
              Non-technical safety advisories derived from verified earth observation telemetry.
            </p>
          </div>
        ) : (
          /* ANALYST & ADMIN: Calibrated AI Model Provenance Card */
          <div className="mt-4 px-3 py-2.5 rounded-xl bg-slate-900/90 border border-agni-border">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-200">
                <Cpu className="w-3.5 h-3.5 text-amber-400" />
                <span>Calibrated 7-Class AI</span>
              </div>
              <span className="text-[9px] font-mono px-1 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                ACTIVE
              </span>
            </div>
            <p className="text-[10px] text-slate-400 leading-tight">
              18-feature remote sensing XGBoost classifier with TreeExplainer SHAP attributions.
            </p>
            <div className="mt-2 pt-1.5 border-t border-slate-800 space-y-0.5 text-[10px] font-mono text-slate-400">
              <div className="flex justify-between">
                <span>Tier 1 Selective:</span>
                <strong className="text-emerald-400">97.2%</strong>
              </div>
              <div className="flex justify-between">
                <span>Spatial CV:</span>
                <strong className="text-emerald-400">94.3%</strong>
              </div>
              <div className="flex justify-between">
                <span>Temporal Holdout:</span>
                <strong className="text-slate-300">69.9%</strong>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer Provenance & Safe Gating Notice */}
      <div className="px-3 text-[10px] text-slate-500 border-t border-slate-800 pt-3 mt-4 space-y-1">
        <div className="flex items-center justify-between font-mono">
          <span className="text-slate-400 font-bold">AGNI-NETRA v1.0</span>
          <span className="text-[9px] text-emerald-500 font-semibold">HITL GATED</span>
        </div>
        <div className="text-[9px] text-slate-500">
          Statutory dispatch disabled by policy
        </div>
      </div>
    </aside>
  );
}
