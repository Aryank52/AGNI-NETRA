export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function getApiDocsUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/api\/v1\/?$/, "/docs");
  }
  return "http://127.0.0.1:8000/docs";
}

export interface FetchApiOptions extends RequestInit {
  timeoutMs?: number;
}

export async function fetchApi<T>(
  endpoint: string,
  options: FetchApiOptions = {}
): Promise<T> {
  const { timeoutMs = 12000, ...fetchOptions } = options;
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
      signal: fetchOptions.signal || controller.signal,
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const errJson = await res.json();
        errorDetail = errJson.detail || errorDetail;
      } catch {
        // use status text
      }
      throw new Error(errorDetail);
    }

    return await res.json();
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new Error(`Request timed out after ${timeoutMs}ms: ${endpoint}`);
    }
    throw err;
  }
}
