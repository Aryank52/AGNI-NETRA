"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  fallbackMessage?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an unhandled client error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 rounded-xl bg-slate-900/90 border border-red-500/30 text-slate-200 space-y-4 my-2">
          <div className="flex items-center gap-3 text-red-400">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <h3 className="font-bold text-sm">
              {this.props.fallbackTitle || "Component Encountered a Client Exception"}
            </h3>
          </div>
          <p className="text-xs text-slate-400">
            {this.props.fallbackMessage ||
              "An unexpected runtime issue occurred in this panel. The rest of the platform remains fully operational."}
          </p>
          {this.state.error && (
            <pre className="p-2.5 rounded bg-slate-950 text-[11px] font-mono text-red-300 overflow-x-auto max-h-32 border border-slate-800">
              {this.state.error.message || String(this.state.error)}
            </pre>
          )}
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Panel</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
