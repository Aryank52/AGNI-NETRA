"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/authContext";
import { UserRole } from "@/types";
import { fetchApi } from "@/lib/api";
import StatusBadge from "./StatusBadge";
import { 
  Flame, Lock, Search, X, Clock, Terminal, 
  MapPin, Factory, Zap, Shield, UserCheck, 
  ChevronDown, Bell, LogOut, Menu
} from "lucide-react";

export interface TopBarProps {
  onToggleSidebar?: () => void;
  className?: string;
}

export const ROLE_PROFILES: { role: UserRole; name: string; badge: string; color: string }[] = [
  { role: "ANALYST", name: "Analyst Portal", badge: "INTELLIGENCE", color: "text-blue-400 border-blue-500/30" },
  { role: "AGENCY", name: "Agency Response", badge: "EMERGENCY", color: "text-red-400 border-red-500/30" },
  { role: "PUBLIC", name: "Public Safety", badge: "CITIZEN", color: "text-emerald-400 border-emerald-500/30" },
  { role: "ADMIN", name: "System Admin", badge: "OBSERVABILITY", color: "text-purple-400 border-purple-500/30" },
];

export default function TopBar({ onToggleSidebar, className = "" }: TopBarProps) {
  const { user, switchRole, logout } = useAuth();
  const router = useRouter();

  // Dual Clocks (UTC and IST)
  const [missionClock, setMissionClock] = useState({ utc: "", ist: "" });
  const [roleMenuOpen, setRoleMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setMissionClock({
        utc: now.toISOString().substring(11, 19) + " UTC",
        ist: now.toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour12: false }) + " IST",
      });
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  // Search logic
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setSearchLoading(true);
      try {
        const res = await fetchApi<any>(`/gis/search?q=${encodeURIComponent(searchQuery.trim())}`);
        setSearchResults(res?.results || (Array.isArray(res) ? res : []));
      } catch (err) {
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const currentRole = user?.role || "ANALYST";

  return (
    <header
      className={`h-14 border-b border-agni-border bg-slate-950/90 backdrop-blur-md px-4 flex items-center justify-between gap-3 shrink-0 z-30 font-mono text-xs ${className}`}
    >
      {/* Left: Brand & Mobile Toggle */}
      <div className="flex items-center gap-3">
        {onToggleSidebar && (
          <button
            type="button"
            onClick={onToggleSidebar}
            className="md:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
            aria-label="Toggle navigation"
          >
            <Menu className="w-4 h-4" />
          </button>
        )}

        <Link href="/dashboard" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500/20 via-slate-900 to-red-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shadow-sm group-hover:border-amber-400 transition-all">
            <Flame className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-1.5 font-bold tracking-wider text-slate-100 group-hover:text-amber-300 transition-colors">
              <span>AGNI-NETRA</span>
              <span className="text-[10px] text-amber-400 font-sans font-medium hidden sm:inline">
                अग्नि-नेत्र
              </span>
            </div>
            <div className="text-[9px] text-slate-500 tracking-tight hidden md:block">
              Sovereign India AI Thermal Intelligence
            </div>
          </div>
        </Link>
      </div>

      {/* Middle: Live Clocks & Safety Gate Indicator */}
      <div className="hidden lg:flex items-center gap-4 text-[11px]">
        {/* Dual Clocks */}
        <div className="flex items-center gap-3 px-3 py-1 rounded-lg bg-slate-900/80 border border-slate-800">
          <div className="flex items-center gap-1.5 text-slate-300">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span className="font-bold">{missionClock.ist || "00:00:00 IST"}</span>
          </div>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400">{missionClock.utc || "00:00:00 UTC"}</span>
        </div>

        {/* Operational Dispatch Gate (Hard Invariant) */}
        <div
          title="ENABLE_OPERATIONAL_DISPATCH_GATE = False (Automated sirens / emergency dispatches permanently blocked by statutory policy)"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-950/20 border border-red-500/30 text-red-300"
        >
          <Lock className="w-3.5 h-3.5 text-red-400" />
          <span className="text-[10px] font-bold">DISPATCH GATE: BLOCKED</span>
        </div>
      </div>

      {/* Right: Institutional Search & Role Switcher */}
      <div className="flex items-center gap-2.5">
        {/* Quick Search Trigger */}
        <button
          type="button"
          onClick={() => setSearchOpen(true)}
          className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200 flex items-center gap-2 transition-colors"
        >
          <Search className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-[11px] hidden sm:inline">Search cadastre...</span>
          <kbd className="hidden md:inline text-[9px] px-1 rounded bg-slate-800 text-slate-400 border border-slate-700">
            ⌘K
          </kbd>
        </button>

        {/* JARVIS Quick Link */}
        <Link
          href="/jarvis"
          className="px-2.5 py-1.5 rounded-lg bg-amber-500/15 border border-amber-500/30 hover:border-amber-500/60 text-amber-300 flex items-center gap-1.5 transition-colors font-bold"
        >
          <Terminal className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-[11px] hidden md:inline">JARVIS</span>
        </Link>

        {/* Role Switcher Menu */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setRoleMenuOpen(!roleMenuOpen)}
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-200 transition-colors"
          >
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[11px] font-bold hidden sm:inline">{currentRole}</span>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {roleMenuOpen && (
            <div className="absolute right-0 mt-2 w-56 p-1.5 rounded-xl bg-slate-950 border border-slate-800 shadow-2xl z-50 animate-in fade-in slide-in-from-top-2">
              <div className="px-2.5 py-2 border-b border-slate-800 mb-1">
                <p className="text-[10px] text-slate-400">Authenticated Operational Profile</p>
                <p className="text-xs font-bold text-slate-200 truncate">{user?.full_name || "Analyst User"}</p>
              </div>

              <div className="space-y-0.5">
                {ROLE_PROFILES.map((prof) => (
                  <button
                    key={prof.role}
                    type="button"
                    onClick={() => {
                      switchRole(prof.role);
                      setRoleMenuOpen(false);
                    }}
                    className={`w-full px-2.5 py-1.5 rounded-lg text-left text-xs transition-all flex items-center justify-between ${
                      currentRole === prof.role
                        ? "bg-amber-500/15 text-amber-300 font-bold border border-amber-500/30"
                        : "text-slate-400 hover:bg-slate-900 hover:text-white"
                    }`}
                  >
                    <span>{prof.name}</span>
                    <span className={`text-[9px] px-1 rounded border font-mono ${prof.color}`}>
                      {prof.badge}
                    </span>
                  </button>
                ))}
              </div>

              <div className="mt-1 pt-1 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => {
                    logout();
                    setRoleMenuOpen(false);
                    router.push("/login");
                  }}
                  className="w-full px-2.5 py-1.5 rounded-lg text-left text-xs text-red-400 hover:bg-red-950/30 transition-all flex items-center gap-2"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Global Search Command Modal */}
      {searchOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-start justify-center p-4 pt-20">
          <div
            ref={searchRef}
            className="w-full max-w-xl rounded-xl bg-slate-950 border border-slate-800 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95"
          >
            <div className="p-3 border-b border-slate-800 flex items-center gap-2.5">
              <Search className="w-4 h-4 text-amber-400 shrink-0" />
              <input
                type="text"
                autoFocus
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search facilities, thermal events, coordinates, districts..."
                className="w-full bg-transparent text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none font-sans"
              />
              <button
                type="button"
                onClick={() => setSearchOpen(false)}
                className="p-1 rounded text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="max-h-80 overflow-y-auto divide-y divide-slate-800/50 p-1">
              {searchLoading ? (
                <div className="py-8 text-center text-slate-500 text-xs">
                  Querying PostGIS spatial cadastre across 35,570 facilities...
                </div>
              ) : searchResults.length > 0 ? (
                searchResults.map((res: any, idx) => (
                  <div
                    key={idx}
                    onClick={() => {
                      setSearchOpen(false);
                      if (res.latitude && res.longitude) {
                        router.push(`/dashboard?lat=${res.latitude}&lon=${res.longitude}`);
                      } else if (res.id) {
                        router.push(`/dashboard/events/${res.id}`);
                      }
                    }}
                    className="p-2.5 hover:bg-slate-900 rounded-lg cursor-pointer transition-colors flex items-center justify-between"
                  >
                    <div>
                      <h5 className="text-xs font-bold text-slate-200">{res.name || res.title || res.event_code}</h5>
                      <p className="text-[11px] text-slate-400">{res.state || res.category || "Geospatial Entity"}</p>
                    </div>
                    {res.coordinates && (
                      <span className="text-[10px] text-slate-500 font-mono">
                        {res.coordinates[0]?.toFixed(2)}, {res.coordinates[1]?.toFixed(2)}
                      </span>
                    )}
                  </div>
                ))
              ) : searchQuery.length >= 2 ? (
                <div className="py-8 text-center text-slate-500 text-xs">
                  No cadastral entities found matching "{searchQuery}".
                </div>
              ) : (
                <div className="py-6 px-4 text-slate-500 text-xs leading-relaxed font-sans">
                  Type at least 2 characters to search across 35,570 industrial facilities, 502 power stations (1,633 generating units), and clustered thermal events.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
