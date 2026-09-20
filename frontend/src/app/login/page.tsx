"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { UserRole } from "@/types";
import { useAuth } from "@/lib/authContext";
import { fetchApi } from "@/lib/api";
import AgniNetraLogo from "@/components/common/AgniNetraLogo";
import { 
  Flame, ShieldCheck, ArrowRight, Lock, 
  Mail, Users, CheckCircle2, AlertCircle, KeyRound
} from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login, user, switchRole } = useAuth();
  
  const [email, setEmail] = useState("analyst@agninetra.gov.in");
  const [password, setPassword] = useState("AgniNetra@2026");
  const [selectedRole, setSelectedRole] = useState<UserRole>("ANALYST");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const DEMO_ROLES = [
    {
      role: "ANALYST",
      title: "Geospatial Analyst",
      email: "analyst@agninetra.gov.in",
      desc: "Full verification queue, candidate review, dossiers",
      color: "border-blue-500/40 text-blue-400 bg-blue-950/20",
    },
    {
      role: "AGENCY",
      title: "Emergency Response Agency",
      email: "agency@ndma.gov.in",
      desc: "Priority incidents, dispatch alerts, multi-state overview",
      color: "border-red-500/40 text-red-400 bg-red-950/20",
    },
    {
      role: "ADMIN",
      title: "System Administrator",
      email: "admin@agninetra.gov.in",
      desc: "Ingestion management, model metadata, audit logs",
      color: "border-purple-500/40 text-purple-400 bg-purple-950/20",
    },
    {
      role: "PUBLIC",
      title: "Public Viewer",
      email: "public@user.in",
      desc: "High-level fire safety advisory, no sensitive coordinates",
      color: "border-slate-500/40 text-slate-300 bg-slate-900/40",
    },
  ];

  const handleRoleSelect = (rEmail: string, rName: UserRole) => {
    setEmail(rEmail);
    setPassword("AgniNetra@2026");
    setSelectedRole(rName);
    switchRole(rName);
  };

  const [showPassword, setShowPassword] = useState(false);

  const handleGoogleSignIn = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchApi<any>("/auth/google", {
        method: "POST",
        body: JSON.stringify({
          email: email.includes("@") ? email : "analyst.sarabhai@gmail.com",
          name: "Dr. Vikram Sarabhai",
        })
      });
      if (res && res.access_token) {
        localStorage.setItem("agni_token", res.access_token);
        localStorage.setItem("agni_user", JSON.stringify(res.user));
        if (res.user.role === "AGENCY") router.push("/portal/agency");
        else if (res.user.role === "PUBLIC") router.push("/portal/public");
        else if (res.user.role === "ADMIN") router.push("/admin");
        else router.push("/dashboard");
      }
    } catch (err: any) {
      setError(err.message || "Google Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, selectedRole);
      if (selectedRole === "AGENCY") {
        router.push("/portal/agency");
      } else if (selectedRole === "PUBLIC") {
        router.push("/portal/public");
      } else if (selectedRole === "ADMIN") {
        router.push("/admin");
      } else {
        router.push("/dashboard");
      }
    } catch (err: any) {
      setError(err.message || "Failed to authenticate");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 selection:bg-amber-500 selection:text-slate-950">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center flex flex-col items-center">
        <Link href="/" className="inline-block">
          <AgniNetraLogo size={46} subtext="NATIONAL GEOSPATIAL INTELLIGENCE" />
        </Link>
        <h2 className="mt-4 text-xl font-extrabold text-white tracking-tight">
          Sign In to Decision Support Command Portal
        </h2>
        <p className="mt-1 text-xs text-slate-400">
          Satellite-Derived Thermal Observation & Industrial Intelligence Platform
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-xl">
        <div className="bg-agni-card py-8 px-6 shadow-2xl rounded-2xl sm:px-10 border border-agni-border space-y-6">
          {error && (
            <div className="p-3.5 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{error}</span>
            </div>
          )}

          {/* Google OAuth Button */}
          <button
            type="button"
            onClick={handleGoogleSignIn}
            disabled={loading}
            className="w-full py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-semibold text-xs flex items-center justify-center gap-3 transition-colors shadow-sm cursor-pointer"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            <span>Continue with Google</span>
          </button>

          <div className="relative flex items-center justify-center">
            <div className="border-t border-slate-800 w-full" />
            <span className="bg-agni-card px-3 text-[10px] uppercase font-mono text-slate-500 absolute">
              Or sign in with email
            </span>
          </div>

          {/* Form */}
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Official / Registered Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500"
                  placeholder="name@organization.com or .gov.in"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Security Passcode
                </label>
                <Link
                  href="/forgot-password"
                  className="text-[11px] text-amber-400 hover:text-amber-300 font-semibold"
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
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-10 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500"
                  placeholder="••••••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300"
                >
                  <KeyRound className="w-4 h-4" />
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-xs tracking-wider shadow-lg shadow-amber-500/20 flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <span>{loading ? "Authenticating Session..." : "Access Command Center"}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Links to Register */}
          <div className="text-center text-xs text-slate-400 border-t border-slate-800 pt-4">
            Need an authorized account?{" "}
            <Link href="/register" className="text-amber-400 hover:underline font-bold">
              Register New Organization
            </Link>
          </div>

          {/* 1-Click Role Switcher */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Or Select 1-Click Evaluator Persona:
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {DEMO_ROLES.map((r) => (
                <button
                  key={r.role}
                  type="button"
                  onClick={() => handleRoleSelect(r.email, r.role as UserRole)}
                  className={`p-2.5 rounded-xl border text-left transition-all ${r.color} hover:brightness-125`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold">{r.title}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-900/80 border border-slate-700">
                      {r.role}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1 line-clamp-1">
                    {r.desc}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
