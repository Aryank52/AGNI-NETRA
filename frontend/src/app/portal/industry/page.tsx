"use client";

import React, { useState, useEffect } from "react";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import { fetchApi } from "@/lib/api";
import { 
  Building2, ShieldCheck, Flame, Send, 
  CheckCircle2, RefreshCw, AlertCircle, FileText,
  Clock, Download
} from "lucide-react";

export default function IndustryPortalPage() {
  const [facilities, setFacilities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [declModalOpen, setDeclModalOpen] = useState(false);
  const [selectedFacName, setSelectedFacName] = useState("");
  const [facType, setFacType] = useState("PETROCHEMICAL");
  const [flareStack, setFlareStack] = useState("FLARE-STACK-01");
  const [duration, setDuration] = useState(4);
  const [contact, setContact] = useState("compliance@plant.in");
  const [notes, setNotes] = useState("");
  const [declSuccess, setDeclSuccess] = useState<string | null>(null);

  const loadFacilities = async () => {
    setLoading(true);
    try {
      const data = await fetchApi<any[]>("/portals/industry/facilities");
      setFacilities(data || []);
      if (data && data.length > 0) {
        setSelectedFacName(data[0].name);
      }
    } catch (err) {
      console.warn("Failed to load industry facilities:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFacilities();
  }, []);

  const handleDeclareSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetchApi<any>("/portals/industry/declare-emission", {
        method: "POST",
        body: JSON.stringify({
          facility_name: selectedFacName,
          facility_type: facType,
          state: "Gujarat",
          planned_operation: "Maintenance Flaring",
          flare_stack_id: flareStack,
          expected_duration_hours: Number(duration),
          declarer_contact: contact,
          notes: notes || "Routine shutdown flare protocol",
        }),
      });
      setDeclSuccess(res.reference_number || "CPCB-DECL-SUCCESS");
      setTimeout(() => {
        setDeclModalOpen(false);
        setDeclSuccess(null);
      }, 2000);
    } catch (err) {
      alert("Failed to submit declaration: " + err);
    }
  };

  return (
    <div className="min-h-screen bg-agni-navy flex flex-col selection:bg-amber-500 selection:text-slate-950">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-6 space-y-6 max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-agni-border pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold">
                  PLANT COMPLIANCE & MONITORING
                </span>
                <span className="text-xs text-slate-400">CPCB Self-Reporting & Emission Ledger</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2.5 mt-1">
                <Building2 className="w-6 h-6 text-amber-400" />
                Industry Portal & Self-Regulation Desk
              </h1>
              <p className="text-xs text-slate-400 mt-1">
                Register plant flare stacks, declare scheduled maintenance burns, monitor thermal emissions against state CPCB limits, and download verified green compliance certificates.
              </p>
            </div>

            <button
              onClick={() => setDeclModalOpen(true)}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 flex items-center gap-2 transition-all"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Declare Planned Flaring Notice</span>
            </button>
          </div>

          {/* Plant Registry Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {facilities.map((fac) => {
              const isGradeA = fac.green_rating === "GRADE A";
              const isGradeB = fac.green_rating === "GRADE B";

              return (
                <div
                  key={fac.id}
                  className="p-5 rounded-2xl bg-agni-card border border-agni-border hover:border-amber-500/40 transition-all space-y-3 shadow-xl"
                >
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                    <span className={`text-[9px] uppercase font-mono px-2 py-0.5 rounded font-bold ${
                      isGradeA
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                        : isGradeB
                        ? "bg-yellow-500/20 text-yellow-300 border border-yellow-500/30"
                        : "bg-red-500/20 text-red-300 border border-red-500/30"
                    }`}>
                      {fac.green_rating}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      STATUS: {fac.status}
                    </span>
                  </div>

                  <div>
                    <h3 className="font-bold text-sm text-white">{fac.name}</h3>
                    <div className="text-xs text-slate-400 mt-0.5">{fac.facility_type} • {fac.state} ({fac.district || "Industrial Area"})</div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 grid grid-cols-2 gap-2 text-xs font-mono">
                    <div>
                      <div className="text-slate-500 text-[10px]">THERMAL PASSES</div>
                      <div className="text-white font-bold">{fac.thermal_events_count} Detections</div>
                    </div>
                    <div>
                      <div className="text-slate-500 text-[10px]">OPERATING CYCLE</div>
                      <div className="text-emerald-400 font-bold">{fac.operating_hours || "24x7 Continuous"}</div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-xs">
                    <span className="text-slate-500 font-mono text-[11px]">
                      {fac.latitude.toFixed(2)}°N, {fac.longitude.toFixed(2)}°E
                    </span>
                    <button
                      onClick={() => {
                        setSelectedFacName(fac.name);
                        setDeclModalOpen(true);
                      }}
                      className="text-amber-400 hover:text-amber-300 font-semibold text-xs"
                    >
                      Declare Flaring →
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Planned Emission Declaration Modal */}
          {declModalOpen && (
            <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 z-50 animate-in fade-in">
              <div className="w-full max-w-lg bg-agni-card border border-agni-border rounded-2xl p-6 shadow-2xl space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
                    <Flame className="w-4 h-4 text-amber-400" />
                    Planned Flaring / Maintenance Declaration
                  </h3>
                  <button
                    onClick={() => setDeclModalOpen(false)}
                    className="text-slate-400 hover:text-white"
                  >
                    ✕
                  </button>
                </div>

                {declSuccess ? (
                  <div className="p-6 text-center space-y-2 text-emerald-400">
                    <CheckCircle2 className="w-10 h-10 mx-auto animate-bounce" />
                    <div className="font-bold text-sm">Flaring Notice Registered!</div>
                    <div className="font-mono text-xs text-amber-300">Ref: {declSuccess}</div>
                    <p className="text-xs text-slate-400">Suppression protocol enabled for automated false alarms.</p>
                  </div>
                ) : (
                  <form onSubmit={handleDeclareSubmit} className="space-y-4 text-xs">
                    <div>
                      <label className="block font-semibold text-slate-300 mb-1">
                        Facility Name
                      </label>
                      <input
                        type="text"
                        value={selectedFacName}
                        onChange={(e) => setSelectedFacName(e.target.value)}
                        className="w-full p-2 rounded-xl bg-slate-900 border border-slate-700 text-white font-medium focus:outline-none focus:border-amber-500"
                        required
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block font-semibold text-slate-300 mb-1">
                          Flare Stack ID
                        </label>
                        <input
                          type="text"
                          value={flareStack}
                          onChange={(e) => setFlareStack(e.target.value)}
                          className="w-full p-2 rounded-xl bg-slate-900 border border-slate-700 text-white font-mono"
                          required
                        />
                      </div>
                      <div>
                        <label className="block font-semibold text-slate-300 mb-1">
                          Duration (Hours)
                        </label>
                        <input
                          type="number"
                          value={duration}
                          onChange={(e) => setDuration(Number(e.target.value))}
                          className="w-full p-2 rounded-xl bg-slate-900 border border-slate-700 text-white font-mono"
                          min="1"
                          max="72"
                          required
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block font-semibold text-slate-300 mb-1">
                        Compliance Contact Email
                      </label>
                      <input
                        type="email"
                        value={contact}
                        onChange={(e) => setContact(e.target.value)}
                        className="w-full p-2 rounded-xl bg-slate-900 border border-slate-700 text-white font-mono"
                        required
                      />
                    </div>

                    <div>
                      <label className="block font-semibold text-slate-300 mb-1">
                        Maintenance Reason / Safety Notes
                      </label>
                      <textarea
                        rows={3}
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        placeholder="e.g. Hydrocracker unit scheduled depressurization protocol..."
                        className="w-full p-2 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder:text-slate-600 focus:outline-none focus:border-amber-500"
                      />
                    </div>

                    <div className="flex items-center justify-end gap-3 pt-2">
                      <button
                        type="button"
                        onClick={() => setDeclModalOpen(false)}
                        className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold shadow-md shadow-amber-500/20"
                      >
                        Submit Notice
                      </button>
                    </div>
                  </form>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
