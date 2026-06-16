import "server-only";

import { cache } from "react";
import { redirect } from "next/navigation";

import { apiFetch, ApiError } from "@/lib/api";
import { getAccessToken } from "@/lib/session";
import type { Me } from "@/lib/types";

/**
 * Lädt das aktuelle Profil über /auth/me/. Per React-cache pro Render memoisiert.
 * Gibt null zurück, wenn keine gültige Session besteht.
 */
export const getCurrentUser = cache(async (): Promise<Me | null> => {
  if (!(await getAccessToken())) return null;
  try {
    return await apiFetch<Me>("/auth/me/");
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) return null;
    throw err;
  }
});

/** Erzwingt eine Anmeldung; leitet sonst auf /login um. */
export async function requireUser(): Promise<Me> {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  return user;
}

/** Erzwingt Admin-Rechte; leitet Nicht-Admins aufs Dashboard. */
export async function requireAdmin(): Promise<Me> {
  const user = await requireUser();
  if (!user.is_admin) redirect("/dashboard");
  return user;
}
