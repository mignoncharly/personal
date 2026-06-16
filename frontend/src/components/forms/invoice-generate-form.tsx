"use client";

import { useActionState } from "react";
import Link from "next/link";

import { generateInvoice, type ActionState } from "@/actions/invoices";
import { SubmitButton } from "@/components/submit-button";
import { Alert, Field, Input, Select } from "@/components/ui";
import type { CustomerChoice } from "@/lib/types";

export function InvoiceGenerateForm({
  customers,
}: {
  customers: CustomerChoice[];
}) {
  const [state, formAction] = useActionState<ActionState, FormData>(
    generateInvoice,
    {},
  );
  const today = new Date().toISOString().slice(0, 10);

  return (
    <form action={formAction} className="space-y-5">
      {state.error && <Alert kind="error">{state.error}</Alert>}

      <Field
        label="Kunde"
        htmlFor="customer"
        hint="Es werden alle freigegebenen, noch nicht abgerechneten Schichten im Zeitraum berücksichtigt."
      >
        <Select id="customer" name="customer" required defaultValue="">
          <option value="" disabled>
            Bitte wählen …
          </option>
          {customers.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
              {c.city ? ` (${c.city})` : ""}
            </option>
          ))}
        </Select>
      </Field>

      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="Zeitraum von" htmlFor="period_start">
          <Input id="period_start" name="period_start" type="date" required />
        </Field>
        <Field label="Zeitraum bis" htmlFor="period_end">
          <Input id="period_end" name="period_end" type="date" required />
        </Field>
      </div>

      <Field label="Rechnungsdatum" htmlFor="invoice_date">
        <Input id="invoice_date" name="invoice_date" type="date" defaultValue={today} />
      </Field>

      <div className="flex gap-3">
        <SubmitButton pendingLabel="Wird erstellt …">Rechnung erstellen</SubmitButton>
        <Link
          href="/rechnungen"
          className="inline-flex items-center rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          Abbrechen
        </Link>
      </div>
    </form>
  );
}
