"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { apiFetch, ApiError } from "@/lib/api";
import type { Shift } from "@/lib/types";

export interface ActionState {
  error?: string;
}

function num(value: FormDataEntryValue | null): number | undefined {
  const s = typeof value === "string" ? value.trim() : "";
  if (s === "") return undefined;
  const n = Number(s);
  return Number.isNaN(n) ? undefined : n;
}

function str(value: FormDataEntryValue | null): string {
  return typeof value === "string" ? value.trim() : "";
}

function buildPayload(formData: FormData) {
  const payload: Record<string, unknown> = {
    customer: num(formData.get("customer")),
    shift_type: str(formData.get("shift_type")),
    date: str(formData.get("date")),
    start_time: str(formData.get("start_time")),
    end_time: str(formData.get("end_time")),
    break_minutes: num(formData.get("break_minutes")) ?? 0,
    note: str(formData.get("note")),
  };
  const employee = num(formData.get("employee"));
  if (employee !== undefined) payload.employee = employee;
  return payload;
}

function refreshShiftPaths(id?: number) {
  revalidatePath("/schichten");
  revalidatePath("/dashboard");
  if (id) revalidatePath(`/schichten/${id}`);
}

export async function createShift(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  let created: Shift;
  try {
    created = await apiFetch<Shift>("/shifts/", {
      method: "POST",
      body: buildPayload(formData),
    });
    if (str(formData.get("intent")) === "submit") {
      await apiFetch(`/shifts/${created.id}/submit/`, { method: "POST" });
    }
  } catch (err) {
    if (err instanceof ApiError) return { error: err.toUserMessage() };
    return { error: "Schicht konnte nicht gespeichert werden." };
  }
  refreshShiftPaths(created.id);
  redirect(`/schichten/${created.id}`);
}

export async function updateShift(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const id = num(formData.get("id"));
  if (!id) return { error: "Ungültige Schicht." };
  try {
    await apiFetch<Shift>(`/shifts/${id}/`, {
      method: "PATCH",
      body: buildPayload(formData),
    });
    if (str(formData.get("intent")) === "submit") {
      await apiFetch(`/shifts/${id}/submit/`, { method: "POST" });
    }
  } catch (err) {
    if (err instanceof ApiError) return { error: err.toUserMessage() };
    return { error: "Änderungen konnten nicht gespeichert werden." };
  }
  refreshShiftPaths(id);
  redirect(`/schichten/${id}`);
}

/** Einfacher Statuswechsel per Action-Button (submit/approve/calculate).
 *
 * Bei einem Fehler (z. B. fehlender Vertrag → 400) wird zurück auf die
 * Schicht-Seite mit Fehlermeldung umgeleitet, statt die Seite abstürzen zu
 * lassen ("A server error occurred").
 */
async function shiftAction(formData: FormData, verb: string) {
  const id = num(formData.get("id"));
  if (!id) return;
  try {
    await apiFetch(`/shifts/${id}/${verb}/`, { method: "POST" });
  } catch (err) {
    const msg = err instanceof ApiError ? err.toUserMessage() : "Aktion fehlgeschlagen.";
    redirect(`/schichten/${id}?error=${encodeURIComponent(msg)}`);
  }
  refreshShiftPaths(id);
}

export async function submitShift(formData: FormData) {
  await shiftAction(formData, "submit");
}

export async function approveShift(formData: FormData) {
  await shiftAction(formData, "approve");
}

export async function calculateShift(formData: FormData) {
  await shiftAction(formData, "calculate");
}

export async function rejectShift(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const id = num(formData.get("id"));
  const reason = str(formData.get("reason"));
  if (!id) return { error: "Ungültige Schicht." };
  if (!reason) return { error: "Bitte einen Ablehnungsgrund angeben." };
  try {
    await apiFetch(`/shifts/${id}/reject/`, {
      method: "POST",
      body: { reason },
    });
  } catch (err) {
    if (err instanceof ApiError) return { error: err.toUserMessage() };
    return { error: "Schicht konnte nicht abgelehnt werden." };
  }
  refreshShiftPaths(id);
  return {};
}

export async function deleteShift(formData: FormData) {
  const id = num(formData.get("id"));
  if (!id) return;
  try {
    await apiFetch(`/shifts/${id}/`, { method: "DELETE" });
  } catch (err) {
    const msg = err instanceof ApiError ? err.toUserMessage() : "Schicht konnte nicht gelöscht werden.";
    redirect(`/schichten/${id}?error=${encodeURIComponent(msg)}`);
  }
  refreshShiftPaths();
  redirect("/schichten");
}
