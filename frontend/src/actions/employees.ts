"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { apiFetch, ApiError } from "@/lib/api";
import type { Employee } from "@/lib/types";

export interface ActionState {
  error?: string;
}

function str(value: FormDataEntryValue | null): string {
  return typeof value === "string" ? value.trim() : "";
}

function payload(formData: FormData, includeEmptyPassword: boolean) {
  const data: Record<string, unknown> = {
    email: str(formData.get("email")),
    first_name: str(formData.get("first_name")),
    last_name: str(formData.get("last_name")),
    phone: str(formData.get("phone")),
    qualification: str(formData.get("qualification")),
    street: str(formData.get("street")),
    zip_code: str(formData.get("zip_code")),
    city: str(formData.get("city")),
    is_active: formData.get("is_active") === "on",
  };
  const password = str(formData.get("password"));
  // Beim Bearbeiten nur senden, wenn gesetzt (sonst bleibt das Passwort unverändert).
  if (password || includeEmptyPassword) {
    if (password) data.password = password;
  }
  return data;
}

export async function createEmployee(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  let created: Employee;
  try {
    created = await apiFetch<Employee>("/employees/", {
      method: "POST",
      body: payload(formData, true),
    });
  } catch (err) {
    if (err instanceof ApiError) return { error: err.toUserMessage() };
    return { error: "Mitarbeiter konnte nicht gespeichert werden." };
  }
  revalidatePath("/mitarbeiter");
  redirect(`/mitarbeiter/${created.id}`);
}

export async function updateEmployee(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const id = str(formData.get("id"));
  if (!id) return { error: "Ungültiger Mitarbeiter." };
  try {
    await apiFetch<Employee>(`/employees/${id}/`, {
      method: "PATCH",
      body: payload(formData, false),
    });
  } catch (err) {
    if (err instanceof ApiError) return { error: err.toUserMessage() };
    return { error: "Änderungen konnten nicht gespeichert werden." };
  }
  revalidatePath("/mitarbeiter");
  revalidatePath(`/mitarbeiter/${id}`);
  redirect(`/mitarbeiter/${id}`);
}

export async function deleteEmployee(formData: FormData) {
  const id = str(formData.get("id"));
  if (!id) return;
  try {
    await apiFetch(`/employees/${id}/`, { method: "DELETE" });
  } catch (err) {
    const msg =
      err instanceof ApiError
        ? err.toUserMessage()
        : "Mitarbeiter konnte nicht gelöscht werden.";
    redirect(`/mitarbeiter/${id}?error=${encodeURIComponent(msg)}`);
  }
  revalidatePath("/mitarbeiter");
  redirect("/mitarbeiter");
}
