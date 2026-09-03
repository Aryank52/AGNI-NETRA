"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/authContext";
import { UserRole } from "@/types";
import { fetchApi } from "@/lib/api";
import AgniNetraLogo from "@/components/common/AgniNetraLogo";
import { 
  Flame, ShieldAlert, Radio, UserCheck, 
  Layers, LogOut, ChevronDown, CheckCircle2, AlertTriangle,
  Search, X, MapPin, Factory, Zap, Pickaxe, Trees, Shield, Loader2
} from "lucide-react";

const ROLES: UserRole[] = ["ANALYST", "RESEARCHER", "INDUSTRY", "AGENCY", "PUBLIC", "ADMIN"];

interface SearchResultItem {
  id: string;
  type: string;
  title: string;
  subtitle: string;
  state?: string;
  district?: string;
  coordinates: [number, number];
  bbox?: [number, number, number, number];
  zoom?: number;
}

export default function Header() {
  const { user, switchRole, logout } = useAuth();
  const router = useRouter();
  const [roleMenuOpen, setRoleMenuOpen] = useState(false);

  // Global Search State
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const searchContainerRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<any>(null);

  // Click outside to close search dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setSearchOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced search query
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.trim().length < 2) {
      setSearchResults([]);
      setSearchLoading(false);
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setSearchLoading(true);
      try {
        const data = await fetchApi<{ results: SearchResultItem[] }>(
          `/gis/search?q=${encodeURIComponent(searchQuery.trim())}`
        );
        setSearchResults(data?.results || []);
        setSearchOpen(true);
      } catch (err) {
        console.warn("Global search failed:", err);
      } finally {
        setSearchLoading(false);
      }
    }, 280);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery]);

  const handleSelectResult = (item: SearchResultItem) => {
    setSearchOpen(false);
    setSearchQuery("");

    if (item.type === "EVENT") {
      router.push(`/dashboard/events/${item.id}`);
    } else if (item.type === "STATE") {
      router.push(`/dashboard?state=${encodeURIComponent(item.title)}`);
    } else if (item.type === "DISTRICT") {
      router.push(`/dashboard?state=${encodeURIComponent(item.state || "")}&district=${encodeURIComponent(item.title)}`);
    } else if (item.type === "FACILITY" || item.type === "POWER_STATION") {
      router.push(`/dashboard/atlas?search=${encodeURIComponent(item.title)}`);
    } else if (item.type === "MINING") {
      router.push(`/dashboard?state=${encodeURIComponent(item.state || "")}&lat=${item.coordinates[1]}&lon=${item.coordinates[0]}`);
    } else {
      router.push(`/dashboard?lat=${item.coordinates[1]}&lon=${item.coordinates[0]}`);
    }
  };

  const getResultIcon = (type: string) => {
    switch (type) {
      case "EVENT":
        return <Flame className="w-4 h-4 text-red-400" />;
      case "POWER_STATION":
        return <Zap className="w-4 h-4 text-yellow-400" />;
      case "FACILITY":
        return <Factory className="w-4 h-4 text-cyan-400" />;
      case "MINING":
        return <Pickaxe className="w-4 h-4 text-purple-400" />;
      case "PROTECTED_AREA":
        return <Trees className="w-4 h-4 text-emerald-400" />;
      case "COORDINATES":
      case "STATE":
      case "DISTRICT":
      default:
        return <MapPin className="w-4 h-4 text-amber-400" />;
    }
  };

  return (
    <header className="h-16 bg-agni-slate/95 border-b border-agni-border px-4 lg:px-6 flex items-center justify-between z-30 backdrop-blur-md sticky top-0 font-sans">
      {/* Brand Title */}
      <div className="flex items-center gap-3 shrink-0">
        <Link href="/" className="group">
          <AgniNetraLogo size="md" subtext="GEOSPATIAL THERMAL INTELLIGENCE" />
        </Link>
      </div>

      {/* Center: Global Multi-Entity Search Bar */}
      <div ref={searchContainerRef} className="relative flex-1 max-w-md mx-4 hidden md:block">
        <div className="relative flex items-center">
          <Search className="w-4 h-4 absolute left-3 text-slate-400 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => {
              if (searchResults.length > 0) setSearchOpen(true);
            }}
            placeholder="Search event ID, facility, power plant, coords, district, mine..."
            className="w-full pl-9 pr-8 py-1.5 bg-slate-900/90 border border-slate-700/80 rounded-xl text-xs text-slate-100 placeholder:text-slate-400 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 transition-all shadow-inner"
            id="global-search-input"
          />
          {searchLoading ? (
            <Loader2 className="w-3.5 h-3.5 absolute right-2.5 text-amber-400 animate-spin" />
          ) : searchQuery ? (
            <button
              onClick={() => {
                setSearchQuery("");
                setSearchResults([]);
              }}
              className="absolute right-2.5 text-slate-400 hover:text-white"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          ) : null}
        </div>

        {/* Search Results Dropdown */}
        {searchOpen && searchResults.length > 0 && (
          <div className="absolute left-0 right-0 mt-2 bg-slate-950/95 border border-slate-700/90 rounded-2xl shadow-2xl p-2 z-50 backdrop-blur-xl animate-in fade-in max-h-96 overflow-y-auto">
            <div className="px-2 py-1 text-[10px] font-mono text-slate-400 uppercase tracking-wider border-b border-slate-800">
              Matches ({searchResults.length})
            </div>
            <div className="py-1 space-y-1">
              {searchResults.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleSelectResult(item)}
                  className="flex items-center gap-3 p-2 rounded-xl hover:bg-slate-900 cursor-pointer transition-colors group"
                >
                  <div className="w-7 h-7 rounded-lg bg-slate-900 flex items-center justify-center shrink-0 border border-slate-800">
                    {getResultIcon(item.type)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="font-semibold text-xs text-white group-hover:text-amber-400 truncate">
                      {item.title}
                    </div>
                    <div className="text-[10px] text-slate-400 truncate">
                      {item.subtitle}
                    </div>
                  </div>
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 uppercase shrink-0">
                    {item.type}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Role Switcher & User Profile */}
      <div className="flex items-center gap-3 shrink-0">
        {/* Role Selector Dropdown */}
        <div className="relative">
          <button
            onClick={() => setRoleMenuOpen(!roleMenuOpen)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-agni-card hover:bg-slate-800 border border-agni-border text-xs transition-colors"
          >
            <UserCheck className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-slate-400 hidden sm:inline">Portal:</span>
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
        <div className="flex items-center gap-2 bg-agni-card/60 px-3 py-1.5 rounded-lg border border-agni-border text-xs hidden sm:flex">
          <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center font-bold text-[10px] text-white">
            {user?.full_name?.charAt(0) || "A"}
          </div>
          <div className="text-left">
            <div className="font-medium text-slate-200 leading-none">{user?.full_name || "Analyst"}</div>
            <div className="text-[10px] text-slate-400 leading-tight truncate max-w-[120px]">{user?.organization || "CPCB / SPCB"}</div>
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
