"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/authContext";
import AgniNetraLogo from "@/components/common/AgniNetraLogo";
import { 
  Activity, Shield, Users, ArrowRight,
  AlertCircle, ChevronDown, Lock, Mail, Eye, EyeOff, Sparkles
} from "lucide-react";

type WorkspaceRole = "ANALYST" | "AGENCY" | "PUBLIC";

interface WorkspaceOption {
  role: WorkspaceRole;
  title: string;
  descriptor: string;
  icon: React.ComponentType<{ className?: string }>;
  accentColor: string;
  borderSelected: string;
  bgSelected: string;
  ringSelected: string;
  badgeClass: string;
}

const WORKSPACES: WorkspaceOption[] = [
  {
    role: "ANALYST",
    title: "ANALYST",
    descriptor: "Operational Intelligence",
    icon: Activity,
    accentColor: "text-cyan-400",
    borderSelected: "border-cyan-500",
    bgSelected: "bg-cyan-500/10",
    ringSelected: "ring-1 ring-cyan-500/50",
    badgeClass: "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
  },
  {
    role: "AGENCY",
    title: "AGENCY",
    descriptor: "Response Intelligence",
    icon: Shield,
    accentColor: "text-rose-400",
    borderSelected: "border-rose-500",
    bgSelected: "bg-rose-500/10",
    ringSelected: "ring-1 ring-rose-500/50",
    badgeClass: "bg-rose-500/20 text-rose-300 border-rose-500/30",
  },
  {
    role: "PUBLIC",
    title: "PUBLIC",
    descriptor: "Public Safety",
    icon: Users,
    accentColor: "text-emerald-400",
    borderSelected: "border-emerald-500",
    bgSelected: "bg-emerald-500/10",
    ringSelected: "ring-1 ring-emerald-500/50",
    badgeClass: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  },
];

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, loginPrototype } = useAuth();

  const [selectedWorkspace, setSelectedWorkspace] = useState<WorkspaceRole>("ANALYST");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Secondary legacy account login (kept completely secondary)
  const [showAccountLogin, setShowAccountLogin] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [accountLoading, setAccountLoading] = useState(false);
  const [accountError, setAccountError] = useState<string | null>(null);

  const getSafeRedirectUrl = () => {
    const rawRedirect = searchParams.get("redirect");
    if (rawRedirect && rawRedirect.startsWith("/") && !rawRedirect.startsWith("//")) {
      return rawRedirect;
    }
    return null;
  };

  const handleSignIn = async () => {
    setLoading(true);
    setError(null);

    try {
      await loginPrototype(selectedWorkspace);

      const targetRedirect = getSafeRedirectUrl();
      const defaultDest =
        selectedWorkspace === "ANALYST"
          ? "/dashboard"
          : selectedWorkspace === "AGENCY"
          ? "/portal/agency"
          : "/portal/public";

      if (targetRedirect && targetRedirect.startsWith(defaultDest)) {
        router.push(targetRedirect);
      } else {
        router.push(defaultDest);
      }
    } catch (err: any) {
      setError(err.message || "Failed to initialize prototype session.");
      setLoading(false);
    }
  };

  const handleAccountSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAccountLoading(true);
    setAccountError(null);

    try {
      await login(email.trim(), password);

      const storedUser = localStorage.getItem("agni_user");
      const userObj = storedUser ? JSON.parse(storedUser) : null;
      const userRole = String(userObj?.role || "").toUpperCase();

      const rolePortalMap: Record<string, string> = {
        ADMIN: "/admin",
        ANALYST: "/dashboard",
        AGENCY: "/portal/agency",
        PUBLIC: "/portal/public",
      };

      const dest = rolePortalMap[userRole] || "/portal/public";
      router.push(dest);
    } catch (err: any) {
      setAccountError(err.message || "Invalid email or password.");
      setAccountLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/90 py-8 px-6 shadow-2xl rounded-2xl sm:px-8 border border-slate-800 space-y-6 max-w-lg mx-auto backdrop-blur-md">
      {/* Brand & Prototype Badge */}
      <div className="text-center space-y-2">
        <div className="flex items-center justify-center gap-2">
          <span className="text-base font-black text-white tracking-widest font-mono">
            AGNI-NETRA
          </span>
          <span className="py-0.5 px-2 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 font-mono text-[10px] font-bold tracking-widest uppercase inline-flex items-center gap-1">
            <Sparkles className="w-2.5 h-2.5" />
            PROTOTYPE
          </span>
        </div>

        <h1 className="text-2xl font-black text-white tracking-tight font-sans">
          Access AGNI-NETRA
        </h1>
        <p className="text-xs text-slate-400 font-medium">
          Choose your workspace
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Three Compact Workspace Selection Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {WORKSPACES.map((ws) => {
          const Icon = ws.icon;
          const isSelected = selectedWorkspace === ws.role;

          return (
            <button
              key={ws.role}
              type="button"
              onClick={() => setSelectedWorkspace(ws.role)}
              disabled={loading}
              className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between space-y-2.5 ${
                isSelected
                  ? `${ws.borderSelected} ${ws.bgSelected} ${ws.ringSelected} shadow-md`
                  : "bg-slate-950/60 border-slate-800 hover:border-slate-700 opacity-75 hover:opacity-100"
              }`}
            >
              <div className="flex items-center justify-between">
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center border ${
                    isSelected ? ws.badgeClass : "bg-slate-900 border-slate-800 text-slate-400"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                </div>
                {isSelected && (
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                )}
              </div>

              <div>
                <h3
                  className={`text-xs font-bold font-mono tracking-wide ${
                    isSelected ? "text-white" : "text-slate-300"
                  }`}
                >
                  {ws.title}
                </h3>
                <p className="text-[10px] text-slate-400 leading-snug mt-0.5">
                  {ws.descriptor}
                </p>
              </div>
            </button>
          );
        })}
      </div>

      {/* Single Sign-In Button */}
      <div className="pt-1">
        <button
          type="button"
          onClick={handleSignIn}
          disabled={loading}
          className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-xs tracking-wider font-mono shadow-lg shadow-amber-500/20 flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
        >
          {loading ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
              <span>Launching Workspace...</span>
            </>
          ) : (
            <>
              <span>Sign In →</span>
            </>
          )}
        </button>
      </div>

      {/* Visually Secondary: Optional Account Login for production/existing credentials */}
      <div className="pt-2 border-t border-slate-800/80">
        <div className="text-center">
          <button
            type="button"
            onClick={() => setShowAccountLogin(!showAccountLogin)}
            className="text-[11px] text-slate-500 hover:text-slate-400 transition-colors inline-flex items-center gap-1 font-mono py-1 px-2 rounded hover:bg-slate-900/60 cursor-pointer"
          >
            <span>{showAccountLogin ? "Hide account sign in" : "Existing account sign in"}</span>
            <ChevronDown
              className={`w-3 h-3 transition-transform ${showAccountLogin ? "rotate-180" : ""}`}
            />
          </button>
        </div>

        {showAccountLogin && (
          <div className="mt-3 p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3 animate-in fade-in duration-150">
            {accountError && (
              <div className="p-2.5 rounded-lg bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-3.5 h-3.5 shrink-0 text-red-400" />
                <span>{accountError}</span>
              </div>
            )}

            <form onSubmit={handleAccountSubmit} className="space-y-3">
              <div>
                <label className="block text-[10px] font-mono font-bold text-slate-400 uppercase mb-1">
                  Email
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-slate-500">
                    <Mail className="w-3.5 h-3.5" />
                  </div>
                  <input
                    type="email"
                    required
                    disabled={accountLoading}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="analyst@agency.gov"
                    className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-mono font-bold text-slate-400 uppercase mb-1">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-slate-500">
                    <Lock className="w-3.5 h-3.5" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    disabled={accountLoading}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-8 pr-8 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-2.5 flex items-center text-slate-500 hover:text-slate-300"
                  >
                    {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={accountLoading}
                className="w-full py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-mono font-bold transition flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                {accountLoading ? "Authenticating..." : "Account Sign In"}
              </button>
            </form>
          </div>
        )}
      </div>

      {/* Simple Prototype Workspace Creation Link */}
      <div className="text-center text-[11px] text-slate-400 border-t border-slate-800/80 pt-3">
        Need a dedicated account?{" "}
        <Link href="/register" className="text-amber-400 hover:underline font-bold">
          Create Prototype Workspace
        </Link>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-agni-navy flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 selection:bg-amber-500 selection:text-slate-950 font-sans">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center flex flex-col items-center">
        <Link href="/" className="inline-block transition-transform hover:scale-105">
          <AgniNetraLogo size={42} subtext="NATIONAL GEOSPATIAL INTELLIGENCE" />
        </Link>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-lg">
        <Suspense
          fallback={
            <div className="p-8 text-center text-slate-500 font-mono text-xs">
              Loading workspace gateway...
            </div>
          }
        >
          <LoginForm />
        </Suspense>
      </div>
    </div>
  );
}
