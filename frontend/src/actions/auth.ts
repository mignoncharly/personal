"use server";

import { redirect } from "next/navigation";

import { apiFetch, ApiError } from "@/lib/api";
import { clearTokens, setTokens } from "@/lib/session";
import type { TokenResponse } from "@/lib/types";

export interface FormState {
  error?: string;
  success?: string;
}

function safeNext(next: FormDataEntryValue | null): string {
  const value = typeof next === "string" ? next : "";
  // Nur interne Pfade zulassen (kein Open-Redirect).
  return value.startsWith("/") && !value.startsWith("//") ? value : "/dashboard";
}

export async function login(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  const next = safeNext(formData.get("next"));

  if (!email || !password) {
    return { error: "Bitte E-Mail und Passwort eingeben." };
  }

  try {
    const data = await apiFetch<TokenResponse>("/auth/token/", {
      method: "POST",
      body: { email, password },
      noAuth: true,
    });
    await setTokens(data.access, data.refresh);
  } catch (err) {
    if (err instanceof ApiError) {
      if (err.status === 401) {
        return { error: "E-Mail oder Passwort ist falsch." };
      }
      return { error: err.toUserMessage() };
    }
    return { error: "Das Backend ist nicht erreichbar. Bitte später erneut versuchen." };
  }

  redirect(next);
}

export async function logout() {
  await clearTokens();
  redirect("/login");
}

export async function requestPasswordReset(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const email = String(formData.get("email") ?? "").trim();
  if (!email) return { error: "Bitte E-Mail-Adresse eingeben." };

  try {
    await apiFetch("/auth/password/reset/", {
      method: "POST",
      body: { email },
      noAuth: true,
    });
  } catch (err) {
    if (err instanceof ApiError) return { error: err.toUserMessage() };
    return { error: "Das Backend ist nicht erreichbar." };
  }
  return {
    success:
      "Falls ein Konto existiert, wurde eine E-Mail mit weiteren Schritten versendet.",
  };
}

export async function confirmPasswordReset(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const uid = String(formData.get("uid") ?? "");
  const token = String(formData.get("token") ?? "");
  const newPassword = String(formData.get("new_password") ?? "");
  const confirm = String(formData.get("confirm_password") ?? "");

  if (!uid || !token) return { error: "Der Link ist ungültig oder unvollständig." };
  if (newPassword.length < 8)
    return { error: "Das Passwort muss mindestens 8 Zeichen lang sein." };
  if (newPassword !== confirm)
    return { error: "Die Passwörter stimmen nicht überein." };

  try {
    await apiFetch("/auth/password/reset/confirm/", {
      method: "POST",
      body: { uid, token, new_password: newPassword },
      noAuth: true,
    });
  } catch (err) {
    if (err instanceof ApiError) return { error: err.toUserMessage() };
    return { error: "Das Backend ist nicht erreichbar." };
  }
  return { success: "Passwort wurde gesetzt. Sie können sich jetzt anmelden." };
}
