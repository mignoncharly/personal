/** Zentrale Konfiguration für den Zugriff auf das Django-Backend. */

/**
 * Basis-URL der API. Serverseitig (Server Components/Actions, proxy.ts) kann
 * eine interne Adresse via API_URL gesetzt werden; ansonsten greift die
 * öffentliche NEXT_PUBLIC_API_URL bzw. der lokale Default.
 */
export const API_URL =
  process.env.API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000/api";

export const COOKIE_ACCESS = "mp_access";
export const COOKIE_REFRESH = "mp_refresh";

/** Lebensdauer des Refresh-Cookies in Sekunden (= Refresh-Token, 7 Tage). */
export const REFRESH_MAX_AGE = 7 * 24 * 60 * 60;
