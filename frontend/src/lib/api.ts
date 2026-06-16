import "server-only";

import { API_URL } from "@/lib/config";
import {
  getAccessToken,
  getRefreshToken,
  setAccessToken,
} from "@/lib/session";

/** Fehler einer API-Antwort inkl. Status und (DRF-)Feldfehlern. */
export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, data: unknown, message?: string) {
    super(message ?? `API-Fehler ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }

  /** Liefert eine lesbare Fehlermeldung aus einer DRF-Fehlerantwort. */
  toUserMessage(): string {
    const d = this.data;
    if (typeof d === "string" && d) return d;
    if (d && typeof d === "object") {
      const obj = d as Record<string, unknown>;
      if (typeof obj.detail === "string") return obj.detail;
      const parts: string[] = [];
      for (const [key, val] of Object.entries(obj)) {
        const text = Array.isArray(val) ? val.join(" ") : String(val);
        parts.push(key === "non_field_errors" ? text : `${key}: ${text}`);
      }
      if (parts.length) return parts.join(" · ");
    }
    return this.message;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  /** Query-Parameter; undefined/leere Werte werden ausgelassen. */
  query?: Record<string, string | number | boolean | undefined | null>;
  /** Bei true wird kein Authorization-Header gesetzt (öffentliche Endpunkte). */
  noAuth?: boolean;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = `${API_URL}${path}`;
  if (!query) return url;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }
  const qs = params.toString();
  return qs ? `${url}?${qs}` : url;
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = await getRefreshToken();
  if (!refresh) return null;
  const res = await fetch(`${API_URL}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
    cache: "no-store",
  });
  if (!res.ok) return null;
  const data = (await res.json()) as { access?: string };
  if (!data.access) return null;
  // Best effort: Cookie aktualisieren. Während eines Renders verbietet Next das
  // Setzen von Cookies – dann greift der proaktive Refresh in proxy.ts.
  try {
    await setAccessToken(data.access);
  } catch {
    /* read-only Kontext (Render) – ignorieren */
  }
  return data.access;
}

/**
 * Zentraler API-Aufruf gegen das Django-Backend.
 * Hängt das Access-Token an und erneuert es bei 401 einmalig per Refresh-Token.
 */
export async function apiFetch<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, query, noAuth = false } = options;
  const url = buildUrl(path, query);

  const doFetch = async (token: string | undefined): Promise<Response> => {
    const headers: Record<string, string> = {};
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (token && !noAuth) headers["Authorization"] = `Bearer ${token}`;
    return fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      cache: "no-store",
    });
  };

  let token = noAuth ? undefined : await getAccessToken();
  let res = await doFetch(token);

  if (res.status === 401 && !noAuth) {
    const fresh = await refreshAccessToken();
    if (fresh) {
      token = fresh;
      res = await doFetch(token);
    }
  }

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  const data = text ? safeJson(text) : null;

  if (!res.ok) {
    throw new ApiError(res.status, data);
  }
  return data as T;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}
