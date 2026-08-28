"use client";

import React, { useState, useEffect } from "react";
import { Play, Pause, RotateCcw, Clock } from "lucide-react";

interface TimeSliderProps {
  selectedRange: string;
  onSelectRange: (range: string) => void;
}

const RANGES = [
  { id: "24h", label: "24 Hours" },
  { id: "7d", label: "7 Days" },
  { id: "30d", label: "30 Days" },
  { id: "6m", label: "6 Months" },
  { id: "1y", label: "1 Year" },
];

export default function TimeSlider({ selectedRange, onSelectRange }: TimeSliderProps) {
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        const currentIndex = RANGES.findIndex((r) => r.id === selectedRange);
        const nextIndex = (currentIndex + 1) % RANGES.length;
        onSelectRange(RANGES[nextIndex].id);
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [isPlaying, selectedRange, onSelectRange]);

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 w-[90%] max-w-xl bg-agni-card/90 border border-agni-border/80 rounded-2xl p-3 shadow-2xl backdrop-blur-xl">
      <div className="flex items-center justify-between gap-4">
        {/* Play / Pause Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="p-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 transition-colors shadow-md shadow-amber-500/20"
            title={isPlaying ? "Pause Timeline Playback" : "Start Temporal Playback"}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-current" />}
          </button>
          <div className="hidden sm:flex items-center gap-1.5 text-[11px] font-mono text-slate-400">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>TIMELINE</span>
          </div>
        </div>

        {/* Range Buttons */}
        <div className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-xl border border-slate-800 grow justify-between">
          {RANGES.map((r) => {
            const isSelected = selectedRange === r.id;
            return (
              <button
                key={r.id}
                onClick={() => {
                  setIsPlaying(false);
                  onSelectRange(r.id);
                }}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                  isSelected
                    ? "bg-amber-500 text-slate-950 shadow-md font-bold"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                {r.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
