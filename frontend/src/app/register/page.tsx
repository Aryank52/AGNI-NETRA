"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { 
  Building, User, Mail, Lock, Eye, EyeOff,
  AlertCircle, CheckCircle2, ShieldCheck, ArrowRight, Info
} from "lucide-react";
import AgniNetraLogo from "@/components/common/AgniNetraLogo";
import { fetchApi } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  
  const [fullName, setFullName] = useState("");
  const [organization, setOrganization] = useState("");
  const [email, setEmail] = useState("");
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
      setError("Please enter a valid official email address.");
      return;
    }

    if (password.length < 8) {
      setError("Security passcode must be at least 8 characters in length.");
      return;
    }

    const hasLetter = /[a-zA-Z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    if (!hasLetter || !hasNumber) {
      setError("Passcode must contain at least one letter and one number.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Security passcodes do not match.");
      return;
    }

    setLoading(true);

    try {
      await fetchApi("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          full_name: fullName.trim(),
          email: trimmedEmail,
          organization: organization.trim(),
          password,
        }),
      });
      setSuccess(true);
    } catch (err: any) {
      setError(err.message || "Registration request failed. Please check your details and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 selection:bg-amber-500 selection:text-slate-950">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center flex flex-col items-center">
        <Link href="/" className="inline-block transition-transform hover:scale-105">
          <AgniNetraLogo size={46} subtext="NATIONAL GEOSPATIAL INTELLIGENCE" />
        </Link>
        <h2 className="mt-4 text-2xl font-black text-white tracking-tight font-sans">
          Request Operational Access
        </h2>
        <p className="mt-1 text-xs text-slate-400 max-w-sm">
          Operational roles require organizational verification before elevated platform activation.
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-lg">
        <div className="bg-agni-card py-8 px-6 shadow-2xl rounded-2xl sm:px-10 border border-agni-border space-y-6">
          {success ? (
            <div className="text-center space-y-5 py-4">
              <div className="w-14 h-14 mx-auto rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8 text-emerald-400" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-bold text-white">Registration Submitted Successfully</h3>
                <p className="text-xs text-slate-300 max-w-md mx-auto leading-relaxed">
                  Your credentials have been provisioned with <strong className="text-amber-400">Public Viewer</strong> tier. Operational roles (Analyst, Agency, Administrator) are activated following verification of organizational credentials by platform administrators.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-left text-xs text-slate-400 space-y-1">
                <div className="font-mono font-bold text-[11px] text-slate-300 uppercase">Verification Notice</div>
                <p className="text-[11px]">
                  Government & institutional accounts (@gov.in, @nic.in, @isro.res.in, authorized enterprises) are prioritized for operational clearance.
                </p>
              </div>

              <Link
                href="/login"
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-xs tracking-wider shadow-lg shadow-amber-500/20 inline-flex items-center justify-center gap-2 transition-all cursor-pointer"
              >
                <span>Proceed to Login</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          ) : (
            <>
              {/* Access Policy Banner */}
              <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-300 flex items-start gap-2.5">
                <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <div className="font-mono font-bold text-[11px] text-cyan-300 uppercase">Credentialing Policy</div>
                  <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
                    All accounts are initially provisioned with Public Viewer permissions. Operational command features are activated post-verification.
                  </p>
                </div>
              </div>

              {error && (
                <div className="p-3.5 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 text-xs flex items-center gap-2.5">
                  <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                  <span>{error}</span>
                </div>
              )}

              <form className="space-y-4" onSubmit={handleSubmit}>
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
                        className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
                        placeholder="Dr. Vikram Sarabhai"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5 font-mono">
                      Organization / Agency
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                        <Building className="w-4 h-4" />
                      </div>
                      <input
                        type="text"
                        required
                        disabled={loading}
                        value={organization}
                        onChange={(e) => setOrganization(e.target.value)}
                        className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
                        placeholder="NDMA / CPCB / State PCB / Forest Dept"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
                      Official Work Email
                    </label>
                    <span className="text-[10px] text-slate-500 font-mono">Institutional domain preferred</span>
                  </div>
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
                      placeholder="officer@organization.gov.in"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5 font-mono">
                      Passcode
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
                        className="w-full pl-9 pr-10 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
                        placeholder="Min 8 characters"
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

                  <div>
                    <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5 font-mono">
                      Confirm Passcode
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
                        className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
                        placeholder="Re-enter passcode"
                      />
                    </div>
                  </div>
                </div>

                <div className="text-[10px] text-slate-500 font-mono">
                  Complexity: Minimum 8 characters, with letters and numbers.
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-xs tracking-wider shadow-lg shadow-amber-500/20 flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                      <span>Submitting Access Request...</span>
                    </>
                  ) : (
                    <>
                      <span>Submit Access Request</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>

              <div className="text-center text-xs text-slate-400 border-t border-slate-800 pt-4">
                Already have an authorized profile?{" "}
                <Link href="/login" className="text-amber-400 hover:underline font-bold">
                  Sign In
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
