export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function getApiDocsUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/api\/v1\/?$/, "/docs");
  }
  return "http://127.0.0.1:8000/docs";
}

export interface FetchApiOptions extends RequestInit {
  timeoutMs?: number;
  skipCache?: boolean;
}

// =============================================================================
// Bounded Concurrency & In-Flight Request Deduplication Controls
// =============================================================================
const MAX_CONCURRENT_REQUESTS = 5;
let activeRequestCount = 0;
const requestQueue: Array<() => void> = [];

function acquireRequestSlot(): Promise<void> {
  if (activeRequestCount < MAX_CONCURRENT_REQUESTS) {
    activeRequestCount++;
    return Promise.resolve();
  }
  return new Promise((resolve) => {
    requestQueue.push(resolve);
  });
}

function releaseRequestSlot(): void {
  if (requestQueue.length > 0) {
    const nextResolve = requestQueue.shift()!;
    nextResolve();
  } else {
    activeRequestCount = Math.max(0, activeRequestCount - 1);
  }
}

// In-flight GET promise deduplication
const inFlightRequests = new Map<string, Promise<any>>();

// In-memory response cache for static GIS & boundary data (5-minute TTL)
interface CacheEntry {
  data: any;
  expiresAt: number;
}
const responseCache = new Map<string, CacheEntry>();
const CACHEABLE_ENDPOINTS = [
  "/geography/states",
  "/gis/admin/states",
  "/gis/admin/districts",
  "/gis/protected-areas",
  "/gis/lulc",
];

function isEndpointCacheable(endpoint: string): boolean {
  return CACHEABLE_ENDPOINTS.some((prefix) => endpoint.startsWith(prefix));
}

export async function fetchApi<T>(
  endpoint: string,
  options: FetchApiOptions = {}
): Promise<T> {
  const method = (options.method || "GET").toUpperCase();
  const isGet = method === "GET";

  // 1. Check in-memory cache for static GIS / administrative endpoints
  if (isGet && !options.skipCache && isEndpointCacheable(endpoint)) {
    const cached = responseCache.get(endpoint);
    if (cached && cached.expiresAt > Date.now()) {
      return cached.data as T;
    }
  }

  // 2. In-flight request deduplication for identical GET requests
  if (isGet && inFlightRequests.has(endpoint)) {
    return inFlightRequests.get(endpoint) as Promise<T>;
  }

  const fetchPromise = (async (): Promise<T> => {
    // Acquire a bounded concurrency slot (max 5 simultaneous requests to protect backend)
    await acquireRequestSlot();

    const { timeoutMs = 20000, skipCache: _skip, ...fetchOptions } = options;
    const token = typeof window !== "undefined" ? localStorage.getItem("agni_token") : null;

    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...(fetchOptions.headers || {}),
    };

    if (token) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...fetchOptions,
        headers,
        credentials: "include",
        signal: fetchOptions.signal || controller.signal,
      });

      clearTimeout(timeoutId);

      if (!res.ok) {
        if (res.status === 401 && typeof window !== "undefined") {
          localStorage.removeItem("agni_token");
          localStorage.removeItem("agni_user");
          window.dispatchEvent(new CustomEvent("agni:unauthorized"));
        }
        let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
        try {
          const errJson = await res.json();
          errorDetail = errJson.detail || errorDetail;
        } catch {
          // use status text
        }
        throw new Error(errorDetail);
      }

      const data = await res.json();

      // Cache static GIS/geography data for 5 minutes
      if (isGet && isEndpointCacheable(endpoint)) {
        responseCache.set(endpoint, {
          data,
          expiresAt: Date.now() + 5 * 60 * 1000,
        });
      }

      return data as T;
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (err.name === "AbortError") {
        throw new Error(`Request timed out after ${timeoutMs}ms: ${endpoint}`);
      }
      throw err;
    } finally {
      releaseRequestSlot();
    }
  })();

  if (isGet) {
    inFlightRequests.set(endpoint, fetchPromise);
    fetchPromise.finally(() => {
      inFlightRequests.delete(endpoint);
    });
  }

  return fetchPromise;
}
