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

export function safeArray<T>(val: any): T[] {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  if (val && Array.isArray(val.items)) return val.items;
  if (val && Array.isArray(val.alerts)) return val.alerts;
  if (val && Array.isArray(val.facilities)) return val.facilities;
  if (val && Array.isArray(val.results)) return val.results;
  return [];
}

