import { NextRequest, NextResponse } from "next/server";

import {
  API_URL,
  COOKIE_ACCESS,
  COOKIE_REFRESH,
  REFRESH_MAX_AGE,
} from "@/lib/config";

// Öffentliche Routen (kein Login nötig). Alles andere ist geschützt.
const PUBLIC_ROUTES = ["/login", "/passwort-reset"];

const isProd = process.env.NODE_ENV === "production";

/** Liest den Ablaufzeitpunkt (exp, Sekunden) aus einem JWT, ohne Signaturprüfung. */
function jwtExp(token: string): number | null {
  try {
    const payload = token.split(".")[1];
    const json = Buffer.from(payload, "base64url").toString("utf8");
    const data = JSON.parse(json) as { exp?: number };
    return typeof data.exp === "number" ? data.exp : null;
  } catch {
    return null;
  }
}

async function refreshAccess(refresh: string): Promise<string | null> {
  try {
    const res = await fetch(`${API_URL}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
      cache: "no-store",
    });
    if (!res.ok) return null;
    const data = (await res.json()) as { access?: string };
    return data.access ?? null;
  } catch {
    return null;
  }
}

export async function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const isPublic = PUBLIC_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );

  const access = req.cookies.get(COOKIE_ACCESS)?.value;
  const refresh = req.cookies.get(COOKIE_REFRESH)?.value;
  const hasSession = Boolean(access || refresh);

  // Angemeldete Nutzer von öffentlichen Auth-Seiten wegleiten.
  if (isPublic) {
    if (hasSession && pathname === "/login") {
      return NextResponse.redirect(new URL("/dashboard", req.nextUrl));
    }
    return NextResponse.next();
  }

  // Geschützte Route ohne jegliche Session → Login.
  if (!hasSession) {
    const url = new URL("/login", req.nextUrl);
    if (pathname !== "/") url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  // Proaktiver Refresh: Access-Token fehlt oder läuft in < 60 s ab.
  const exp = access ? jwtExp(access) : null;
  const expiringSoon = exp !== null && exp - Date.now() / 1000 < 60;
  if ((!access || expiringSoon) && refresh) {
    const fresh = await refreshAccess(refresh);
    if (fresh) {
      const res = NextResponse.next();
      res.cookies.set(COOKIE_ACCESS, fresh, {
        httpOnly: true,
        secure: isProd,
        sameSite: "lax",
        path: "/",
        maxAge: REFRESH_MAX_AGE,
      });
      return res;
    }
  }

  return NextResponse.next();
}

export const config = {
  // Nicht auf statische Assets / Next-Interna laufen lassen.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.svg$).*)"],
};
