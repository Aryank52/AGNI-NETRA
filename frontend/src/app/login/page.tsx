"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/authContext";
import AgniNetraLogo from "@/components/common/AgniNetraLogo";
import { 
  Activity, ShieldAlert, Globe, ArrowRight,
  AlertCircle, Lock, Mail, Eye, EyeOff, Sparkles
} from "lucide-react";

type PrototypeRole = "ANALYST" | "AGENCY" | "PUBLIC";

interface PersonaCard {
  role: PrototypeRole;
  title: string;
  descriptor: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  colorClasses: string;
  badgeClasses: string;
  iconClasses: string;
}

const PERSONA_CARDS: PersonaCard[] = [
  {
    role: "ANALYST",
    title: "ANALYST",
    descriptor: "Operational Intelligence",
    description: "Analyze thermal events, geospatial signals, candidate detections, investigations and intelligence.",
    icon: Activity,
    colorClasses: "border-cyan-500/40 bg-cyan-950/20 hover:border-cyan-400/80 hover:bg-cyan-500/10 text-cyan-300",
    badgeClasses: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40",
    iconClasses: "text-cyan-400",
  },
  {
    role: "AGENCY",
    title: "AGENCY",
    descriptor: "Response Intelligence",
    description: "Situational awareness, emergency response, incident coordination and operational monitoring.",
    icon: ShieldAlert,
    colorClasses: "border-red-500/40 bg-red-950/20 hover:border-red-400/80 hover:bg-red-500/10 text-red-300",
    badgeClasses: "bg-red-500/20 text-red-300 border-red-500/40",
    iconClasses: "text-red-400",
  },
  {
    role: "PUBLIC",
    title: "PUBLIC",
    descriptor: "Public Safety",
    description: "Public advisories, hazard context, regional thermal information and safety guidance.",
    icon: Globe,
    colorClasses: "border-emerald-500/40 bg-emerald-950/20 hover:border-emerald-400/80 hover:bg-emerald-500/10 text-emerald-300",
    badgeClasses: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
    iconClasses: "text-emerald-400",
  },
];

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, loginPrototype } = useAuth();

  const isPrototypeMode = process.env.NEXT_PUBLIC_PROTOTYPE_MODE !== "false";

  // Normal login state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 1-Click Prototype session state
  const [protoLoadingRole, setProtoLoadingRole] = useState<PrototypeRole | null>(null);

  const getSafeRedirectUrl = (role: string) => {
    const rawRedirect = searchParams.get("redirect");
    if (rawRedirect && rawRedirect.startsWith("/") && !rawRedirect.startsWith("//")) {
      const rolePrefixMap: Record<string, string> = {
        ADMIN: "/admin",
        ANALYST: "/dashboard",
        AGENCY: "/portal/agency",
        PUBLIC: "/portal/public",
      };
      const expectedPrefix = rolePrefixMap[role];
      if (expectedPrefix && rawRedirect.startsWith(expectedPrefix)) {
        return rawRedirect;
      }
    }
    return null;
  };

  const handleNormalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

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

      const redirectDest = getSafeRedirectUrl(userRole);
      const defaultDest = rolePortalMap[userRole] || "/portal/public";
      router.push(redirectDest || defaultDest);
    } catch (err: any) {
      setError(err.message || "Invalid authorized email or passcode.");
    } finally {
      setLoading(false);
    }
  };

  const handlePrototypeClick = async (role: PrototypeRole) => {
    if (!isPrototypeMode) {
      setError("Prototype access is currently unavailable in this environment.");
      return;
    }

    setProtoLoadingRole(role);
    setError(null);

    try {
      await loginPrototype(role);

      const redirectDest = getSafeRedirectUrl(role);
      const defaultDest =
        role === "ANALYST"
          ? "/dashboard"
          : role === "AGENCY"
          ? "/portal/agency"
          : "/portal/public";

      router.push(redirectDest || defaultDest);
    } catch (err: any) {
      setError(err.message || "Failed to initialize prototype session.");
      setProtoLoadingRole(null);
    }
  };

  return (
    <div className="bg-slate-900/90 py-7 px-6 shadow-2xl rounded-2xl sm:px-8 border border-slate-800 space-y-5 max-w-xl mx-auto backdrop-blur-md">
      {error && (
        <div className="p-3 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Normal Credentials Form */}
      <form className="space-y-4" onSubmit={handleNormalSubmit}>
        <div>
          <label className="block text-[11px] font-mono font-bold text-slate-300 uppercase tracking-wider mb-1.5">
            AUTHORIZED EMAIL ADDRESS
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <Mail className="w-4 h-4" />
            </div>
            <input
              type="email"
              required
              disabled={loading || !!protoLoadingRole}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-white text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
              placeholder="name@gmail.com"
              autoComplete="username"
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="block text-[11px] font-mono font-bold text-slate-300 uppercase tracking-wider">
              SECURITY PASSCODE
            </label>
            <Link
              href="/forgot-password"
              className="text-[11px] text-amber-400 hover:text-amber-300 font-semibold transition-colors"
            >
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <Lock className="w-4 h-4" />
            </div>
            <input
              type={showPassword ? "text" : "password"}
              required
              disabled={loading || !!protoLoadingRole}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-9 pr-10 py-2.5 rounded-xl bg-slate-950 border border-slate-700 text-white text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
              placeholder="••••••••••••••"
              autoComplete="current-password"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              disabled={loading || !!protoLoadingRole}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300 transition-colors"
              aria-label={showPassword ? "Hide passcode" : "Show passcode"}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !!protoLoadingRole}
          className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-xs tracking-wider shadow-lg shadow-amber-500/20 flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50 font-mono"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
              <span>Authenticating Session...</span>
            </>
          ) : (
            <>
              <span>Access Command Center →</span>
            </>
          )}
        </button>
      </form>

      {/* Registration Link */}
      <div className="text-center text-xs text-slate-400 border-t border-slate-800/80 pt-3">
        Need an authorized account?{" "}
        <Link href="/register" className="text-amber-400 hover:underline font-bold">
          Register New Organization
        </Link>
      </div>

      {/* 1-Click Prototype Persona Section */}
      <div className="pt-2 space-y-3">
        <div className="relative flex items-center justify-center">
          <div className="border-t border-slate-800 w-full" />
          <span className="bg-slate-900 px-3 text-[10px] uppercase font-mono font-bold text-slate-400 absolute flex items-center gap-1.5">
            <Sparkles className="w-2.5 h-2.5 text-amber-400" />
            <span>OR SELECT 1-CLICK PROTOTYPE PERSONA</span>
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
          {PERSONA_CARDS.map((p) => {
            const Icon = p.icon;
            const isCardLoading = protoLoadingRole === p.role;

            return (
              <button
                key={p.role}
                type="button"
                onClick={() => handlePrototypeClick(p.role)}
                disabled={loading || !!protoLoadingRole}
                className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between space-y-2 ${p.colorClasses} disabled:opacity-50`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Icon className={`w-3.5 h-3.5 ${p.iconClasses}`} />
                    <span className="text-xs font-bold font-mono tracking-wide">
                      {p.title}
                    </span>
                  </div>
                  <span
                    className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ${p.badgeClasses}`}
                  >
                    {isCardLoading ? "..." : "1-CLICK"}
                  </span>
                </div>

                <div>
                  <p className="text-[11px] font-semibold text-slate-200 leading-tight">
                    {p.descriptor}
                  </p>
                  <p className="text-[10px] text-slate-400 leading-snug mt-1 line-clamp-3">
                    {p.description}
                  </p>
                </div>

                <div className="pt-1 flex items-center justify-end text-[10px] font-mono font-bold">
                  {isCardLoading ? (
                    <span className="inline-flex items-center gap-1 text-amber-400">
                      <span className="w-2.5 h-2.5 border border-amber-400 border-t-transparent rounded-full animate-spin" />
                      Opening...
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 opacity-80 group-hover:opacity-100">
                      Enter →
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-agni-navy flex flex-col justify-center py-10 px-4 sm:px-6 lg:px-8 selection:bg-amber-500 selection:text-slate-950 font-sans">
      {/* Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center flex flex-col items-center">
        <Link href="/" className="inline-block transition-transform hover:scale-105">
          <AgniNetraLogo size={44} subtext="NATIONAL GEOSPATIAL INTELLIGENCE" />
        </Link>
        <h1 className="mt-3 text-xl sm:text-2xl font-black text-white tracking-tight">
          Sign In to Decision Support Command Portal
        </h1>
        <p className="mt-1 text-xs text-slate-400 max-w-sm">
          Satellite-Derived Thermal Observation & Industrial Intelligence Platform
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-xl">
        <Suspense
          fallback={
            <div className="p-8 text-center text-slate-500 font-mono text-xs">
              Loading command portal...
            </div>
          }
        >
          <LoginForm />
        </Suspense>
      </div>
    </div>
  );
}
