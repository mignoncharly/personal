import { NextResponse } from "next/server";

import { API_URL } from "@/lib/config";
import { getAccessToken, getRefreshToken, setAccessToken } from "@/lib/session";

async function refresh(): Promise<string | null> {
  const token = await getRefreshToken();
  if (!token) return null;
  const res = await fetch(`${API_URL}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: token }),
    cache: "no-store",
  });
  if (!res.ok) return null;
  const data = (await res.json()) as { access?: string };
  if (!data.access) return null;
  try {
    await setAccessToken(data.access);
  } catch {
    /* read-only Kontext – ignorieren */
  }
  return data.access;
}

/**
 * Lädt eine Datei (CSV/PDF …) vom Backend mit JWT und reicht sie an den Browser
 * durch. Erneuert das Access-Token bei 401 einmalig. `search` (z. B. aktive
 * Filter) wird an das Backend weitergegeben.
 */
export async function proxyDownload(
  backendPath: string,
  search?: URLSearchParams,
): Promise<NextResponse> {
  const qs = search && [...search.keys()].length ? `?${search.toString()}` : "";
  const url = `${API_URL}${backendPath}${qs}`;

  const doFetch = (token?: string) =>
    fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      cache: "no-store",
    });

  let token = await getAccessToken();
  let res = await doFetch(token);
  if (res.status === 401) {
    const fresh = await refresh();
    if (fresh) {
      token = fresh;
      res = await doFetch(token);
    }
  }

  if (!res.ok) {
    return NextResponse.json(
      { error: "Download fehlgeschlagen." },
      { status: res.status },
    );
  }

  const body = await res.arrayBuffer();
  const headers = new Headers();
  const contentType = res.headers.get("Content-Type");
  if (contentType) headers.set("Content-Type", contentType);
  const disposition = res.headers.get("Content-Disposition");
  if (disposition) headers.set("Content-Disposition", disposition);
  return new NextResponse(body, { status: 200, headers });
}
