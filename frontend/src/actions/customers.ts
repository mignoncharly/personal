"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { apiFetch, ApiError } from "@/lib/api";
import type { Customer, CustomerContract } from "@/lib/types";

export interface ActionState {
  error?: string;
}

function str(value: FormDataEntryValue | null): string {
  return typeof value === "string" ? value.trim() : "";
}

function bool(formData: FormData, name: string): boolean {
  return formData.get(name) === "on";
}

function customerPayload(formData: FormData) {
  return {
    name: str(formData.get("name")),
    customer_number: str(formData.get("customer_number")),
    contact_person: str(formData.get("contact_person")),
    street: str(formData.get("street")),
    zip_code: str(formData.get("zip_code")),
    city: str(formData.get("city")),
    bundesland: str(formData.get("bundesland")),
    phone: str(formData.get("phone")),
    fax: str(formData.get("fax")),
    email: str(formData.get("email")),
    is_active: bool(formData, "is_active"),
  };
}

export async function createCustomer(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  let created: Customer;
  try {
    created = await apiFetch<Customer>("/customers/", {
      method: "POST",
      body: customerPayload(formData),
    });
  } catch (err) {
    if (err instanceof ApiError) return { error: err.toUserMessage() };
    return { error: "Kunde konnte nicht gespeichert werden." };
  }
  revalidatePath("/kunden");
  redirect(`/kunden/${created.id}`);
}

export async function updateCustomer(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const id = str(formData.get("id"));
  if (!id) return { error: "Ungültiger Kunde." };
  try {
    await apiFetch<Customer>(`/customers/${id}/`, {
      method: "PATCH",
      body: customerPayload(formData),
    });
  } catch (err) {
    if (err instanceof ApiError) return { error: err.toUserMessage() };
    return { error: "Änderungen konnten nicht gespeichert werden." };
  }
  revalidatePath("/kunden");
  revalidatePath(`/kunden/${id}`);
  redirect(`/kunden/${id}`);
}

export async function deleteCustomer(formData: FormData) {
  const id = str(formData.get("id"));
  if (!id) return;
  try {
    await apiFetch(`/customers/${id}/`, { method: "DELETE" });
  } catch (err) {
    const msg =
      err instanceof ApiError
        ? err.toUserMessage()
        : "Kunde konnte nicht gelöscht werden.";
    redirect(`/kunden/${id}?error=${encodeURIComponent(msg)}`);
  }
  revalidatePath("/kunden");
  redirect("/kunden");
}

function contractPayload(formData: FormData) {
  return {
    customer: Number(str(formData.get("customer"))),
    valid_from: str(formData.get("valid_from")),
    is_active: bool(formData, "is_active"),
    base_hourly_rate: str(formData.get("base_hourly_rate")),
    night_surcharge_pct: str(formData.get("night_surcharge_pct")),
    saturday_surcharge_pct: str(formData.get("saturday_surcharge_pct")),
    sunday_surcharge_pct: str(formData.get("sunday_surcharge_pct")),
    holiday_surcharge_pct: str(formData.get("holiday_surcharge_pct")),
    cumulative_surcharges: bool(formData, "cumulative_surcharges"),
    night_start: str(formData.get("night_start")),
    night_end: str(formData.get("night_end")),
    invoice_rhythm: str(formData.get("invoice_rhythm")),
    payment_term_days: Number(str(formData.get("payment_term_days")) || "14"),
    vat_rate: str(formData.get("vat_rate")),
  };
}

export async function saveContract(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const contractId = str(formData.get("contract_id"));
  const customerId = str(formData.get("customer"));
  try {
    if (contractId) {
      await apiFetch<CustomerContract>(`/contracts/${contractId}/`, {
        method: "PATCH",
        body: contractPayload(formData),
      });
    } else {
      await apiFetch<CustomerContract>("/contracts/", {
        method: "POST",
        body: contractPayload(formData),
      });
    }
  } catch (err) {
    if (err instanceof ApiError) return { error: err.toUserMessage() };
    return { error: "Vertrag konnte nicht gespeichert werden." };
  }
  revalidatePath(`/kunden/${customerId}`);
  redirect(`/kunden/${customerId}`);
}
