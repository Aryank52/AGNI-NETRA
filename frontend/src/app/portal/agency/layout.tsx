"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/authContext";

export default function AgencyPortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated || !user) {
      router.replace("/login?redirect=/portal/agency");
      return;
    }

    if (user.role === "PUBLIC") {
      router.replace("/portal/public");
      return;
    }
  }, [user, isAuthenticated, isLoading, router]);

  if (isLoading || !isAuthenticated || !user) {
    return (
      <div className="min-h-screen bg-agni-navy flex flex-col items-center justify-center text-slate-400">
        <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mb-3" />
        <span className="font-mono text-xs uppercase tracking-wider text-slate-400">
          Authenticating Agency Portal Access...
        </span>
      </div>
    );
  }

  if (user.role === "PUBLIC") {
    return (
      <div className="min-h-screen bg-agni-navy flex flex-col items-center justify-center text-slate-400">
        <span className="font-mono text-xs uppercase tracking-wider text-amber-400">
          Redirecting to Public Safety Portal...
        </span>
      </div>
    );
  }

  return <>{children}</>;
}
