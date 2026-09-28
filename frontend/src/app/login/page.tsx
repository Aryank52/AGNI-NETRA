"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/authContext";
import AgniNetraLogo from "@/components/common/AgniNetraLogo";
import { 
  ShieldCheck, ArrowRight, Lock,
  Mail, AlertCircle, Eye, EyeOff,
  ChevronDown, Sparkles
} from "lucide-react";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, loginPrototype } = useAuth();
  
  // Prototype mode detection (defaults to true if NEXT_PUBLIC_PROTOTYPE_MODE is true or staging/dev)
  const isPrototypeMode = process.env.NEXT_PUBLIC_PROTOTYPE_MODE !== "false";

  // Demo session states
  const [demoLoading, setDemoLoading] = useState<string | null>(null);
  const [demoError, setDemoError] = useState<string | null>(null);

  // Normal account sign-in toggle and fields
  const [showAccountLogin, setShowAccountLogin] = useState<boolean>(!isPrototypeMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberWorkstation, setRememberWorkstation] = useState(false);
  const [accountLoading, setAccountLoading] = useState(false);
  const [accountError, setAccountError] = useState<string | null>(null);
  const [roleMismatch, setRoleMismatch] = useState<{ role: string; portal: string } | null>(null);

  const getSafeRedirectUrl = () => {
    const rawRedirect = searchParams.get("redirect");
    if (rawRedirect && rawRedirect.startsWith("/") && !rawRedirect.startsWith("//")) {
      return rawRedirect;
    }
    return null;
  };

  // One-click demo session handler
  const handleDemoAccess = async (role: "ANALYST" | "AGENCY" | "PUBLIC") => {
    setDemoLoading(role);
    setDemoError(null);

    try {
      await loginPrototype(role);
      const targetRedirect = getSafeRedirectUrl();
      const defaultDest = role === "ANALYST" ? "/dashboard" : role === "AGENCY" ? "/portal/agency" : "/portal/public";

      // If user came with a valid redirect matching their demo workspace, navigate there
      if (targetRedirect && targetRedirect.startsWith(defaultDest)) {
        router.push(targetRedirect);
      } else {
        router.push(defaultDest);
      }
    } catch (err: any) {
      setDemoError(err.message || "Failed to initialize prototype session.");
      setDemoLoading(null);
    }
  };

  // Normal credentials submission
  const handleAccountSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAccountLoading(true);
    setAccountError(null);
    setRoleMismatch(null);

    try {
      await login(email.trim(), password);

      const storedUser = localStorage.getItem("agni_user");
      if (!storedUser) {
        throw new Error("Authentication succeeded but account profile was not returned.");
      }

      const authenticatedUser = JSON.parse(storedUser) as { role?: string };
      const accountRole = String(authenticatedUser.role || "").toUpperCase();

      const rolePortalMap: Record<string, string> = {
        ADMIN: "/admin",
        ANALYST: "/dashboard",
        AGENCY: "/portal/agency",
        PUBLIC: "/portal/public",
        RESEARCHER: "/portal/research",
        INDUSTRY: "/portal/industry",
      };

      const authorizedPortal = rolePortalMap[accountRole];
      const targetRedirect = getSafeRedirectUrl();

      if (targetRedirect) {
        const parsedPath = (
          targetRedirect.startsWith("http")
            ? new URL(targetRedirect).pathname
            : new URL(targetRedirect, "http://localhost").pathname
        ).replace(/\/+$/, "") || "/";

        const authorized =
          !!authorizedPortal &&
          (parsedPath === authorizedPortal || parsedPath.startsWith(`${authorizedPortal}/`));

        if (!authorized) {
          setAccountError(`Your account is registered for ${accountRole} access.`);
          if (authorizedPortal) {
            setRoleMismatch({
              role: accountRole,
              portal: authorizedPortal,
            });
          }
          return;
        }

        router.push(targetRedirect);
        return;
      }

      if (authorizedPortal) {
        router.push(authorizedPortal);
      } else {
        setAccountError("Portal access denied. No authorized workspace is assigned to this account.");
      }
    } catch (err: any) {
      setAccountError(err.message || "Invalid email or password. Access denied.");
    } finally {
      setAccountLoading(false);
    }
  };

  return (
    <div className="bg-agni-card py-8 px-6 shadow-2xl rounded-2xl sm:px-10 border border-agni-border space-y-6">
      {/* Header & Subtitle */}
      <div className="text-center space-y-1">
        <h1 className="text-2xl font-black text-white tracking-tight font-sans">
          Access AGNI-NETRA
        </h1>
        <p className="text-xs text-slate-400">
          Choose your workspace
        </p>

        {/* Prototype Notice Indicator */}
        {isPrototypeMode && (
          <div className="pt-2 flex justify-center">
            <span className="inline-flex items-center gap-1.5 py-1 px-3 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 font-mono text-[10px] font-bold tracking-widest uppercase">
              <Sparkles className="w-3 h-3 text-amber-400" />
              <span>PROTOTYPE ACCESS MODE</span>
            </span>
          </div>
        )}
      </div>

      {demoError && (
        <div className="p-3.5 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
          <span>{demoError}</span>
        </div>
      )}

      {/* Three Workspace Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* ANALYST */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-700/80 hover:border-cyan-500/60 transition flex flex-col justify-between space-y-3">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-cyan-500/30 bg-cyan-500/10 text-[10px] font-bold text-cyan-400 font-mono">
                AN
              </span>
              <span className="text-[9px] font-mono uppercase text-cyan-400 font-bold">
                Workstation
              </span>
            </div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wide">
              Analyst
            </h2>
            <p className="text-[11px] text-slate-400 leading-snug">
              Operational geospatial intelligence, live satellite passes, and investigation dossiers.
            </p>
          </div>

          {isPrototypeMode ? (
            <button
              type="button"
              disabled={!!demoLoading}
              onClick={() => handleDemoAccess("ANALYST")}
              className="w-full py-2 px-3 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 text-xs font-bold font-mono transition flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              {demoLoading === "ANALYST" ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
                  <span>Launching...</span>
                </>
              ) : (
                <>
                  <span>Enter Analyst Demo</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          ) : (
            <Link
              href="/login?redirect=%2Fdashboard"
              className="w-full py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold text-center transition block"
            >
              Select Analyst
            </Link>
          )}
        </div>

        {/* AGENCY */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-700/80 hover:border-red-500/60 transition flex flex-col justify-between space-y-3">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-red-500/30 bg-red-500/10 text-[10px] font-bold text-red-400 font-mono">
                AG
              </span>
              <span className="text-[9px] font-mono uppercase text-red-400 font-bold">
                Response
              </span>
            </div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wide">
              Agency
            </h2>
            <p className="text-[11px] text-slate-400 leading-snug">
              Emergency response coordination, hazard triage, containment dispatch, and regulatory reports.
            </p>
          </div>

          {isPrototypeMode ? (
            <button
              type="button"
              disabled={!!demoLoading}
              onClick={() => handleDemoAccess("AGENCY")}
              className="w-full py-2 px-3 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-300 border border-red-500/40 text-xs font-bold font-mono transition flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              {demoLoading === "AGENCY" ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
                  <span>Launching...</span>
                </>
              ) : (
                <>
                  <span>Enter Agency Demo</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          ) : (
            <Link
              href="/login?redirect=%2Fportal%2Fagency"
              className="w-full py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold text-center transition block"
            >
              Select Agency
            </Link>
          )}
        </div>

        {/* PUBLIC */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-700/80 hover:border-emerald-500/60 transition flex flex-col justify-between space-y-3">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-[10px] font-bold text-emerald-400 font-mono">
                PU
              </span>
              <span className="text-[9px] font-mono uppercase text-emerald-400 font-bold">
                Advisory
              </span>
            </div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wide">
              Public
            </h2>
            <p className="text-[11px] text-slate-400 leading-snug">
              Public safety advisories, regional hazard maps, air quality context, and protective precautions.
            </p>
          </div>

          {isPrototypeMode ? (
            <button
              type="button"
              disabled={!!demoLoading}
              onClick={() => handleDemoAccess("PUBLIC")}
              className="w-full py-2 px-3 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 text-xs font-bold font-mono transition flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              {demoLoading === "PUBLIC" ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
                  <span>Launching...</span>
                </>
              ) : (
                <>
                  <span>Enter Public Demo</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          ) : (
            <Link
              href="/portal/public"
              className="w-full py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold text-center transition block"
            >
              Open Public
            </Link>
          )}
        </div>
      </div>

      {/* Account Login Toggle Section */}
      <div className="pt-2 border-t border-slate-800/80 space-y-4">
        <div className="text-center">
          <button
            type="button"
            onClick={() => setShowAccountLogin(!showAccountLogin)}
            className="text-xs text-slate-400 hover:text-white transition-colors inline-flex items-center gap-1.5 font-mono py-1 px-2.5 rounded-lg hover:bg-slate-900 cursor-pointer"
          >
            <span>{showAccountLogin ? "Hide account sign-in" : "Sign in with account"}</span>
            <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showAccountLogin ? "rotate-180" : ""}`} />
          </button>
        </div>

        {showAccountLogin && (
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4 animate-in fade-in duration-200">
            {accountError && (
              <div className="p-3 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                  <span>{accountError}</span>
                </div>
                {roleMismatch && (
                  <Link
                    href={roleMismatch.portal}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-amber-400 hover:text-amber-300 underline underline-offset-4 ml-6 transition-colors"
                  >
                    <span>
                      Switch to {roleMismatch.role === "ANALYST" ? "Analyst" : roleMismatch.role === "AGENCY" ? "Agency" : roleMismatch.role === "ADMIN" ? "Admin" : "Public"} Portal
                    </span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                )}
              </div>
            )}

            <form className="space-y-3.5" onSubmit={handleAccountSubmit}>
              <div>
                <label className="block text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-1 font-mono">
                  EMAIL ADDRESS
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    type="email"
                    required
                    disabled={accountLoading}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
                    placeholder="name@gmail.com"
                    autoComplete="username"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-[11px] font-bold text-slate-300 uppercase tracking-wider font-mono">
                    PASSWORD
                  </label>
                  <Link
                    href="/forgot-password"
                    className="text-[10px] text-amber-400 hover:text-amber-300 transition-colors"
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
                    disabled={accountLoading}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-9 pr-10 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
                    placeholder="••••••••••••"
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={accountLoading}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300 transition-colors"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between pt-0.5">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={rememberWorkstation}
                    onChange={(e) => setRememberWorkstation(e.target.checked)}
                    disabled={accountLoading}
                    className="w-3 h-3 rounded bg-slate-900 border-slate-700 text-amber-500 focus:ring-0 focus:ring-offset-0"
                  />
                  <span className="text-[11px] text-slate-400">Remember workstation</span>
                </label>
              </div>

              <button
                type="submit"
                disabled={accountLoading}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-xs tracking-wider shadow-md shadow-amber-500/20 flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
              >
                {accountLoading ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                    <span>Signing In...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In to Workspace</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </form>
          </div>
        )}
      </div>

      {/* Registration Link */}
      <div className="text-center text-xs text-slate-400 border-t border-slate-800 pt-4">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="text-amber-400 hover:underline font-bold">
          Register for Portal Access
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
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-lg">
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
