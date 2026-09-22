"use client";

import React, { useState } from "react";
import { 
  Terminal, ShieldCheck, HelpCircle, Activity, ChevronRight,
  Database, Layers, AlertTriangle, ArrowRight, UserCheck, CheckCircle2
} from "lucide-react";
import EpistemicBadge from "./EpistemicBadge";
import Lifecycle, { PipelineStage } from "./Lifecycle";

export interface StructuredJARVISPayload {
  assessment?: string;
  evidence?: string[];
  historical?: string;
  model?: string;
  uncertainty?: string;
  next_best_evidence?: string;
  prevention?: string;
  human_action?: string;
}

export interface JARVISCardProps {
  stage?: PipelineStage;
  eventRef?: string;
  payload: StructuredJARVISPayload;
  modelProvenance?: {
    candidateName?: string;
    isChampion?: boolean;
    calibratedScore?: number;
  };
  onExecuteHumanAction?: () => void;
  className?: string;
}

export default function JARVISCard({
  stage = "INVESTIGATING",
  eventRef,
  payload,
  modelProvenance = {
    candidateName: "xgb-v3.0-real-candidate",
    isChampion: false,
  },
  onExecuteHumanAction,
  className = "",
}: JARVISCardProps) {
  const [expandedSection, setExpandedSection] = useState<string | null>("assessment");

  const sections: { id: keyof StructuredJARVISPayload; label: string; icon: any; epistemic: string }[] = [
    { id: "assessment", label: "1. Grounded Assessment", icon: Terminal, epistemic: "OBSERVED" },
    { id: "evidence", label: "2. Empirical Evidence Fused", icon: Database, epistemic: "OBSERVED" },
    { id: "historical", label: "3. Historical Recurrence & Baseline", icon: Layers, epistemic: "DERIVED" },
    { id: "model", label: "4. ML Attribution & Governance", icon: Activity, epistemic: "INFERRED" },
    { id: "uncertainty", label: "5. Epistemic Uncertainty & Gaps", icon: HelpCircle, epistemic: "UNKNOWN" },
    { id: "next_best_evidence", label: "6. Next Best Evidence (NBE)", icon: ChevronRight, epistemic: "DERIVED" },
    { id: "prevention", label: "7. Root Cause & Prevention", icon: AlertTriangle, epistemic: "INFERRED" },
    { id: "human_action", label: "8. Governed Human Action Required", icon: UserCheck, epistemic: "DERIVED" },
  ];

  return (
    <div
      className={`rounded-xl border border-amber-500/30 bg-slate-900/90 shadow-lg relative overflow-hidden flex flex-col font-mono text-xs ${className}`}
    >
      {/* Header Banner */}
      <div className="p-3.5 bg-gradient-to-r from-amber-500/15 via-slate-900 to-slate-950 border-b border-amber-500/30 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
            <Terminal className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-amber-300 tracking-wider">
                JARVIS MASTER INTELLIGENCE OBSERVER
              </span>
              <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold">
                SINGLE MASTER
              </span>
            </div>
            {eventRef && (
              <p className="text-[10px] text-slate-400 font-normal">
                Synchronized Target: <strong className="text-slate-200">{eventRef}</strong>
              </p>
            )}
          </div>
        </div>

        {/* Candidate Model Invariant Badge */}
        <div className="hidden sm:flex items-center gap-2 text-[10px]">
          <span className="text-slate-400">Model:</span>
          <span className="px-1.5 py-0.2 rounded bg-purple-500/20 text-purple-300 border border-purple-500/40 font-bold">
            {modelProvenance.candidateName} (CANDIDATE)
          </span>
        </div>
      </div>

      {/* 7-Stage Pipeline Tracker */}
      <div className="p-2 border-b border-slate-800/80 bg-slate-950/40">
        <Lifecycle currentStage={stage} />
      </div>

      {/* 8 Structured Canonical Sections Accordion / Cards */}
      <div className="divide-y divide-slate-800/60 flex-1 overflow-y-auto max-h-[520px]">
        {sections.map((sec) => {
          const content = payload[sec.id];
          if (!content) return null;
          const isExpanded = expandedSection === sec.id;
          const Icon = sec.icon;

          return (
            <div key={sec.id} className="transition-colors">
              <button
                type="button"
                onClick={() => setExpandedSection(isExpanded ? null : sec.id)}
                className={`w-full p-3 flex items-center justify-between text-left transition-colors ${
                  isExpanded ? "bg-slate-800/40 text-amber-300" : "hover:bg-slate-800/20 text-slate-300"
                }`}
              >
                <div className="flex items-center gap-2">
                  <Icon className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <span className="font-semibold text-xs">{sec.label}</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <EpistemicBadge state={sec.epistemic} size="xs" />
                  <ChevronRight
                    className={`w-3.5 h-3.5 text-slate-400 transition-transform ${
                      isExpanded ? "rotate-90" : ""
                    }`}
                  />
                </div>
              </button>

              {isExpanded && (
                <div className="px-4 py-3 bg-slate-950/40 text-slate-300 text-xs font-sans leading-relaxed border-t border-slate-800/40">
                  {Array.isArray(content) ? (
                    <ul className="space-y-1.5 list-disc list-inside font-mono text-[11px] text-slate-200">
                      {content.map((item, idx) => (
                        <li key={idx} className="leading-snug">{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="whitespace-pre-line">{content}</p>
                  )}

                  {sec.id === "human_action" && onExecuteHumanAction && (
                    <div className="mt-3 pt-2.5 border-t border-slate-800 flex items-center justify-between">
                      <span className="text-[11px] text-amber-400/90 font-mono">
                        HITL Governance: Action requires authorized analyst sign-off
                      </span>
                      <button
                        type="button"
                        onClick={onExecuteHumanAction}
                        className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold font-mono text-xs flex items-center gap-1.5 shadow-sm transition-all"
                      >
                        <UserCheck className="w-3.5 h-3.5" />
                        <span>Perform Analyst Verification</span>
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer Invariant Notice */}
      <div className="p-2 px-3.5 bg-slate-950 border-t border-slate-800 text-[10px] text-slate-500 flex items-center justify-between">
        <span className="font-mono">NO AUTONOMOUS DISPATCH • HUMAN AUTHORIZED ONLY</span>
        <span className="text-emerald-500 font-mono font-semibold">GATE: ACTIVE</span>
      </div>
    </div>
  );
}
