import "server-only";

import { cookies } from "next/headers";

import {
  COOKIE_ACCESS,
  COOKIE_REFRESH,
  REFRESH_MAX_AGE,
} from "@/lib/config";

const isProd = process.env.NODE_ENV === "production";

/**
 * Schreibt Access- und Refresh-Token als httpOnly-Cookies.
 * Darf nur aus Server Actions oder Route Handlern aufgerufen werden.
 */
export async function setTokens(access: string, refresh: string) {
  const store = await cookies();
  const base = {
    httpOnly: true,
    secure: isProd,
    sameSite: "lax" as const,
    path: "/",
  };
  store.set(COOKIE_ACCESS, access, { ...base, maxAge: REFRESH_MAX_AGE });
  store.set(COOKIE_REFRESH, refresh, { ...base, maxAge: REFRESH_MAX_AGE });
}

/** Aktualisiert nur das Access-Token (z. B. nach einem Refresh). */
export async function setAccessToken(access: string) {
  const store = await cookies();
  store.set(COOKIE_ACCESS, access, {
    httpOnly: true,
    secure: isProd,
    sameSite: "lax",
    path: "/",
    maxAge: REFRESH_MAX_AGE,
  });
}

export async function clearTokens() {
  const store = await cookies();
  store.delete(COOKIE_ACCESS);
  store.delete(COOKIE_REFRESH);
}

export async function getAccessToken(): Promise<string | undefined> {
  return (await cookies()).get(COOKIE_ACCESS)?.value;
}

export async function getRefreshToken(): Promise<string | undefined> {
  return (await cookies()).get(COOKIE_REFRESH)?.value;
}
