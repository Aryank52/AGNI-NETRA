/**
 * AGNI-NETRA — Safe Value & Formatting Utilities
 * Provides resilient, null-safe parsing, formatting, and array extraction
 * to prevent runtime client-side exceptions across all portals.
 */

export function safeNumber(val: any, fallback: number = 0): number {
  if (val === null || val === undefined) return fallback;
  const num = typeof val === "number" ? val : parseFloat(val);
  return isNaN(num) ? fallback : num;
}

export function formatNumber(val: any, decimals: number = 1, fallback: string = "0.0"): string {
  if (val === null || val === undefined) return fallback;
  const num = typeof val === "number" ? val : parseFloat(val);
  if (isNaN(num)) return fallback;
  return num.toFixed(decimals);
}

export function formatFrp(val: any, fallback: string = "0.0 MW"): string {
  if (val === null || val === undefined) return fallback;
  const num = typeof val === "number" ? val : parseFloat(val);
  if (isNaN(num)) return fallback;
  return `${num.toFixed(1)} MW`;
}

export function formatPercent(val: any, decimals: number = 1, fallback: string = "0.0%"): string {
  if (val === null || val === undefined) return fallback;
  const num = typeof val === "number" ? val : parseFloat(val);
  if (isNaN(num)) return fallback;
  // If value is a fraction 0-1, convert to percentage
  const pct = num <= 1.0 && num >= 0 ? num * 100 : num;
  return `${pct.toFixed(decimals)}%`;
}

export function formatDate(val: any, fallback: string = "N/A"): string {
  if (!val) return fallback;
  try {
    const d = new Date(val);
    if (isNaN(d.getTime())) return fallback;
    return d.toLocaleDateString("en-IN", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return fallback;
  }
}

export function formatDateTime(val: any, fallback: string = "N/A"): string {
  if (!val) return fallback;
  try {
    const d = new Date(val);
    if (isNaN(d.getTime())) return fallback;
    return d.toLocaleString("en-IN", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return fallback;
  }
}

export function formatCoord(lat: any, lon: any, decimals: number = 4): string {
  const safeLat = safeNumber(lat, 0);
  const safeLon = safeNumber(lon, 0);
  return `${safeLat.toFixed(decimals)}°N, ${safeLon.toFixed(decimals)}°E`;
}

export function formatDistance(meters: any, fallback: string = "N/A"): string {
  if (meters === null || meters === undefined) return fallback;
  const m = safeNumber(meters, -1);
  if (m < 0) return fallback;
  if (m < 1000) return `${Math.round(m)} m`;
  return `${(m / 1000).toFixed(2)} km`;
}

export function safeArray<T = any>(val: any): T[] {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  if (typeof val === "string") {
    const trimmed = val.trim();
    return trimmed ? ([trimmed] as unknown as T[]) : [];
  }
  if (typeof val === "object" && val !== null) {
    if (Array.isArray(val.items)) return val.items;
    if (Array.isArray(val.alerts)) return val.alerts;
    if (Array.isArray(val.facilities)) return val.facilities;
    if (Array.isArray(val.results)) return val.results;
    if (Array.isArray(val.cases)) return val.cases;
    if (Array.isArray(val.reasons)) return val.reasons;
  }
  return [];
}

export function normalizeAssessmentItems(val: any, fallback: string[] = []): string[] {
  if (!val) return fallback;
  if (Array.isArray(val)) {
    const items = val
      .map((item) => {
        if (typeof item === "string") return item.trim();
        if (typeof item === "object" && item !== null) {
          return item.text || item.label || item.description || item.reason || "";
        }
        return String(item || "");
      })
      .filter((s) => s.length > 0);
    return items.length > 0 ? items : fallback;
  }
  if (typeof val === "string") {
    const trimmed = val.trim();
    return trimmed.length > 0 ? [trimmed] : fallback;
  }
  if (typeof val === "object" && val !== null) {
    if (Array.isArray(val.items)) return normalizeAssessmentItems(val.items, fallback);
    if (Array.isArray(val.reasons)) return normalizeAssessmentItems(val.reasons, fallback);
    if (Array.isArray(val.points)) return normalizeAssessmentItems(val.points, fallback);
    if (val.structured_explanation && typeof val.structured_explanation === "object") {
      const parts = Object.values(val.structured_explanation).filter((v) => typeof v === "string") as string[];
      if (parts.length > 0) return parts;
    }
    const knownKeys = ["physical_detection", "spatial_proximity", "persistence_pattern", "calibrated_risk", "summary", "text", "description"];
    const extracted: string[] = [];
    for (const k of knownKeys) {
      if (typeof val[k] === "string" && val[k].trim()) {
        extracted.push(val[k].trim());
      }
    }
    if (extracted.length > 0) return extracted;
    const strValues = Object.values(val).filter((v) => typeof v === "string" && (v as string).trim().length > 0) as string[];
    if (strValues.length > 0) return strValues;
  }
  return fallback;
}

export function normalizeAssessmentSummary(val: any, fallback: string = ""): string {
  if (!val) return fallback;
  if (typeof val === "string") return val.trim() || fallback;
  if (Array.isArray(val)) {
    const str = val.filter((x) => typeof x === "string").join(" ");
    return str.trim() || fallback;
  }
  if (typeof val === "object" && val !== null) {
    if (typeof val.summary === "string" && val.summary.trim()) return val.summary.trim();
    if (typeof val.description === "string" && val.description.trim()) return val.description.trim();
    if (val.structured_explanation && typeof val.structured_explanation === "object") {
      const parts = Object.values(val.structured_explanation).filter((v) => typeof v === "string") as string[];
      if (parts.length > 0) return parts.join(" ");
    }
    const strValues = Object.values(val).filter((v) => typeof v === "string" && (v as string).trim().length > 0) as string[];
    if (strValues.length > 0) return strValues.join(" ");
  }
  return fallback;
}


