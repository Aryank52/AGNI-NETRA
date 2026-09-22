"use client";

import React, { useState } from "react";
import TopBar from "./TopBar";
import Sidebar from "./Sidebar";
import { useAuth } from "@/lib/authContext";

export interface AppShellProps {
  children: React.ReactNode;
  activePath?: string;
  className?: string;
}

export default function AppShell({ children, className = "" }: AppShellProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user } = useAuth();

  return (
    <div className="flex flex-col h-screen w-screen bg-agni-navy text-slate-100 overflow-hidden font-sans select-none">
      {/* TopBar */}
      <TopBar onToggleSidebar={() => setMobileMenuOpen(!mobileMenuOpen)} />

      {/* Main Workspace Frame */}
      <div className="flex flex-1 min-h-0 overflow-hidden relative">
        {/* Desktop Sidebar */}
        <div className="hidden md:flex h-full shrink-0">
          <Sidebar
            collapsed={sidebarCollapsed}
            onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          />
        </div>

        {/* Mobile Sidebar Overlay / Drawer */}
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-40 md:hidden flex">
            <div
              className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity"
              onClick={() => setMobileMenuOpen(false)}
            />
            <div className="relative flex-1 flex flex-col max-w-xs w-full bg-slate-950 z-50 h-full">
              <Sidebar onToggleCollapse={() => setMobileMenuOpen(false)} />
            </div>
          </div>
        )}

        {/* Primary Operational Content Canvas */}
        <main
          className={`flex-1 min-w-0 h-full overflow-y-auto overflow-x-hidden bg-slate-950/60 p-4 md:p-6 lg:p-8 ${className}`}
        >
          <div className="max-w-7xl mx-auto w-full space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
