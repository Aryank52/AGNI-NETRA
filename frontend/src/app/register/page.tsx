"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { 
  Building, User, Mail, Lock, Eye, EyeOff,
  AlertCircle, CheckCircle2, ArrowRight, Sparkles,
  Activity, Shield, Users
} from "lucide-react";
import AgniNetraLogo from "@/components/common/AgniNetraLogo";
import { fetchApi } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  
  const [fullName, setFullName] = useState("");
  const [organization, setOrganization] = useState("");
  const [email, setEmail] = useState("");
  const [requestedRole, setRequestedRole] = useState<"ANALYST" | "AGENCY" | "PUBLIC">("ANALYST");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedEmail = email.trim();
    if (!trimmedEmail.includes("@") || !trimmedEmail.includes(".")) {
      setError("Please enter a valid email address.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters in length.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      await fetchApi("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          full_name: fullName.trim(),
          email: trimmedEmail,
          organization: organization.trim() || undefined,
          password,
          requested_role: requestedRole,
          role: requestedRole,
        }),
      });
      setSuccess(true);
    } catch (err: any) {
      setError(err.message || "Registration failed. Please check your details and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 selection:bg-amber-500 selection:text-slate-950 font-sans">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center flex flex-col items-center">
        <Link href="/" className="inline-block transition-transform hover:scale-105">
          <AgniNetraLogo size={42} subtext="NATIONAL GEOSPATIAL INTELLIGENCE" />
        </Link>
        <div className="mt-3 flex items-center justify-center gap-2">
          <span className="text-xl font-black text-white tracking-wider font-mono">
            AGNI-NETRA
          </span>
          <span className="py-0.5 px-2 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 font-mono text-[10px] font-bold tracking-widest uppercase inline-flex items-center gap-1">
            <Sparkles className="w-2.5 h-2.5" />
            PROTOTYPE
          </span>
        </div>
        <h1 className="mt-2 text-2xl font-black text-white tracking-tight">
          Create Prototype Workspace
        </h1>
        <p className="mt-1 text-xs text-slate-400 max-w-sm">
          Select your workspace role to create a prototype account.
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-lg">
        <div className="bg-slate-900/90 py-8 px-6 shadow-2xl rounded-2xl sm:px-8 border border-slate-800 space-y-6 backdrop-blur-md">
          {success ? (
            <div className="text-center space-y-5 py-4">
              <div className="w-14 h-14 mx-auto rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8 text-emerald-400" />
              </div>
              <div className="space-y-1.5">
                <h2 className="text-xl font-bold text-white">Workspace Initialized</h2>
                <p className="text-sm font-mono text-amber-400 font-bold">
                  Role: {requestedRole}
                </p>
                <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed pt-1">
                  Your prototype account has been created successfully. You can now access your designated workspace.
                </p>
              </div>

              <Link
                href="/login"
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-xs tracking-wider shadow-lg shadow-amber-500/20 inline-flex items-center justify-center gap-2 transition-all cursor-pointer"
              >
                <span>Continue to Sign In</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          ) : (
            <>
              {error && (
                <div className="p-3.5 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center gap-2.5">
                  <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                  <span>{error}</span>
                </div>
              )}

              <form className="space-y-4" onSubmit={handleSubmit}>
                {/* 3-Role Workspace Selector */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
                      WORKSPACE ROLE
                    </label>
                    <span className="text-[10px] text-slate-500 font-mono">Select One</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      type="button"
                      onClick={() => setRequestedRole("ANALYST")}
                      className={`p-2.5 rounded-xl border text-left transition cursor-pointer ${
                        requestedRole === "ANALYST"
                          ? "border-cyan-500 bg-cyan-500/10 ring-1 ring-cyan-500/40 text-white"
                          : "border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold font-mono text-cyan-400 flex items-center gap-1">
                          <Activity className="w-3 h-3" />
                          ANALYST
                        </span>
                        {requestedRole === "ANALYST" && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>}
                      </div>
                      <p className="text-[10px] text-slate-400 mt-1 truncate">Operational Intel</p>
                    </button>

                    <button
                      type="button"
                      onClick={() => setRequestedRole("AGENCY")}
                      className={`p-2.5 rounded-xl border text-left transition cursor-pointer ${
                        requestedRole === "AGENCY"
                          ? "border-rose-500 bg-rose-500/10 ring-1 ring-rose-500/40 text-white"
                          : "border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold font-mono text-rose-400 flex items-center gap-1">
                          <Shield className="w-3 h-3" />
                          AGENCY
                        </span>
                        {requestedRole === "AGENCY" && <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>}
                      </div>
                      <p className="text-[10px] text-slate-400 mt-1 truncate">Response Ops</p>
                    </button>

                    <button
                      type="button"
                      onClick={() => setRequestedRole("PUBLIC")}
                      className={`p-2.5 rounded-xl border text-left transition cursor-pointer ${
                        requestedRole === "PUBLIC"
                          ? "border-emerald-500 bg-emerald-500/10 ring-1 ring-emerald-500/40 text-white"
                          : "border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold font-mono text-emerald-400 flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          PUBLIC
                        </span>
                        {requestedRole === "PUBLIC" && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>}
                      </div>
                      <p className="text-[10px] text-slate-400 mt-1 truncate">Public Safety</p>
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5 font-mono">
                      Full Name
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                        <User className="w-4 h-4" />
                      </div>
                      <input
                        type="text"
                        required
                        disabled={loading}
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white text-xs placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
                        placeholder="Aryan Sharma"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5 font-mono">
                      Organization (Optional)
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                        <Building className="w-4 h-4" />
                      </div>
                      <input
                        type="text"
                        disabled={loading}
                        value={organization}
                        onChange={(e) => setOrganization(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white text-xs placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
                        placeholder="Optional"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5 font-mono">
                    Email Address
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
                      className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
                      placeholder="name@example.com"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5 font-mono">
                      Password
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                        <Lock className="w-4 h-4" />
                      </div>
                      <input
                        type={showPassword ? "text" : "password"}
                        required
                        disabled={loading}
                        minLength={8}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full pl-9 pr-10 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
                        placeholder="Min 8 characters"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        disabled={loading}
                        className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300 transition-colors"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5 font-mono">
                      Confirm Password
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                        <Lock className="w-4 h-4" />
                      </div>
                      <input
                        type={showPassword ? "text" : "password"}
                        required
                        disabled={loading}
                        minLength={8}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-white text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
                        placeholder="Confirm password"
                      />
                    </div>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-xs tracking-wider shadow-lg shadow-amber-500/20 flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed font-mono"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                      <span>Creating Workspace...</span>
                    </>
                  ) : (
                    <>
                      <span>Create Prototype Workspace →</span>
                    </>
                  )}
                </button>
              </form>

              <div className="text-center text-xs text-slate-400 border-t border-slate-800 pt-4">
                Already have access?{" "}
                <Link href="/login" className="text-amber-400 hover:underline font-bold">
                  Sign In to Prototype
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
