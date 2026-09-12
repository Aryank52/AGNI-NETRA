"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/authContext";
import { UserRole } from "@/types";
import { fetchApi } from "@/lib/api";
import AgniNetraLogo from "@/components/common/AgniNetraLogo";
import { 
  Flame, ShieldAlert, Radio, UserCheck, 
  Layers, LogOut, ChevronDown, CheckCircle2, AlertTriangle,
  Search, X, MapPin, Factory, Zap, Pickaxe, Trees, Shield, Loader2,
  Clock, Menu, Bell, BarChart3, Globe, Cpu, Eye, Building2, GraduationCap,
  Map as MapIcon, Settings, Sparkles
} from "lucide-react";

export interface PortalOption {
  role: UserRole;
  name: string;
  description: string;
  href: string;
  badge: string;
  badgeColor: string;
}

export const PORTAL_OPTIONS: PortalOption[] = [
  {
    role: "ANALYST",
    name: "ANALYST PORTAL",
    description: "Full Intelligence Analysis & Verification",
    href: "/dashboard",
    badge: "INTELLIGENCE",
    badgeColor: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  },
  {
    role: "AGENCY",
    name: "AGENCY PORTAL",
    description: "Emergency Response & Incident Operations",
    href: "/portal/agency",
    badge: "RESPONSE",
    badgeColor: "bg-red-500/20 text-red-300 border-red-500/30",
  },
  {
    role: "PUBLIC",
    name: "PUBLIC PORTAL",
    description: "Safety Alerts & Public Impact",
    href: "/portal/public",
    badge: "PUBLIC SAFETY",
    badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  },
  {
    role: "ADMIN",
    name: "ADMIN PORTAL",
    description: "System Administration & National Observability",
    href: "/admin",
    badge: "OBSERVABILITY",
    badgeColor: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  },
];

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
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [missionClock, setMissionClock] = useState({ utc: "", ist: "" });

  useEffect(() => {
    const updateClocks = () => {
      const now = new Date();
      setMissionClock({
        utc: now.toISOString().substring(11, 19) + " UTC",
        ist: now.toLocaleTimeString("en-IN", { timeZone: "Asia/Kolkata", hour12: false }) + " IST",
      });
    };
    updateClocks();
    const timer = setInterval(updateClocks, 1000);
    return () => clearInterval(timer);
  }, []);

  // Global Search State & Institutional Command Palette
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [mobileSearchOpen, setMobileSearchOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const searchContainerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const mobileSearchInputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<any>(null);

  // Load recent searches from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem("agni_netra_recent_searches");
      if (saved) setRecentSearches(JSON.parse(saved));
    } catch {}
  }, []);

  const saveRecentSearch = (term: string) => {
    if (!term || !term.trim()) return;
    try {
      const clean = term.trim();
      const updated = [clean, ...recentSearches.filter((s) => s.toLowerCase() !== clean.toLowerCase())].slice(0, 5);
      setRecentSearches(updated);
      localStorage.setItem("agni_netra_recent_searches", JSON.stringify(updated));
    } catch {}
  };

  // Global Ctrl+K / Cmd+K listener
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setSearchOpen(true);
        setTimeout(() => {
          searchInputRef.current?.focus();
        }, 50);
      }
      if (e.key === "Escape") {
        setSearchOpen(false);
        setMobileSearchOpen(false);
      }
    };
    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => window.removeEventListener("keydown", handleGlobalKeyDown);
  }, []);

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
      setSelectedIndex(-1);
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
        setSelectedIndex(-1);
      } catch (err) {
        console.warn("Global search failed:", err);
      } finally {
        setSearchLoading(false);
      }
    }, 250);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery]);

  const handleSelectResult = (item: SearchResultItem) => {
    saveRecentSearch(item.title || searchQuery);
    setSearchOpen(false);
    setMobileSearchOpen(false);
    setSearchQuery("");
    setSelectedIndex(-1);

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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!searchResults.length) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % searchResults.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + searchResults.length) % searchResults.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (selectedIndex >= 0 && searchResults[selectedIndex]) {
        handleSelectResult(searchResults[selectedIndex]);
      } else if (searchResults.length > 0) {
        handleSelectResult(searchResults[0]);
      }
    }
  };

  // Grouped search results for structured presentation
  const groupedResults = useMemo(() => {
    const groups: { key: string; label: string; items: SearchResultItem[] }[] = [
      { key: "events", label: "THERMAL HOTSPOTS & CLUSTERS", items: [] },
      { key: "facilities", label: "INDUSTRIAL FACILITIES & POWER UTILITIES", items: [] },
      { key: "geography", label: "ADMINISTRATIVE BOUNDARIES & COORDS", items: [] },
      { key: "mining_pa", label: "MINERAL LEASES & ECOLOGICAL RESERVES", items: [] },
    ];

    searchResults.forEach((item) => {
      if (item.type === "EVENT") groups[0].items.push(item);
      else if (item.type === "FACILITY" || item.type === "POWER_STATION") groups[1].items.push(item);
      else if (item.type === "STATE" || item.type === "DISTRICT" || item.type === "COORDINATES") groups[2].items.push(item);
      else groups[3].items.push(item);
    });

    return groups.filter((g) => g.items.length > 0);
  }, [searchResults]);

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

      {/* Center: Global Multi-Entity Command Palette Search Bar */}
      <div ref={searchContainerRef} className="relative flex-1 max-w-lg mx-4 hidden md:block">
        <div className="relative flex items-center">
          <Search className="w-4 h-4 absolute left-3 text-slate-400 pointer-events-none" />
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => {
              setSearchOpen(true);
            }}
            placeholder="Search event ID, plant, power station, coords, state, mine..."
            className="w-full pl-9 pr-20 py-1.5 bg-slate-900/90 border border-slate-700/80 rounded-xl text-xs text-slate-100 placeholder:text-slate-400 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 transition-all shadow-inner"
            id="global-search-input"
          />

          <div className="absolute right-2 flex items-center gap-1.5 pointer-events-none">
            {searchLoading ? (
              <Loader2 className="w-3.5 h-3.5 text-amber-400 animate-spin" />
            ) : searchQuery ? (
              <button
                type="button"
                onClick={() => {
                  setSearchQuery("");
                  setSearchResults([]);
                  setSelectedIndex(-1);
                }}
                className="pointer-events-auto text-slate-400 hover:text-white"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            ) : (
              <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[9px] font-mono text-slate-400 bg-slate-800/90 border border-slate-700/80 rounded shadow-xs">
                Ctrl K
              </kbd>
            )}
          </div>
        </div>

        {/* Command Palette Results Dropdown */}
        {searchOpen && (
          <div className="absolute left-0 right-0 mt-2 bg-slate-950/98 border border-slate-700/90 rounded-2xl shadow-2xl p-2.5 z-50 backdrop-blur-2xl animate-in fade-in max-h-[28rem] overflow-y-auto">
            {/* Header info bar */}
            <div className="px-2 py-1 flex items-center justify-between text-[10px] font-mono text-slate-400 border-b border-slate-800 pb-1.5">
              <span>INSTITUTIONAL GEOSPATIAL SEARCH</span>
              <span>{searchResults.length > 0 ? `${searchResults.length} matches` : "Navigation Palette"}</span>
            </div>

            {/* If user is typing and no matches */}
            {!searchLoading && searchQuery.trim().length >= 2 && searchResults.length === 0 && (
              <div className="p-4 text-center text-xs text-slate-400 space-y-1">
                <p>No geospatial entities matching &quot;<strong className="text-white">{searchQuery}</strong>&quot;</p>
                <p className="text-[11px] text-slate-500">Try searching by state name (e.g., Gujarat), district (e.g., Jamnagar), or coordinates (22.47, 69.83).</p>
              </div>
            )}

            {/* Empty search: Show Recent Searches & Quick Suggested Shortcuts */}
            {!searchQuery && (
              <div className="p-2 space-y-3">
                {recentSearches.length > 0 && (
                  <div>
                    <div className="text-[10px] font-mono uppercase text-slate-500 mb-1.5 px-1">
                      Recent Searches
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {recentSearches.map((term, i) => (
                        <button
                          key={i}
                          onClick={() => {
                            setSearchQuery(term);
                            searchInputRef.current?.focus();
                          }}
                          className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-[11px] text-slate-300 hover:text-amber-400 font-mono transition-colors"
                        >
                          {term}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <div className="text-[10px] font-mono uppercase text-slate-500 mb-1.5 px-1">
                    Quick Spatial Targets
                  </div>
                  <div className="grid grid-cols-2 gap-1.5 text-xs">
                    <button
                      onClick={() => {
                        setSearchQuery("Gujarat");
                        searchInputRef.current?.focus();
                      }}
                      className="p-2 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800/80 text-left text-slate-300 hover:text-white transition-colors"
                    >
                      <div className="font-bold text-amber-400 font-mono">Gujarat</div>
                      <div className="text-[10px] text-slate-400">Petrochemical & Flaring Hub</div>
                    </button>
                    <button
                      onClick={() => {
                        setSearchQuery("Bhilai");
                        searchInputRef.current?.focus();
                      }}
                      className="p-2 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800/80 text-left text-slate-300 hover:text-white transition-colors"
                    >
                      <div className="font-bold text-cyan-400 font-mono">Bhilai Steel</div>
                      <div className="text-[10px] text-slate-400">Integrated Metallurgy Cadastre</div>
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Grouped Search Results */}
            {groupedResults.map((group) => (
              <div key={group.key} className="mt-2 first:mt-1">
                <div className="px-2 py-1 text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider bg-slate-900/40 rounded-md mb-1">
                  {group.label}
                </div>
                <div className="space-y-1">
                  {group.items.map((item) => {
                    const flatIdx = searchResults.findIndex((r) => r.id === item.id);
                    const isKeyboardSelected = flatIdx === selectedIndex;
                    return (
                      <div
                        key={item.id}
                        onClick={() => handleSelectResult(item)}
                        className={`flex items-center gap-3 p-2 rounded-xl cursor-pointer transition-colors group ${
                          isKeyboardSelected
                            ? "bg-slate-800/95 border border-amber-500/50 shadow-sm"
                            : "hover:bg-slate-900 border border-transparent"
                        }`}
                      >
                        <div className="w-7 h-7 rounded-lg bg-slate-900 flex items-center justify-center shrink-0 border border-slate-800">
                          {getResultIcon(item.type)}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="font-semibold text-xs text-white group-hover:text-amber-400 truncate flex items-center gap-2">
                            <span>{item.title}</span>
                            {item.state && (
                              <span className="text-[10px] font-mono text-slate-400 font-normal truncate">
                                ({item.state})
                              </span>
                            )}
                          </div>
                          <div className="text-[10px] text-slate-400 truncate">
                            {item.subtitle}
                          </div>
                        </div>
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 uppercase shrink-0">
                          {item.type}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}

            {/* Footer keyboard shortcut tip */}
            <div className="pt-2 mt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono text-slate-500 px-2">
              <span>Navigate: <kbd className="px-1 py-0.2 bg-slate-800 rounded text-slate-400">↑</kbd> <kbd className="px-1 py-0.2 bg-slate-800 rounded text-slate-400">↓</kbd></span>
              <span>Select: <kbd className="px-1 py-0.2 bg-slate-800 rounded text-slate-400">Enter</kbd></span>
              <span>Close: <kbd className="px-1 py-0.2 bg-slate-800 rounded text-slate-400">Esc</kbd></span>
            </div>
          </div>
        )}
      </div>

      {/* Operational Stream Indicator & Mission Clocks */}
      <div className="hidden lg:flex items-center gap-2.5 shrink-0">
        <Link
          href="/jarvis"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 hover:border-amber-500/50 text-amber-300 text-[11px] font-mono font-bold transition-all shadow-sm group"
          title="Launch JARVIS AI Command & Intelligence Orchestration Layer"
        >
          <Sparkles className="w-3.5 h-3.5 text-amber-400 group-hover:scale-110 transition-transform" />
          <span className="tracking-wide">JARVIS</span>
          <span className="text-[9px] px-1 py-0.2 rounded bg-amber-500/20 text-amber-300 font-normal">AI OPS</span>
        </Link>

        <div 
          className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-orange-500/10 border border-orange-500/30 text-orange-300 text-[11px] font-mono font-bold tracking-wider shadow-sm"
          title="Active Operational Geography: Sovereign Territory of India (Authoritative PostGIS Boundary Containment)"
          id="india-scope-badge"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse"></span>
          <span>SCOPE: INDIA</span>
          <span className="text-[9px] px-1 py-0.2 rounded bg-orange-500/20 text-orange-300 font-normal">36 STATES/UTS</span>
        </div>

        <div className="hidden xl:flex items-center gap-2 px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[11px] font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="font-bold tracking-wider">FIRMS STREAM ACTIVE</span>
        </div>

        <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-300">
          <Clock className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-white font-bold">{missionClock.utc}</span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400">{missionClock.ist}</span>
        </div>
      </div>

      {/* Role Switcher & User Profile & Mobile Toggle */}
      <div className="flex items-center gap-2.5 shrink-0">
        {/* Mobile Search Button */}
        <button
          onClick={() => {
            setMobileSearchOpen(true);
            setTimeout(() => mobileSearchInputRef.current?.focus(), 50);
          }}
          className="p-1.5 md:hidden text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 border border-slate-700"
          aria-label="Open Global Search"
        >
          <Search className="w-5 h-5 text-amber-400" />
        </button>

        {/* Mobile Nav Toggle */}
        <button
          onClick={() => setMobileNavOpen(!mobileNavOpen)}
          className="p-1.5 md:hidden text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 border border-slate-700"
          aria-label="Toggle Navigation Menu"
        >
          {mobileNavOpen ? <X className="w-5 h-5 text-amber-400" /> : <Menu className="w-5 h-5" />}
        </button>

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
            <div className="absolute right-0 mt-2 w-72 bg-agni-card border border-agni-border rounded-xl shadow-2xl p-2 z-50 animate-in fade-in slide-in-from-top-2">
              <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800 flex items-center justify-between">
                <span>Switch Operational Portal</span>
                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">4 Portals</span>
              </div>
              <div className="py-1 space-y-1">
                {PORTAL_OPTIONS.map((portal) => {
                  const isActive = user?.role === portal.role;
                  return (
                    <button
                      key={portal.role}
                      onClick={() => {
                        switchRole(portal.role);
                        setRoleMenuOpen(false);
                        router.push(portal.href);
                      }}
                      className={`w-full text-left p-2.5 rounded-lg transition-all border ${
                        isActive
                          ? "bg-amber-500/15 text-amber-300 font-semibold border-amber-500/40 shadow-sm"
                          : "text-slate-300 hover:bg-slate-800/80 border-transparent"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          <span className="font-bold text-xs">{portal.name}</span>
                          <span className={`text-[8px] font-mono px-1.5 py-0.2 rounded font-bold uppercase border ${portal.badgeColor}`}>
                            {portal.badge}
                          </span>
                        </div>
                        {isActive && <CheckCircle2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />}
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                        {portal.description}
                      </div>
                    </button>
                  );
                })}
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

      {/* Mobile Slide-Over Navigation Menu */}
      {mobileNavOpen && (
        <div className="fixed inset-x-0 top-16 bottom-0 bg-slate-950/98 z-50 p-4 overflow-y-auto border-t border-slate-800 md:hidden space-y-4 animate-in fade-in slide-in-from-top-4">
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">MISSION CLOCK:</span>
              <span className="text-white font-bold">{missionClock.utc}</span>
            </div>
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">INGESTION:</span>
              <span className="text-emerald-400 font-bold">ACTIVE (15-min cycle)</span>
            </div>
          </div>

          <div className="space-y-3">
            <div className="text-[11px] font-mono uppercase text-slate-400 font-bold tracking-wider">COMMAND CENTER</div>
            <div className="grid grid-cols-2 gap-2">
              <Link onClick={() => setMobileNavOpen(false)} href="/dashboard" className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white font-semibold flex items-center gap-2">
                <MapIcon className="w-4 h-4 text-amber-400" />
                <span>Dashboard</span>
              </Link>
              <Link onClick={() => setMobileNavOpen(false)} href="/dashboard/events" className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white font-semibold flex items-center gap-2">
                <Flame className="w-4 h-4 text-red-400" />
                <span>Events</span>
              </Link>
              <Link onClick={() => setMobileNavOpen(false)} href="/dashboard/alerts" className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white font-semibold flex items-center gap-2">
                <Bell className="w-4 h-4 text-amber-400" />
                <span>Alerts</span>
              </Link>
              <Link onClick={() => setMobileNavOpen(false)} href="/dashboard/verification" className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white font-semibold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Verification</span>
              </Link>
            </div>

            <div className="text-[11px] font-mono uppercase text-slate-400 font-bold tracking-wider pt-2">INTELLIGENCE & ASSETS</div>
            <div className="grid grid-cols-2 gap-2">
              <Link onClick={() => setMobileNavOpen(false)} href="/dashboard/atlas" className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white font-semibold flex items-center gap-2">
                <Globe className="w-4 h-4 text-cyan-400" />
                <span>Atlas</span>
              </Link>
              <Link onClick={() => setMobileNavOpen(false)} href="/dashboard/facilities" className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white font-semibold flex items-center gap-2">
                <Factory className="w-4 h-4 text-blue-400" />
                <span>Facilities</span>
              </Link>
              <Link onClick={() => setMobileNavOpen(false)} href="/dashboard/persistent-sources" className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white font-semibold flex items-center gap-2">
                <Flame className="w-4 h-4 text-orange-400" />
                <span>Persistent</span>
              </Link>
              <Link onClick={() => setMobileNavOpen(false)} href="/dashboard/candidates" className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white font-semibold flex items-center gap-2">
                <Search className="w-4 h-4 text-purple-400" />
                <span>Candidates</span>
              </Link>
            </div>

            <div className="text-[11px] font-mono uppercase text-slate-400 font-bold tracking-wider pt-2">ANALYTICS & MISSION</div>
            <div className="grid grid-cols-2 gap-2">
              <Link onClick={() => setMobileNavOpen(false)} href="/dashboard/analytics" className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white font-semibold flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-amber-400" />
                <span>Analytics</span>
              </Link>
              <Link onClick={() => setMobileNavOpen(false)} href="/dashboard/mission-control" className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white font-semibold flex items-center gap-2">
                <Radio className="w-4 h-4 text-purple-400" />
                <span>AGNI-SAT</span>
              </Link>
            </div>

            <div className="text-[11px] font-mono uppercase text-slate-400 font-bold tracking-wider pt-2">OPERATIONAL PORTALS</div>
            <div className="grid grid-cols-2 gap-2">
              <Link onClick={() => { switchRole("ANALYST"); setMobileNavOpen(false); }} href="/dashboard" className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white font-semibold flex items-center gap-2">
                <MapIcon className="w-4 h-4 text-blue-400" />
                <span>Analyst Portal</span>
              </Link>
              <Link onClick={() => { switchRole("AGENCY"); setMobileNavOpen(false); }} href="/portal/agency" className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white font-semibold flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-red-400" />
                <span>Agency Portal</span>
              </Link>
              <Link onClick={() => { switchRole("PUBLIC"); setMobileNavOpen(false); }} href="/portal/public" className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white font-semibold flex items-center gap-2">
                <Eye className="w-4 h-4 text-emerald-400" />
                <span>Public Portal</span>
              </Link>
              <Link onClick={() => { switchRole("ADMIN"); setMobileNavOpen(false); }} href="/admin" className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-white font-semibold flex items-center gap-2">
                <Settings className="w-4 h-4 text-purple-400" />
                <span>Admin Portal</span>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Mobile Floating Command Palette Modal */}
      {mobileSearchOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/95 backdrop-blur-2xl p-4 flex flex-col md:hidden animate-in fade-in">
          <div className="flex items-center gap-2.5 border-b border-slate-800 pb-3">
            <Search className="w-5 h-5 text-amber-400 shrink-0" />
            <input
              ref={mobileSearchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search event ID, facility, coords, district..."
              className="flex-1 bg-transparent text-sm text-white placeholder:text-slate-500 focus:outline-none"
            />
            {searchLoading ? (
              <Loader2 className="w-4 h-4 text-amber-400 animate-spin" />
            ) : (
              <button
                onClick={() => {
                  setMobileSearchOpen(false);
                  setSearchQuery("");
                  setSearchResults([]);
                }}
                className="p-1 rounded-lg text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto py-3 space-y-3">
            {groupedResults.map((group) => (
              <div key={group.key} className="space-y-1.5">
                <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider bg-slate-900/60 p-1 rounded">
                  {group.label}
                </div>
                {group.items.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => handleSelectResult(item)}
                    className="flex items-center gap-3 p-2.5 rounded-xl bg-slate-900/40 border border-slate-800/80 active:bg-slate-800"
                  >
                    <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center shrink-0 border border-slate-800">
                      {getResultIcon(item.type)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="font-semibold text-xs text-white truncate">{item.title}</div>
                      <div className="text-[10px] text-slate-400 truncate">{item.subtitle}</div>
                    </div>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 uppercase shrink-0">
                      {item.type}
                    </span>
                  </div>
                ))}
              </div>
            ))}

            {!searchQuery && (
              <div className="p-2 space-y-2 text-xs text-slate-400">
                <div className="text-[10px] font-mono uppercase text-slate-500">Quick Targets</div>
                <button
                  onClick={() => setSearchQuery("Gujarat")}
                  className="w-full p-2 rounded-xl bg-slate-900 border border-slate-800 text-left text-amber-400 font-mono"
                >
                  Gujarat Petrochemical & Refineries
                </button>
                <button
                  onClick={() => setSearchQuery("Bhilai")}
                  className="w-full p-2 rounded-xl bg-slate-900 border border-slate-800 text-left text-cyan-400 font-mono"
                >
                  Bhilai Steel & Thermal Generation
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
