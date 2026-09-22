"use client";

import React from "react";
import { LucideIcon, Inbox, RefreshCw } from "lucide-react";
import Button from "./Button";

export interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export default function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  actionLabel,
  onAction,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center rounded-xl bg-slate-950/40 border border-slate-800/80 font-mono ${className}`}
    >
      <div className="w-11 h-11 rounded-xl bg-slate-900 border border-slate-700/60 flex items-center justify-center mb-3 text-slate-400">
        <Icon className="w-5 h-5 text-slate-400" />
      </div>
      <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">{title}</h4>
      <p className="text-xs text-slate-400 mt-1 max-w-sm font-sans leading-relaxed">
        {description}
      </p>
      {actionLabel && onAction && (
        <div className="mt-4">
          <Button variant="secondary" size="xs" onClick={onAction}>
            {actionLabel}
          </Button>
        </div>
      )}
    </div>
  );
}
