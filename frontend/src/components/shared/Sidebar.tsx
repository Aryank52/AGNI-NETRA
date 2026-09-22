"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/authContext";
import { 
  Map, Factory, Search, Activity, 
  AlertOctagon, CheckSquare, BarChart3, 
  FileText, ShieldCheck, Cpu, Settings,
  Flame, Bell, Compass, Building2, Eye,
  Sliders, Database, ShieldAlert, BookOpen, Globe, Layers, Radio,
  Pickaxe, GraduationCap, Shield, Terminal, Scale, ChevronLeft, ChevronRight, Lock
} from "lucide-react";

export interface SidebarProps {
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  className?: string;
}

export default function Sidebar({
  collapsed = false,
  onToggleCollapse,
  className = "",
}: SidebarProps) {
  const pathname = usePathname();
  const { user } = useAuth();
  const role = user?.role || "ANALYST";

  // 1. OPERATIONS
  const operationsNav = [
    { label: "Command Center", href: "/dashboard", icon: Map, badge: "88" },
    { label: "Live Intelligence", href: "/dashboard/events", icon: Flame, badge: "82" },
    { label: "Thermal Anomalies", href: "/dashboard/anomalies", icon: AlertOctagon, badge: "ANOM" },
    { label: "Alerts Queue", href: "/dashboard/alerts", icon: Bell, badge: "88" },
    { label: "Analyst Verification", href: "/dashboard/verification", icon: CheckSquare, badge: "6 HITL" },
  ];

  // 2. INTELLIGENCE
  const intelligenceNav = [
    { label: "JARVIS Command", href: "/jarvis", icon: Terminal, badge: "AI OPS" },
    { label: "Historical Baselines", href: "/dashboard/baselines", icon: Layers, badge: "6-YR" },
    { label: "Prevention Intelligence", href: "/dashboard/prevention", icon: ShieldAlert, badge: "ROOT" },
    { label: "Multi-Horizon Analytics", href: "/dashboard/analytics", icon: BarChart3, badge: "TRENDS" },
    { label: "Risk Assessment", href: "/dashboard/risk", icon: Shield, badge: "FORMULA" },
  ];

  // 3. GIS & ASSETS (Canonical counts preserved)
  const gisNav = [
    { label: "Live Geospatial Map", href: "/dashboard/atlas", icon: Globe, badge: "GIS" },
    { label: "Industrial Atlas", href: "/dashboard/atlas", icon: Building2, badge: "35.5k" },
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
    { label: "Ingestion Health", href: "/admin/data-sources", icon: Database, badge: "NRT" },
    { label: "Data Truth & Lineage", href: "/admin/data-truth", icon: Layers, badge: "TRUTH" },
    { label: "ML Governance", href: "/admin/models", icon: Cpu, badge: "CANDIDATE" },
    { label: "System Audit & Health", href: "/admin", icon: Settings, badge: "OPS" },
  ];

  // Role-specific navs
  const agencyNav = [
    { label: "Emergency Response", href: "/portal/agency", icon: ShieldAlert, badge: "OPS" },
    { label: "Active Alerts", href: "/dashboard/alerts", icon: Bell, badge: "88" },
    { label: "Priority Events", href: "/dashboard/events", icon: Flame, badge: "URGENT" },
    { label: "Operational Map", href: "/dashboard/atlas", icon: Map, badge: "GIS" },
    { label: "Incident Reports", href: "/dashboard/reports", icon: FileText },
  ];

  const publicNav = [
    { label: "Safety Overview", href: "/portal/public", icon: Eye, badge: "CITIZEN" },
    { label: "Hazard Alerts", href: "/portal/public#alerts", icon: Bell, badge: "PUBLIC" },
    { label: "Public Safety Map", href: "/portal/public#map", icon: Map, badge: "REGIONAL" },
    { label: "Citizen Guidance", href: "/portal/public#guidance", icon: ShieldCheck, badge: "GUIDE" },
  ];

  const renderNavGroup = (title: string, items: any[]) => (
    <div className="mb-4">
      {!collapsed && (
        <div className="px-3 mb-1.5 text-[10px] font-bold tracking-wider text-slate-500 uppercase font-mono flex items-center justify-between">
          <span>{title}</span>
        </div>
      )}
      <nav className="space-y-0.5">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive =
            pathname === item.href ||
            (item.href !== "/dashboard" && pathname.startsWith(item.href.split("?")[0].split("#")[0]));

          return (
            <Link
              key={item.label}
              href={item.href}
              title={collapsed ? item.label : undefined}
              className={`flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
                isActive
                  ? "bg-amber-500/15 text-amber-300 border border-amber-500/40 font-semibold shadow-sm"
                  : "text-slate-400 hover:bg-slate-800/80 hover:text-slate-200 border border-transparent"
              } ${collapsed ? "justify-center px-2" : ""}`}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <Icon
                  className={`w-3.5 h-3.5 shrink-0 ${
                    isActive ? "text-amber-400" : "text-slate-400"
                  }`}
                />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </div>

              {!collapsed && item.badge && (
                <span
                  className={`text-[9px] font-mono px-1.5 py-0.2 rounded shrink-0 ml-1.5 font-bold ${
                    item.badge.includes("HITL") || item.badge === "88" || item.badge === "82"
                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                      : item.badge === "CANDIDATE"
                      ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                      : "bg-slate-800 text-slate-400 border border-slate-700/60"
                  }`}
                >
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
    <aside
      className={`${
        collapsed ? "w-16" : "w-64"
      } bg-slate-950/95 border-r border-agni-border flex flex-col justify-between py-3 px-2 shrink-0 transition-all duration-200 h-full min-h-0 overflow-y-auto ${className}`}
    >
      <div>
        {/* Rail Collapse Toggle */}
        {onToggleCollapse && (
          <div className="flex items-center justify-end px-2 mb-2">
            <button
              type="button"
              onClick={onToggleCollapse}
              className="p-1 rounded text-slate-500 hover:text-slate-200 hover:bg-slate-900 transition-colors"
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {collapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
            </button>
          </div>
        )}

        {role === "AGENCY" ? (
          renderNavGroup("Emergency Response", agencyNav)
        ) : role === "PUBLIC" ? (
          renderNavGroup("Public Safety", publicNav)
        ) : role === "ADMIN" ? (
          <>
            {renderNavGroup("Operations", operationsNav)}
            {renderNavGroup("Intelligence", intelligenceNav)}
            {renderNavGroup("GIS & Cadastre", gisNav)}
            {renderNavGroup("Simulation", simulationNav)}
            {renderNavGroup("Reporting", reportingNav)}
            {renderNavGroup("Administration", systemNav)}
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
      </div>

      {/* Footer Invariants & Cadastre Semantics */}
      {!collapsed ? (
        <div className="px-3 pt-3 border-t border-slate-800/80 font-mono text-[10px] text-slate-500 space-y-1.5">
          <div className="flex items-center justify-between text-slate-400">
            <span>SOVEREIGN INDIA</span>
            <span className="text-emerald-400 font-bold">7,595 LGD</span>
          </div>
          <div className="flex items-center justify-between text-[9px] text-slate-500">
            <span>35,570 Facilities</span>
            <span>502 Power / 1,633 Units</span>
          </div>
          <div className="pt-1.5 border-t border-slate-900 flex items-center justify-between text-[9px]">
            <span className="text-red-400/80 font-bold flex items-center gap-1">
              <Lock className="w-2.5 h-2.5" /> GATE: BLOCKED
            </span>
            <span className="text-slate-500">HITL REQD</span>
          </div>
        </div>
      ) : (
        <div className="py-2 border-t border-slate-800/80 flex flex-col items-center gap-1" title="Operational Dispatch Gate Blocked">
          <Lock className="w-3.5 h-3.5 text-red-400" />
        </div>
      )}
    </aside>
  );
}
