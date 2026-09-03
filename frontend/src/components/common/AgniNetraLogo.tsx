"use client";

import React from "react";

interface AgniNetraLogoProps {
  size?: number | "sm" | "md" | "lg";
  showText?: boolean;
  className?: string;
  textClassName?: string;
  subtext?: string;
}

export default function AgniNetraLogo({
  size = "md",
  showText = true,
  className = "",
  textClassName = "",
  subtext = "GEOSPATIAL THERMAL INTELLIGENCE",
}: AgniNetraLogoProps) {
  let pixelSize = 36;
  if (typeof size === "number") {
    pixelSize = size;
  } else if (size === "sm") {
    pixelSize = 28;
  } else if (size === "lg") {
    pixelSize = 48;
  }

  return (
    <div className={`inline-flex items-center gap-2.5 select-none ${className}`}>
      {/* Precision Vector Emblem: Satellite Aperture + Thermal Iris + Sensing Crosshairs */}
      <svg
        width={pixelSize}
        height={pixelSize}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="shrink-0 transition-transform duration-300 hover:scale-105 drop-shadow-[0_0_12px_rgba(245,158,11,0.35)]"
      >
        <defs>
          {/* Radiant Thermal Core */}
          <radialGradient id="agniCore" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="30%" stopColor="#fbbf24" />
            <stop offset="65%" stopColor="#f97316" />
            <stop offset="100%" stopColor="#ef4444" stopOpacity="0.9" />
          </radialGradient>

          {/* Optical Aperture Arc Gradient */}
          <linearGradient id="orbitalArc" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#38bdf8" />
            <stop offset="50%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#ef4444" />
          </linearGradient>

          {/* Geometric Iris Gradient */}
          <linearGradient id="irisRing" x1="0%" y1="50%" x2="100%" y2="50%">
            <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.8" />
            <stop offset="50%" stopColor="#fbbf24" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#0ea5e9" stopOpacity="0.8" />
          </linearGradient>
        </defs>

        {/* Outer Circular Geodesic Tracking Perimeter */}
        <circle
          cx="50"
          cy="50"
          r="45"
          stroke="#1e293b"
          strokeWidth="1.5"
          strokeDasharray="4 3"
        />

        {/* Satellite Sun-Synchronous Polar Orbital Ring */}
        <ellipse
          cx="50"
          cy="50"
          rx="44"
          ry="19"
          stroke="url(#orbitalArc)"
          strokeWidth="1.8"
          strokeDasharray="80 12"
          transform="rotate(-28 50 50)"
          className="opacity-90"
        />

        {/* Satellite Node on Orbit */}
        <g transform="rotate(-28 50 50)">
          <circle cx="94" cy="50" r="3" fill="#38bdf8" />
          <line x1="91" y1="50" x2="97" y2="50" stroke="#ffffff" strokeWidth="1" />
          <line x1="94" y1="47" x2="94" y2="53" stroke="#ffffff" strokeWidth="1" />
        </g>

        {/* Tactical Crosshairs (Geospatial Targeting) */}
        <line x1="50" y1="6" x2="50" y2="20" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round" />
        <line x1="50" y1="80" x2="50" y2="94" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round" />
        <line x1="6" y1="50" x2="20" y2="50" stroke="#38bdf8" strokeWidth="1.5" strokeLinecap="round" />
        <line x1="80" y1="50" x2="94" y2="50" stroke="#38bdf8" strokeWidth="1.5" strokeLinecap="round" />

        {/* Hexagonal Sensor Optical Aperture ("Netra" Eye) */}
        <polygon
          points="50,18 78,34 78,66 50,82 22,66 22,34"
          stroke="url(#irisRing)"
          strokeWidth="1.8"
          fill="#020617"
          fillOpacity="0.85"
        />

        {/* Intermediate Thermal Diamond */}
        <polygon
          points="50,26 71,50 50,74 29,50"
          stroke="#f59e0b"
          strokeWidth="1.2"
          strokeDasharray="3 2"
          fill="none"
          className="opacity-75"
        />

        {/* Inner Tri-Segmented Optical Iris Blades */}
        <path
          d="M 50 32 L 65 59 L 35 59 Z"
          stroke="#38bdf8"
          strokeWidth="1"
          fill="none"
          className="opacity-50"
        />
        <path
          d="M 50 68 L 35 41 L 65 41 Z"
          stroke="#ef4444"
          strokeWidth="1"
          fill="none"
          className="opacity-50"
        />

        {/* Central Core Thermal Radiance Flare ("Agni") */}
        <circle cx="50" cy="50" r="10.5" fill="url(#agniCore)" />
        <circle cx="50" cy="50" r="4.5" fill="#ffffff" />
      </svg>

      {/* Typography: Government & Intelligence Grade Aesthetic */}
      {showText && (
        <div className={`flex flex-col leading-tight ${textClassName}`}>
          <div className="flex items-center gap-1.5 tracking-wider">
            <span className="font-extrabold text-white font-mono tracking-widest text-base">
              AGNI<span className="text-amber-400 font-black">·</span>NETRA
            </span>
            <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
              IND
            </span>
          </div>
          <span className="text-[9px] font-mono tracking-widest uppercase text-slate-400 font-semibold truncate max-w-[190px]">
            {subtext}
          </span>
        </div>
      )}
    </div>
  );
}
