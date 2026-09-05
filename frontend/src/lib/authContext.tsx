"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { User, UserRole } from "@/types";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, role?: UserRole) => Promise<void>;
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

async function fetchRoleToken(role: UserRole) {
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

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const savedUser = localStorage.getItem("agni_user");
    const savedToken = localStorage.getItem("agni_token");
    if (savedToken && savedToken.startsWith("ey") && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
        setToken(savedToken);
        return;
      } catch {}
    }

    // Default to authentic Analyst session with valid cryptographic JWT
    fetchRoleToken("ANALYST").then((auth) => {
      if (auth) {
        setUser(auth.user);
        setToken(auth.token);
        localStorage.setItem("agni_user", JSON.stringify(auth.user));
        localStorage.setItem("agni_token", auth.token);
      } else {
        setUser(DEMO_PROFILES.ANALYST);
      }
    });
  }, []);

  const login = async (email: string, role: UserRole = "ANALYST") => {
    const auth = await fetchRoleToken(role);
    if (auth) {
      setUser(auth.user);
      setToken(auth.token);
      localStorage.setItem("agni_user", JSON.stringify(auth.user));
      localStorage.setItem("agni_token", auth.token);
    } else {
      const profile = DEMO_PROFILES[role] || DEMO_PROFILES.ANALYST;
      setUser(profile);
      localStorage.setItem("agni_user", JSON.stringify(profile));
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("agni_user");
    localStorage.removeItem("agni_token");
  };

  const switchRole = async (role: UserRole) => {
    const auth = await fetchRoleToken(role);
    if (auth) {
      setUser(auth.user);
      setToken(auth.token);
      localStorage.setItem("agni_user", JSON.stringify(auth.user));
      localStorage.setItem("agni_token", auth.token);
    } else {
      const profile = DEMO_PROFILES[role] || DEMO_PROFILES.ANALYST;
      setUser(profile);
      localStorage.setItem("agni_user", JSON.stringify(profile));
    }
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
