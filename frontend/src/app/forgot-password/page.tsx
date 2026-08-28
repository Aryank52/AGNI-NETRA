"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  Flame, KeyRound, Mail, ArrowRight, 
  ArrowLeft, CheckCircle2, AlertCircle 
} from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setSent(true);
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 selection:bg-amber-500 selection:text-slate-950">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link href="/" className="inline-flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/30">
            <Flame className="w-6 h-6 text-slate-950 fill-slate-950" />
          </div>
          <span className="font-extrabold text-2xl tracking-wider text-white">
            AGNI<span className="text-amber-400 font-mono">-NETRA</span>
          </span>
        </Link>
        <h2 className="mt-4 text-xl font-extrabold text-white tracking-tight">
          Reset Security Passcode
        </h2>
        <p className="mt-1 text-xs text-slate-400">
          Enter your registered agency/organization email address
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-agni-card py-8 px-6 shadow-2xl rounded-2xl sm:px-10 border border-agni-border space-y-6">
          {sent ? (
            <div className="p-4 text-center space-y-3 text-emerald-400">
              <CheckCircle2 className="w-12 h-12 mx-auto animate-bounce" />
              <div className="text-sm font-bold text-white">Recovery Dispatch Sent!</div>
              <p className="text-xs text-slate-400">
                If <span className="text-amber-400 font-mono">{email}</span> matches an active identity, a secure one-time passcode reset token has been dispatched.
              </p>
              <div className="pt-3">
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2 text-xs font-bold text-amber-400 hover:underline"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  Return to Sign In
                </Link>
              </div>
            </div>
          ) : (
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div>
                <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                  Registered Email Address
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
                    placeholder="analyst@domain.gov.in"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-extrabold text-xs tracking-wider shadow-lg shadow-amber-500/20 flex items-center justify-center gap-2 transition-all"
              >
                <KeyRound className="w-4 h-4" />
                <span>{loading ? "Verifying Identity..." : "Dispatch Reset Link"}</span>
              </button>

              <div className="text-center pt-2">
                <Link
                  href="/login"
                  className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-white"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Back to Sign In</span>
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
