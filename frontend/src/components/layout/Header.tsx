"use client";

import React from "react";
import Link from "next/link";
import { useAuth } from "@/lib/authContext";
import { UserRole } from "@/types";
import { 
  Flame, ShieldAlert, Radio, UserCheck, 
  Layers, LogOut, ChevronDown, CheckCircle2, AlertTriangle
} from "lucide-react";

const ROLES: UserRole[] = ["ANALYST", "RESEARCHER", "INDUSTRY", "AGENCY", "PUBLIC", "ADMIN"];

export default function Header() {
  const { user, switchRole, logout } = useAuth();
  const [roleMenuOpen, setRoleMenuOpen] = React.useState(false);

  return (
    <header className="h-16 bg-agni-slate/95 border-b border-agni-border px-4 lg:px-6 flex items-center justify-between z-30 backdrop-blur-md sticky top-0">
      {/* Brand Title */}
      <div className="flex items-center gap-3">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-500 via-orange-600 to-red-600 p-0.5 shadow-lg shadow-orange-500/20 group-hover:scale-105 transition-transform flex items-center justify-center">
            <Flame className="w-6 h-6 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-wider text-white">AGNI-NETRA</span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
                v1.0 • SIH26162
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              AI Industrial Thermal Risk & Anomaly Intelligence
            </p>
          </div>
        </Link>
      </div>

      {/* Live Tactical Status Ticker */}
      <div className="hidden xl:flex items-center gap-6 text-xs text-slate-300 bg-agni-card/80 px-4 py-1.5 rounded-full border border-agni-border">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="font-mono text-emerald-400">LIVE FEED:</span>
          <span>NASA VIIRS NOAA-20 / MODIS</span>
        </div>
        <div className="h-3 w-px bg-slate-700" />
        <div className="flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-amber-400" />
          <span>SPATIAL CLUSTER: <strong className="text-white">DBSCAN 1.5km</strong></span>
        </div>
        <div className="h-3 w-px bg-slate-700" />
        <div className="flex items-center gap-1.5">
          <Radio className="w-3.5 h-3.5 text-cyan-400" />
          <span>EXPLAINER: <strong className="text-white">SHAP TreeExplainer</strong></span>
        </div>
      </div>

      {/* Role Switcher & User Profile */}
      <div className="flex items-center gap-3">
        {/* Role Selector Dropdown */}
        <div className="relative">
          <button
            onClick={() => setRoleMenuOpen(!roleMenuOpen)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-agni-card hover:bg-slate-800 border border-agni-border text-xs transition-colors"
          >
            <UserCheck className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-slate-400">Portal:</span>
            <span className="font-semibold text-amber-400">{user?.role || "ANALYST"}</span>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {roleMenuOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-agni-card border border-agni-border rounded-xl shadow-2xl p-2 z-50 animate-in fade-in slide-in-from-top-2">
              <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                Switch Decision Portal
              </div>
              <div className="py-1 space-y-1">
                {ROLES.map((r) => (
                  <button
                    key={r}
                    onClick={() => {
                      switchRole(r);
                      setRoleMenuOpen(false);
                    }}
                    className={`w-full flex items-center justify-between px-3 py-2 text-xs rounded-lg transition-colors ${
                      user?.role === r
                        ? "bg-amber-500/20 text-amber-300 font-semibold border border-amber-500/30"
                        : "text-slate-300 hover:bg-slate-800"
                    }`}
                  >
                    <span>{r} PORTAL</span>
                    {user?.role === r && <CheckCircle2 className="w-3.5 h-3.5 text-amber-400" />}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User Card */}
        <div className="flex items-center gap-2 bg-agni-card/60 px-3 py-1.5 rounded-lg border border-agni-border text-xs hidden md:flex">
          <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center font-bold text-[10px] text-white">
            {user?.full_name?.charAt(0) || "U"}
          </div>
          <div className="text-left">
            <div className="font-medium text-slate-200 leading-none">{user?.full_name || "Analyst"}</div>
            <div className="text-[10px] text-slate-400 leading-tight truncate max-w-[120px]">{user?.organization || "CPCB"}</div>
          </div>
        </div>

        <Link
          href="/login"
          className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
          title="Sign Out / Switch Account"
        >
          <LogOut className="w-4 h-4" />
        </Link>
      </div>
    </header>
  );
}
