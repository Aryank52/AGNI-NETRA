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
  Sliders, Database, ShieldAlert, BookOpen, Globe, Layers, Radio
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  const commandCenter = [
    { label: "GIS Tactical Map", href: "/dashboard", icon: Map, badge: "NRT" },
    { label: "Mission Control (AGNI-SAT)", href: "/dashboard/mission-control", icon: Radio, badge: "SIM" },
    { label: "India Thermal Atlas", href: "/dashboard/atlas", icon: Globe, badge: "ATLAS" },
    { label: "Thermal Events", href: "/dashboard/events", icon: Flame },
    { label: "Incident Alerts", href: "/dashboard/alerts", icon: Bell, badge: "ALERT" },
  ];

  const intelligenceModules = [
    { label: "Candidate Discovery", href: "/dashboard/candidates", icon: Search, badge: "USP" },
    { label: "Persistent Sources", href: "/dashboard/persistent-sources", icon: Activity },
    { label: "Industrial Facilities", href: "/dashboard/facilities", icon: Factory },
    { label: "Thermal Baselines", href: "/dashboard/baselines", icon: Sliders },
    { label: "Anomaly Radar", href: "/dashboard/anomalies", icon: AlertOctagon },
    { label: "Risk Matrix", href: "/dashboard/risk", icon: ShieldAlert },
    { label: "Historical Trends", href: "/dashboard/analytics", icon: BarChart3 },
  ];

  const operations = [
    { label: "Analyst Verification", href: "/dashboard/verification", icon: CheckSquare, badge: "HITL" },
    { label: "Intelligence Reports", href: "/dashboard/reports", icon: FileText },
  ];

  const portals = [
    { label: "Research Portal", href: "/portal/research", icon: BookOpen },
    { label: "Industry Portal", href: "/portal/industry", icon: Building2 },
    { label: "Public Transparency", href: "/portal/public", icon: Eye },
    { label: "Data Ingestion Control", href: "/admin/data-sources", icon: Database, badge: "LIVE" },
    { label: "Model Registry", href: "/admin/models", icon: Cpu, badge: "ML" },
    { label: "Dataset Control", href: "/admin/datasets", icon: Layers, badge: "DATA" },
    { label: "Admin & Audit", href: "/admin", icon: Settings, minRole: "ADMIN" },
  ];

  const renderNavGroup = (title: string, items: any[]) => (
    <div className="mb-4">
      <div className="px-3 mb-1.5 text-[10px] font-bold tracking-wider text-slate-500 uppercase font-mono">
        {title}
      </div>
      <nav className="space-y-0.5">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
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
                    : item.badge === "ALERT"
                    ? "bg-red-500/20 text-red-300 border border-red-500/30"
                    : item.badge === "ATLAS"
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                    : item.badge === "ML"
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                    : item.badge === "DATA"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                    : item.badge === "SIM"
                    ? "bg-fuchsia-500/20 text-fuchsia-300 border border-fuchsia-500/30"
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
        {renderNavGroup("Intelligence & Analysis", intelligenceModules)}
        {renderNavGroup("Operations & HITL", operations)}
        {renderNavGroup("Specialized Portals", portals)}

        {/* AI & Remote Sensing Model Badge */}
        <div className="mt-4 px-3 py-2.5 rounded-xl bg-agni-card/70 border border-agni-border/60">
          <div className="flex items-center gap-2 mb-1 text-xs font-semibold text-slate-200">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>XGBoost v1.0 • SHAP</span>
          </div>
          <p className="text-[10px] text-slate-400 leading-tight">
            18-feature remote sensing tabular intelligence with TreeExplainer attributions.
          </p>
          <div className="mt-2 pt-1.5 border-t border-slate-800 flex items-center justify-between text-[10px] font-mono text-slate-400">
            <span>F1: <strong className="text-emerald-400">0.962</strong></span>
            <span>CV: <strong className="text-emerald-400">5-Fold</strong></span>
          </div>
        </div>
      </div>

      {/* Footer Provenance */}
      <div className="px-3 text-[10px] text-slate-500 border-t border-slate-800 pt-3 mt-4">
        <div>AGNI-NETRA Platform</div>
        <div className="text-[9px] text-slate-600">NASA FIRMS • ISRO Bhuvan • OpenStreetMap</div>
      </div>
    </aside>
  );
}
