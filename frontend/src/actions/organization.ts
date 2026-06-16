"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, ApiError } from "@/lib/api";
import type { OrganizationSettings } from "@/lib/types";

export interface ActionState {
  error?: string;
  success?: boolean;
}

function str(value: FormDataEntryValue | null): string {
  return typeof value === "string" ? value.trim() : "";
}

function organizationPayload(formData: FormData) {
  return {
    name: str(formData.get("name")),
    legal_name: str(formData.get("legal_name")),
    street: str(formData.get("street")),
    zip_code: str(formData.get("zip_code")),
    city: str(formData.get("city")),
    phone: str(formData.get("phone")),
    email: str(formData.get("email")),
    vat_id: str(formData.get("vat_id")),
    tax_number: str(formData.get("tax_number")),
    is_small_business: formData.get("is_small_business") === "on",
    bank_name: str(formData.get("bank_name")),
    iban: str(formData.get("iban")),
    bic: str(formData.get("bic")),
    invoice_number_prefix: str(formData.get("invoice_number_prefix")),
  };
}

export async function updateOrganization(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  try {
    await apiFetch<OrganizationSettings>("/organization/", {
      method: "PATCH",
      body: organizationPayload(formData),
    });
  } catch (err) {
    if (err instanceof ApiError) return { error: err.toUserMessage() };
    return { error: "Organisation konnte nicht gespeichert werden." };
  }
  // Der Firmenname erscheint in der Navigation (über /auth/me/) und im
  // Rechnungsbriefkopf – das ganze App-Layout neu validieren.
  revalidatePath("/", "layout");
  return { success: true };
}
