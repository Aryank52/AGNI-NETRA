"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/authContext";
import AgniNetraLogo from "@/components/common/AgniNetraLogo";
import { 
  ShieldCheck, ArrowRight, Lock,
  Mail, AlertCircle, Eye, EyeOff, ShieldAlert
} from "lucide-react";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberWorkstation, setRememberWorkstation] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getSafeRedirectUrl = () => {
    const rawRedirect = searchParams.get("redirect");
    if (rawRedirect && rawRedirect.startsWith("/") && !rawRedirect.startsWith("//")) {
      return rawRedirect;
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await login(email.trim(), password);

      const targetRedirect = getSafeRedirectUrl();
      if (targetRedirect) {
        router.push(targetRedirect);
        return;
      }

      // Check stored user role to route appropriately
      try {
        const storedUser = localStorage.getItem("agni_user");
        if (storedUser) {
          const user = JSON.parse(storedUser);
          if (user.role === "AGENCY") {
            router.push("/portal/agency");
            return;
          } else if (user.role === "ADMIN") {
            router.push("/admin");
            return;
          } else if (user.role === "INDUSTRY") {
            router.push("/portal/industry");
            return;
          } else if (user.role === "RESEARCHER") {
            router.push("/portal/research");
            return;
          } else if (user.role === "PUBLIC") {
            router.push("/portal/public");
            return;
          }
        }
      } catch {}

      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Invalid email or passcode. Operational access denied.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-agni-card py-8 px-6 shadow-2xl rounded-2xl sm:px-10 border border-agni-border space-y-6">
      {/* Statutory Security Invariant Notice */}
      <div className="p-3.5 rounded-xl bg-slate-900/90 border border-amber-500/30 text-slate-300 text-xs space-y-1">
        <div className="flex items-center gap-1.5 text-amber-400 font-mono font-bold text-[11px] uppercase tracking-wider">
          <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
          <span>OFFICIAL SYSTEM — UNAUTHORIZED ACCESS PROHIBITED</span>
        </div>
        <p className="text-[10px] text-slate-400 leading-relaxed font-sans">
          This platform is restricted to authorized national and state entities. All sessions, spatial queries, and intelligence actions are monitored and cryptographically logged.
        </p>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Form */}
{/* AGNI_PORTAL_SELECTOR_V1 */}
<div className="mb-6">
  <div className="mb-3 flex items-center justify-between">
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">
        Select authorized workspace
      </p>
      <p className="mt-1 text-[11px] text-slate-500">
        Portal selection does not grant access. Your assigned RBAC role is verified after sign-in.
      </p>
    </div>
    <span className="hidden text-[9px] font-mono uppercase tracking-widest text-amber-500 sm:block">
      RBAC GATED
    </span>
  </div>

  <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
    <Link
      href="/login?redirect=%2Fadmin"
      className="group rounded-lg border border-slate-700/80 bg-slate-950/30 px-3 py-3 transition hover:border-amber-500/60 hover:bg-amber-500/5"
    >
      <div className="flex items-center gap-2">
        <span className="flex h-7 w-7 items-center justify-center rounded-md border border-amber-500/30 bg-amber-500/10 text-[10px] font-bold text-amber-400">
          AD
        </span>
        <div className="min-w-0">
          <p className="truncate text-[11px] font-semibold uppercase tracking-wide text-slate-200 group-hover:text-amber-300">
            Admin
          </p>
          <p className="text-[9px] text-slate-500">Administration</p>
        </div>
      </div>
    </Link>

    <Link
      href="/login?redirect=%2Fdashboard"
      className="group rounded-lg border border-slate-700/80 bg-slate-950/30 px-3 py-3 transition hover:border-cyan-500/60 hover:bg-cyan-500/5"
    >
      <div className="flex items-center gap-2">
        <span className="flex h-7 w-7 items-center justify-center rounded-md border border-cyan-500/30 bg-cyan-500/10 text-[10px] font-bold text-cyan-400">
          AN
        </span>
        <div className="min-w-0">
          <p className="truncate text-[11px] font-semibold uppercase tracking-wide text-slate-200 group-hover:text-cyan-300">
            Analyst
          </p>
          <p className="text-[9px] text-slate-500">Intelligence</p>
        </div>
      </div>
    </Link>

    <Link
      href="/login?redirect=%2Fportal%2Fagency"
      className="group rounded-lg border border-slate-700/80 bg-slate-950/30 px-3 py-3 transition hover:border-red-500/60 hover:bg-red-500/5"
    >
      <div className="flex items-center gap-2">
        <span className="flex h-7 w-7 items-center justify-center rounded-md border border-red-500/30 bg-red-500/10 text-[10px] font-bold text-red-400">
          AG
        </span>
        <div className="min-w-0">
          <p className="truncate text-[11px] font-semibold uppercase tracking-wide text-slate-200 group-hover:text-red-300">
            Agency
          </p>
          <p className="text-[9px] text-slate-500">Response</p>
        </div>
      </div>
    </Link>

    <Link
      href="/login?redirect=%2Fportal%2Fpublic"
      className="group rounded-lg border border-emerald-500/40 bg-emerald-500/5 px-3 py-3 transition hover:border-emerald-400/70 hover:bg-emerald-500/10"
    >
      <div className="flex items-center gap-2">
        <span className="flex h-7 w-7 items-center justify-center rounded-md border border-emerald-500/30 bg-emerald-500/10 text-[10px] font-bold text-emerald-400">
          PU
        </span>
        <div className="min-w-0">
          <p className="truncate text-[11px] font-semibold uppercase tracking-wide text-slate-200 group-hover:text-emerald-300">
            Public
          </p>
          <p className="text-[9px] text-slate-500">Safety</p>
        </div>
      </div>
    </Link>
  </div>
</div>
      <form className="space-y-4" onSubmit={handleSubmit}>
        <div>
          <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5 font-mono">
            Official / Work Email
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <Mail className="w-4 h-4" />
            </div>
            <input
              type="email"
              required
              disabled={loading}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
              placeholder="officer@domain.gov.in"
              autoComplete="username"
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
              Security Passcode
            </label>
            <Link
              href="/forgot-password"
              className="text-[11px] text-amber-400 hover:text-amber-300 font-semibold transition-colors"
            >
              Forgot passcode?
            </Link>
          </div>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <Lock className="w-4 h-4" />
            </div>
            <input
              type={showPassword ? "text" : "password"}
              required
              disabled={loading}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-9 pr-10 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
              placeholder="••••••••••••"
              autoComplete="current-password"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              disabled={loading}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300 transition-colors"
              aria-label={showPassword ? "Hide passcode" : "Show passcode"}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between pt-1">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={rememberWorkstation}
              onChange={(e) => setRememberWorkstation(e.target.checked)}
              disabled={loading}
              className="w-3.5 h-3.5 rounded bg-slate-900 border-slate-700 text-amber-500 focus:ring-0 focus:ring-offset-0"
            />
            <span className="text-[11px] text-slate-400">Remember this workstation</span>
          </label>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-xs tracking-wider shadow-lg shadow-amber-500/20 flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
              <span>Authenticating Session...</span>
            </>
          ) : (
            <>
              <span>Sign In to Operational Portal</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      {/* Access Request Links */}
      <div className="text-center text-xs text-slate-400 border-t border-slate-800 pt-4">
        Need operational authorization?{" "}
        <Link href="/register" className="text-amber-400 hover:underline font-bold">
          Request Operational Access
        </Link>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-agni-navy flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 selection:bg-amber-500 selection:text-slate-950">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center flex flex-col items-center">
        <Link href="/" className="inline-block transition-transform hover:scale-105">
          <AgniNetraLogo size={46} subtext="NATIONAL GEOSPATIAL INTELLIGENCE" />
        </Link>
        <h2 className="mt-4 text-2xl font-black text-white tracking-tight font-sans">
          Secure Intelligence Portal
        </h2>
        <p className="mt-1 text-xs text-slate-400 max-w-sm">
          Authorized users only. Sign in to access operational intelligence, satellite telemetry, and investigation dossiers.
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <Suspense fallback={
          <div className="p-8 text-center text-slate-500 font-mono text-xs">
            Loading authentication portal...
          </div>
        }>
          <LoginForm />
        </Suspense>
      </div>
    </div>
  );
}
