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
  Pickaxe
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  // Tier 1: COMMAND CENTER
  const commandCenter = [
    { label: "National Overview", href: "/dashboard", icon: Map, badge: "LIVE" },
    { label: "Live Thermal Intelligence", href: "/dashboard/events", icon: Flame, badge: "NRT" },
    { label: "Alerts", href: "/dashboard/alerts", icon: Bell, badge: "QUEUE" },
  ];

  // Tier 2: INTELLIGENCE
  const intelligence = [
    { label: "Thermal Analysis", href: "/dashboard/anomalies", icon: AlertOctagon, badge: "RADAR" },
    { label: "Industrial Atlas", href: "/dashboard/atlas", icon: Globe, badge: "ATLAS" },
    { label: "Mining Intelligence", href: "/dashboard/facilities?sector=Mining", icon: Pickaxe },
    { label: "Persistent Sources", href: "/dashboard/persistent-sources", icon: Activity, badge: "PERSIST" },
    { label: "Candidate Discovery", href: "/dashboard/candidates", icon: Search, badge: "USP" },
    { label: "Historical Analysis", href: "/dashboard/analytics", icon: BarChart3, badge: "2022-26" },
  ];

  // Tier 3: INVESTIGATION
  const investigation = [
    { label: "Investigation Desk", href: "/dashboard/events", icon: ShieldAlert },
    { label: "Analyst Verification", href: "/dashboard/verification", icon: CheckSquare, badge: "HITL" },
    { label: "Intelligence Reports", href: "/dashboard/reports", icon: FileText },
  ];

  // Tier 4: MAP & DATA
  const mapAndData = [
    { label: "Thermal Atlas", href: "/dashboard/atlas", icon: Globe },
    { label: "GIS Layers", href: "/dashboard", icon: Layers },
  ];

  // Tier 5: SATELLITE
  const satellite = [
    { label: "AGNI-SAT", href: "/dashboard/mission-control", icon: Radio, badge: "SIMULATION" },
  ];

  // Tier 6: SYSTEM (Hidden from unauthorized users)
  const system = [
    { label: "Ingestion", href: "/admin/data-sources", icon: Database, badge: "INGEST" },
    { label: "Models", href: "/admin/models", icon: Cpu, badge: "ML" },
    { label: "Datasets", href: "/admin/datasets", icon: Layers, badge: "DATA" },
    { label: "Administration", href: "/admin", icon: Settings, badge: "GOV" },
  ];

  const renderNavGroup = (title: string, items: any[]) => (
    <div className="mb-4">
      <div className="px-3 mb-1.5 text-[10px] font-bold tracking-wider text-slate-500 uppercase font-mono">
        {title}
      </div>
      <nav className="space-y-0.5">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href.split("?")[0]));

          return (
            <Link
              key={item.label}
              href={item.href}
              className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? "bg-amber-500/15 text-amber-400 border border-amber-500/30 shadow-sm"
                  : "text-slate-300 hover:bg-slate-800/70 hover:text-white"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-amber-400" : "text-slate-400"}`} />
                <span className="truncate">{item.label}</span>
              </div>
              {item.badge && (
                <span className={`text-[8px] uppercase font-mono px-1.5 py-0.2 rounded font-bold ${
                  item.badge === "USP"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                    : item.badge === "HITL"
                    ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                    : item.badge === "ALERT" || item.badge === "QUEUE"
                    ? "bg-red-500/20 text-red-300 border border-red-500/30"
                    : item.badge === "ATLAS"
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                    : item.badge === "ML"
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                    : item.badge === "DATA"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                    : item.badge === "SIMULATION"
                    ? "bg-fuchsia-500/20 text-fuchsia-300 border border-fuchsia-500/30"
                    : item.badge === "RADAR"
                    ? "bg-orange-500/20 text-orange-300 border border-orange-500/30"
                    : item.badge === "PUBLIC"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : item.badge === "GOV"
                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                    : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
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
        {renderNavGroup("Investigation", investigation)}
        {renderNavGroup("Map & Data", mapAndData)}
        {renderNavGroup("Satellite", satellite)}
        {user?.role === "ADMIN" && renderNavGroup("System", system)}

        {/* AI & Remote Sensing Model Badge */}
        <div className="mt-4 px-3 py-2.5 rounded-xl bg-agni-card/70 border border-agni-border/60">
          <div className="flex items-center gap-2 mb-1 text-xs font-semibold text-slate-200">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>XGBoost v3.0 • Platt Calibrated</span>
          </div>
          <p className="text-[10px] text-slate-400 leading-tight">
            18-feature remote sensing tabular classifier with TreeExplainer SHAP attributions.
          </p>
          <div className="mt-2 pt-1.5 border-t border-slate-800 flex items-center justify-between text-[10px] font-mono text-slate-400">
            <span>F1: <strong className="text-emerald-400">0.962</strong></span>
            <span>Brier: <strong className="text-emerald-400">0.038</strong></span>
          </div>
        </div>

        {/* Public & Transparency Portal Quick Navigation */}
        <div className="mt-3 px-3 py-2 rounded-lg bg-emerald-950/30 border border-emerald-500/20 flex items-center justify-between">
          <Link href="/portal/public" className="text-[11px] text-emerald-400 hover:text-emerald-300 font-medium flex items-center gap-1.5">
            <Eye className="w-3.5 h-3.5" />
            <span>Public Safety Portal</span>
          </Link>
          <span className="text-[9px] font-mono text-emerald-500">SAFE VIEW</span>
        </div>
      </div>

      {/* Footer Provenance */}
      <div className="px-3 text-[10px] text-slate-500 border-t border-slate-800 pt-3 mt-4">
        <div className="font-mono text-slate-400 font-bold">AGNI-NETRA v1.0</div>
        <div className="text-[9px] text-slate-500">Geospatial Thermal Intelligence</div>
      </div>
    </aside>
  );
}
