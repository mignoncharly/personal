"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { apiFetch, ApiError } from "@/lib/api";
import type { Invoice, InvoicePreview } from "@/lib/types";

export interface ActionState {
  error?: string;
  preview?: InvoicePreview;
  values?: {
    customer?: string;
    period_start?: string;
    period_end?: string;
    invoice_date?: string;
  };
}

function str(value: FormDataEntryValue | null): string {
  return typeof value === "string" ? value.trim() : "";
}

export async function generateInvoice(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const customer = str(formData.get("customer"));
  const periodStart = str(formData.get("period_start"));
  const periodEnd = str(formData.get("period_end"));
  const invoiceDate = str(formData.get("invoice_date"));
  const intent = str(formData.get("intent"));
  const values = {
    customer,
    period_start: periodStart,
    period_end: periodEnd,
    invoice_date: invoiceDate,
  };

  if (!customer) return { error: "Bitte einen Kunden wählen.", values };
  if (!periodStart || !periodEnd)
    return { error: "Bitte den Leistungszeitraum angeben.", values };

  if (intent === "preview") {
    try {
      const preview = await apiFetch<InvoicePreview>("/invoices/preview/", {
        query: {
          customer: Number(customer),
          period_start: periodStart,
          period_end: periodEnd,
          ...(invoiceDate ? { invoice_date: invoiceDate } : {}),
        },
      });
      return { preview, values };
    } catch (err) {
      if (err instanceof ApiError) return { error: err.toUserMessage(), values };
      return { error: "Vorschau konnte nicht berechnet werden.", values };
    }
  }

  let invoice: Invoice;
  try {
    invoice = await apiFetch<Invoice>("/invoices/generate/", {
      method: "POST",
      body: {
        customer: Number(customer),
        period_start: periodStart,
        period_end: periodEnd,
        ...(invoiceDate ? { invoice_date: invoiceDate } : {}),
      },
    });
  } catch (err) {
    if (err instanceof ApiError) return { error: err.toUserMessage(), values };
    return { error: "Rechnung konnte nicht erstellt werden.", values };
  }
  revalidatePath("/rechnungen");
  redirect(`/rechnungen/${invoice.id}`);
}

export async function finalizeInvoice(formData: FormData) {
  const id = str(formData.get("id"));
  if (!id) return;
  try {
    await apiFetch(`/invoices/${id}/finalize/`, { method: "POST" });
  } catch (err) {
    const msg = err instanceof ApiError ? err.toUserMessage() : "Rechnung konnte nicht festgeschrieben werden.";
    redirect(`/rechnungen/${id}?error=${encodeURIComponent(msg)}`);
  }
  revalidatePath("/rechnungen");
  revalidatePath(`/rechnungen/${id}`);
}

export async function sendInvoice(formData: FormData) {
  const id = str(formData.get("id"));
  if (!id) return;
  try {
    await apiFetch(`/invoices/${id}/send/`, { method: "POST" });
  } catch (err) {
    const msg = err instanceof ApiError ? err.toUserMessage() : "Rechnung konnte nicht versendet werden.";
    redirect(`/rechnungen/${id}?error=${encodeURIComponent(msg)}`);
  }
  revalidatePath("/rechnungen");
  redirect(`/rechnungen/${id}?sent=1`);
}

export async function markInvoicePaid(formData: FormData) {
  const id = str(formData.get("id"));
  if (!id) return;
  try {
    await apiFetch(`/invoices/${id}/mark_paid/`, { method: "POST" });
  } catch (err) {
    const msg = err instanceof ApiError ? err.toUserMessage() : "Rechnung konnte nicht als bezahlt markiert werden.";
    redirect(`/rechnungen/${id}?error=${encodeURIComponent(msg)}`);
  }
  revalidatePath("/rechnungen");
  revalidatePath("/dashboard");
  revalidatePath(`/rechnungen/${id}`);
}

export async function markInvoiceUnpaid(formData: FormData) {
  const id = str(formData.get("id"));
  if (!id) return;
  try {
    await apiFetch(`/invoices/${id}/mark_unpaid/`, { method: "POST" });
  } catch (err) {
    const msg = err instanceof ApiError ? err.toUserMessage() : "Zahlungsmarkierung konnte nicht zurückgenommen werden.";
    redirect(`/rechnungen/${id}?error=${encodeURIComponent(msg)}`);
  }
  revalidatePath("/rechnungen");
  revalidatePath("/dashboard");
  revalidatePath(`/rechnungen/${id}`);
}

export async function remindInvoice(formData: FormData) {
  const id = str(formData.get("id"));
  const next = str(formData.get("next"));
  if (!id) return;
  try {
    await apiFetch(`/invoices/${id}/remind/`, { method: "POST" });
  } catch (err) {
    const msg = err instanceof ApiError ? err.toUserMessage() : "Zahlungserinnerung konnte nicht versendet werden.";
    redirect(`/rechnungen/${id}?error=${encodeURIComponent(msg)}`);
  }
  revalidatePath("/rechnungen");
  revalidatePath("/dashboard");
  revalidatePath(`/rechnungen/${id}`);
  if (next.startsWith("/rechnungen")) redirect(next);
  redirect(`/rechnungen/${id}?reminded=1`);
}

export async function cancelInvoice(formData: FormData) {
  const id = str(formData.get("id"));
  if (!id) return;
  try {
    await apiFetch(`/invoices/${id}/cancel/`, { method: "POST" });
  } catch (err) {
    const msg = err instanceof ApiError ? err.toUserMessage() : "Rechnung konnte nicht storniert werden.";
    redirect(`/rechnungen/${id}?error=${encodeURIComponent(msg)}`);
  }
  revalidatePath("/rechnungen");
  revalidatePath("/dashboard");
  redirect(`/rechnungen/${id}`);
}

export async function deleteInvoice(formData: FormData) {
  const id = str(formData.get("id"));
  if (!id) return;
  try {
    await apiFetch(`/invoices/${id}/`, { method: "DELETE" });
  } catch (err) {
    const msg = err instanceof ApiError ? err.toUserMessage() : "Rechnung konnte nicht gelöscht werden.";
    redirect(`/rechnungen/${id}?error=${encodeURIComponent(msg)}`);
  }
  revalidatePath("/rechnungen");
  redirect("/rechnungen");
}
