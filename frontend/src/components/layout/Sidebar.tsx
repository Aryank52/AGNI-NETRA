"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/authContext";
import { 
  Map, Factory, Search, Activity, 
  AlertOctagon, CheckSquare, BarChart3, 
  FileText, ShieldCheck, Cpu, Settings
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  const navItems = [
    { label: "GIS Command Map", href: "/dashboard", icon: Map, minRole: "PUBLIC" },
    { label: "Industrial Facilities", href: "/dashboard/facilities", icon: Factory, minRole: "RESEARCHER" },
    { label: "Persistent Sources", href: "/dashboard/persistent-sources", icon: Activity, minRole: "PUBLIC" },
    { label: "Candidate Discovery", href: "/dashboard/candidates", icon: Search, minRole: "ANALYST", badge: "USP" },
    { label: "Thermal Anomalies", href: "/dashboard/anomalies", icon: AlertOctagon, minRole: "RESEARCHER" },
    { label: "Analyst Verification", href: "/dashboard/verification", icon: CheckSquare, minRole: "ANALYST", badge: "HITL" },
    { label: "Analytics & Trends", href: "/dashboard/analytics", icon: BarChart3, minRole: "PUBLIC" },
    { label: "Intelligence Reports", href: "/dashboard/reports", icon: FileText, minRole: "RESEARCHER" },
    { label: "System & Admin", href: "/admin", icon: Settings, minRole: "ADMIN" },
  ];

  return (
    <aside className="w-64 bg-agni-slate/95 border-r border-agni-border flex flex-col justify-between py-4 px-3 shrink-0 hidden md:flex">
      <div className="space-y-6">
        {/* Navigation Group */}
        <div>
          <div className="px-3 mb-2 text-[10px] font-semibold tracking-wider text-slate-500 uppercase">
            Intelligence Modules
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? "bg-amber-500/15 text-amber-400 border border-amber-500/30 shadow-sm"
                      : "text-slate-300 hover:bg-slate-800/70 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${isActive ? "text-amber-400" : "text-slate-400"}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[9px] uppercase font-mono px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* AI & Remote Sensing Model Badge */}
        <div className="px-3 py-3 rounded-xl bg-agni-card/70 border border-agni-border/60">
          <div className="flex items-center gap-2 mb-1.5 text-xs font-semibold text-slate-200">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span>XGBoost v1.0 • SHAP</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-tight">
            Multi-sensor tabular thermal intelligence with TreeExplainer Shapley attributions.
          </p>
          <div className="mt-2.5 pt-2 border-t border-slate-800 flex items-center justify-between text-[10px] font-mono text-slate-400">
            <span>ACCURACY: <strong className="text-emerald-400">96.2%</strong></span>
            <span>MACRO F1: <strong className="text-emerald-400">0.958</strong></span>
          </div>
        </div>
      </div>

      {/* Footer Provenance */}
      <div className="px-3 text-[11px] text-slate-500 border-t border-slate-800 pt-3">
        <div>Smart India Hackathon 2026</div>
        <div className="text-[10px] text-slate-600">Problem SIH26162 • ISRO / NASA FIRMS</div>
      </div>
    </aside>
  );
}
