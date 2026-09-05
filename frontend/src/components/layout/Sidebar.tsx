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
  Pickaxe, GraduationCap, Shield
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  // 1. COMMAND CENTER
  const commandCenter = [
    { label: "National Overview", href: "/dashboard", icon: Map, badge: "LIVE" },
    { label: "Live Hotspot Events", href: "/dashboard/events", icon: Flame, badge: "NRT" },
    { label: "Alert Queue", href: "/dashboard/alerts", icon: Bell, badge: "QUEUE" },
    { label: "Analyst Verification", href: "/dashboard/verification", icon: CheckSquare, badge: "HITL" },
  ];

  // 2. INTELLIGENCE
  const intelligence = [
    { label: "Thermal Anomalies", href: "/dashboard/anomalies", icon: AlertOctagon, badge: "RADAR" },
    { label: "Persistent Sources", href: "/dashboard/persistent-sources", icon: Activity, badge: "PERSIST" },
    { label: "Industrial Atlas", href: "/dashboard/atlas", icon: Globe, badge: "ATLAS" },
    { label: "Facilities Directory", href: "/dashboard/facilities", icon: Factory },
    { label: "Candidate Discovery", href: "/dashboard/candidates", icon: Search, badge: "USP" },
  ];

  // 3. ANALYTICS
  const analytics = [
    { label: "Multi-Horizon Analytics", href: "/dashboard/analytics", icon: BarChart3, badge: "2022-26" },
    { label: "Risk Assessment", href: "/dashboard/risk", icon: ShieldAlert, badge: "FORMULA" },
    { label: "Intelligence Reports", href: "/dashboard/reports", icon: FileText },
    { label: "Thermal Baselines", href: "/dashboard/baselines", icon: Layers, badge: "ENHANCED" },
  ];

  // 4. MISSION
  const mission = [
    { label: "AGNI-SAT Mission Control", href: "/dashboard/mission-control", icon: Radio, badge: "SIMULATION" },
  ];

  // 5. PORTALS
  const portals = [
    { label: "Public Safety Portal", href: "/portal/public", icon: Eye, badge: "CITIZEN" },
    { label: "Industry Compliance", href: "/portal/industry", icon: Building2, badge: "PLANT" },
    { label: "Research Open Data", href: "/portal/research", icon: GraduationCap, badge: "SCIENCE" },
  ];

  // 6. ADMINISTRATION (Restricted)
  const administration = [
    { label: "Data Ingestion", href: "/admin/data-sources", icon: Database, badge: "INGEST" },
    { label: "Model Governance", href: "/admin/models", icon: Cpu, badge: "REGISTRY" },
    { label: "Datasets & Lineage", href: "/admin/datasets", icon: Layers, badge: "DATA" },
    { label: "System Administration", href: "/admin", icon: Settings, badge: "GOV" },
  ];

  const renderNavGroup = (title: string, items: any[]) => (
    <div className="mb-4">
      <div className="px-3 mb-1.5 text-[10px] font-bold tracking-wider text-slate-400 uppercase font-mono flex items-center justify-between">
        <span>{title}</span>
      </div>
      <nav className="space-y-0.5">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href.split("?")[0]));

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
                  item.badge === "USP"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                    : item.badge === "HITL"
                    ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                    : item.badge === "ALERT" || item.badge === "QUEUE"
                    ? "bg-red-500/20 text-red-300 border border-red-500/30"
                    : item.badge === "ATLAS"
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                    : item.badge === "SIMULATION"
                    ? "bg-fuchsia-500/20 text-fuchsia-300 border border-fuchsia-500/30"
                    : item.badge === "RADAR"
                    ? "bg-orange-500/20 text-orange-300 border border-orange-500/30"
                    : item.badge === "CITIZEN"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : item.badge === "SCIENCE"
                    ? "bg-violet-500/20 text-violet-300 border border-violet-500/30"
                    : item.badge === "PLANT"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : item.badge === "GOV"
                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
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

  return (
    <aside className="w-64 bg-agni-slate/95 border-r border-agni-border flex flex-col justify-between py-4 px-3 shrink-0 hidden md:flex overflow-y-auto">
      <div>
        {renderNavGroup("Command Center", commandCenter)}
        {renderNavGroup("Intelligence", intelligence)}
        {renderNavGroup("Analytics", analytics)}
        {renderNavGroup("Mission", mission)}
        {renderNavGroup("Portals", portals)}
        {user?.role === "ADMIN" && renderNavGroup("Administration", administration)}

        {/* AI & Remote Sensing Model Provenance Card */}
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
