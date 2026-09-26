"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { User, UserRole } from "@/types";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, passwordOrRole?: string, role?: UserRole) => Promise<void>;
  logout: () => void;
  switchRole: (role: UserRole) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DEMO_PROFILES: Record<UserRole, User> = {
  ADMIN: {
    id: "demo-admin-id",
    email: "admin@agninetra.gov.in",
    full_name: "Dr. Rajesh Sharma",
    role: "ADMIN",
    organization: "ISRO / Remote Sensing Centre",
    is_active: true,
    created_at: new Date().toISOString(),
  },
  ANALYST: {
    id: "demo-analyst-id",
    email: "analyst@agninetra.gov.in",
    full_name: "Priya Verma",
    role: "ANALYST",
    organization: "Central Pollution Control Board",
    is_active: true,
    created_at: new Date().toISOString(),
  },
  RESEARCHER: {
    id: "demo-researcher-id",
    email: "researcher@isro.res.in",
    full_name: "Dr. Amit Roy",
    role: "RESEARCHER",
    organization: "Indian Institute of Remote Sensing",
    is_active: true,
    created_at: new Date().toISOString(),
  },
  INDUSTRY: {
    id: "demo-industry-id",
    email: "industry@reliance.com",
    full_name: "Vikram Patel",
    role: "INDUSTRY",
    organization: "Reliance Jamnagar Operations",
    is_active: true,
    created_at: new Date().toISOString(),
  },
  AGENCY: {
    id: "demo-agency-id",
    email: "agency@ndma.gov.in",
    full_name: "Col. S. Deshmukh",
    role: "AGENCY",
    organization: "National Disaster Management Authority",
    is_active: true,
    created_at: new Date().toISOString(),
  },
  PUBLIC: {
    id: "demo-public-id",
    email: "public@user.in",
    full_name: "Rohan Mehta",
    role: "PUBLIC",
    organization: "Public Safety Viewer",
    is_active: true,
    created_at: new Date().toISOString(),
  },
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const isDevAuthEnabled =
  process.env.NEXT_PUBLIC_ENABLE_DEV_AUTH === "true" ||
  (process.env.NODE_ENV === "development" && process.env.NEXT_PUBLIC_ENABLE_DEV_AUTH !== "false");

async function fetchRoleToken(role: UserRole) {
  if (!isDevAuthEnabled) {
    return null;
  }
  try {
    const res = await fetch(`${API_BASE_URL}/auth/dev-token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role }),
    });
    if (res.ok) {
      const data = await res.json();
      return { token: data.access_token as string, user: data.user as User };
    }
  } catch (err) {
    console.warn("Dev token fetch failed, fallback:", err);
  }
  return null;
}

function isTokenExpired(jwtToken: string): boolean {
  try {
    const parts = jwtToken.split(".");
    if (parts.length !== 3) return true;
    const payload = JSON.parse(atob(parts[1]));
    if (!payload.exp) return false;
    // Buffer by 30 seconds before expiration
    return (payload.exp * 1000) <= (Date.now() + 30000);
  } catch {
    return true;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  const refreshAuthToken = async (role: UserRole = "ANALYST") => {
    if (!isDevAuthEnabled) return;
    const auth = await fetchRoleToken(role);
    if (auth) {
      setUser(auth.user);
      setToken(auth.token);
      localStorage.setItem("agni_user", JSON.stringify(auth.user));
      localStorage.setItem("agni_token", auth.token);
    } else {
      setUser(DEMO_PROFILES[role] || DEMO_PROFILES.ANALYST);
    }
  };

  useEffect(() => {
    const savedUser = localStorage.getItem("agni_user");
    const savedToken = localStorage.getItem("agni_token");
    if (savedToken && savedToken.startsWith("ey") && savedUser && !isTokenExpired(savedToken)) {
      try {
        setUser(JSON.parse(savedUser));
        setToken(savedToken);
        return;
      } catch {}
    }

    // Cached token missing, invalid, or expired -> purge storage
    localStorage.removeItem("agni_user");
    localStorage.removeItem("agni_token");

    // Only auto-mint dev session when explicitly enabled in development
    if (isDevAuthEnabled) {
      refreshAuthToken("ANALYST");
    } else {
      setUser(null);
      setToken(null);
    }

    // Listen for unauthorized 401 events to auto-refresh session (dev only) or reset session
    const handleUnauthorized = () => {
      if (isDevAuthEnabled) {
        refreshAuthToken("ANALYST");
      } else {
        setUser(null);
        setToken(null);
        localStorage.removeItem("agni_user");
        localStorage.removeItem("agni_token");
      }
    };
    window.addEventListener("agni:unauthorized", handleUnauthorized);
    return () => window.removeEventListener("agni:unauthorized", handleUnauthorized);
  }, []);

  const login = async (email: string, passwordOrRole?: string, role?: UserRole) => {
    const isRole = (val?: string): val is UserRole =>
      !!val && ["ADMIN", "ANALYST", "RESEARCHER", "INDUSTRY", "AGENCY", "PUBLIC"].includes(val);

    const password = typeof passwordOrRole === "string" && !isRole(passwordOrRole) ? passwordOrRole : undefined;
    const targetRole: UserRole = role || (isRole(passwordOrRole) ? passwordOrRole : "ANALYST");

    if (password) {
      // Real authentication flow using standard OAuth2 password request endpoint
      const body = new URLSearchParams();
      body.append("username", email);
      body.append("password", password);

      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
      });

      if (!res.ok) {
        let errorMsg = `HTTP ${res.status}: Authentication failed`;
        try {
          const errData = await res.json();
          errorMsg = errData.detail || errorMsg;
        } catch {}
        throw new Error(errorMsg);
      }

      const data = await res.json();
      setUser(data.user);
      setToken(data.access_token);
      localStorage.setItem("agni_user", JSON.stringify(data.user));
      localStorage.setItem("agni_token", data.access_token);
      return;
    }

    // Development-only fallback: only fetch dev-token when explicitly enabled
    if (isDevAuthEnabled) {
      const auth = await fetchRoleToken(targetRole);
      if (auth) {
        setUser(auth.user);
        setToken(auth.token);
        localStorage.setItem("agni_user", JSON.stringify(auth.user));
        localStorage.setItem("agni_token", auth.token);
        return;
      }
    }

    const profile = DEMO_PROFILES[targetRole] || DEMO_PROFILES.ANALYST;
    setUser(profile);
    localStorage.setItem("agni_user", JSON.stringify(profile));
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("agni_user");
    localStorage.removeItem("agni_token");
  };

  const switchRole = async (role: UserRole) => {
    if (isDevAuthEnabled) {
      const auth = await fetchRoleToken(role);
      if (auth) {
        setUser(auth.user);
        setToken(auth.token);
        localStorage.setItem("agni_user", JSON.stringify(auth.user));
        localStorage.setItem("agni_token", auth.token);
        return;
      }
    }
    const profile = DEMO_PROFILES[role] || DEMO_PROFILES.ANALYST;
    setUser(profile);
    localStorage.setItem("agni_user", JSON.stringify(profile));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        login,
        logout,
        switchRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
