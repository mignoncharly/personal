import { NextRequest, NextResponse } from "next/server";

import { API_URL } from "@/lib/config";
import {
  getAccessToken,
  getRefreshToken,
  setAccessToken,
} from "@/lib/session";

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

/** Lädt das Rechnungs-PDF vom Backend (mit JWT) und reicht es an den Browser durch. */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const inline = request.nextUrl.searchParams.get("inline") ? "?inline=1" : "";
  const url = `${API_URL}/invoices/${id}/pdf/${inline}`;

  const fetchPdf = (token?: string) =>
    fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      cache: "no-store",
    });

  let token = await getAccessToken();
  let res = await fetchPdf(token);

  if (res.status === 401) {
    const fresh = await refresh();
    if (fresh) {
      token = fresh;
      res = await fetchPdf(token);
    }
  }

  if (!res.ok) {
    return NextResponse.json(
      { error: "PDF konnte nicht erzeugt werden." },
      { status: res.status },
    );
  }

  const body = await res.arrayBuffer();
  const headers = new Headers();
  headers.set("Content-Type", "application/pdf");
  const disposition = res.headers.get("Content-Disposition");
  if (disposition) headers.set("Content-Disposition", disposition);
  return new NextResponse(body, { status: 200, headers });
}
