"use client";

import { useActionState } from "react";
import Link from "next/link";

import { generateInvoice, type ActionState } from "@/actions/invoices";
import { Alert, Button, Card, Field, Input, Select } from "@/components/ui";
import { formatEuro, formatHours } from "@/lib/format";
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
  const values = state.values ?? {};

  return (
    <form action={formAction} className="space-y-5">
      {state.error && <Alert kind="error">{state.error}</Alert>}

      <Field
        label="Kunde"
        htmlFor="customer"
        hint="Es werden alle freigegebenen, noch nicht abgerechneten Schichten im Zeitraum berücksichtigt."
      >
        <Select id="customer" name="customer" required defaultValue={values.customer ?? ""}>
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
          <Input id="period_start" name="period_start" type="date" required defaultValue={values.period_start ?? ""} />
        </Field>
        <Field label="Zeitraum bis" htmlFor="period_end">
          <Input id="period_end" name="period_end" type="date" required defaultValue={values.period_end ?? ""} />
        </Field>
      </div>

      <Field label="Rechnungsdatum" htmlFor="invoice_date">
        <Input id="invoice_date" name="invoice_date" type="date" defaultValue={values.invoice_date ?? today} />
      </Field>

      {state.preview && (
        <Card className="border-indigo-100 bg-indigo-50/40 shadow-none">
          <div className="text-sm font-semibold text-slate-950">Rechnungsvorschau</div>
          <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-slate-500">Kunde</dt>
              <dd className="font-semibold text-slate-950">{state.preview.customer_name}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Abrechenbare Schichten</dt>
              <dd className="font-semibold text-slate-950">{state.preview.shift_count}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Bezahlte Stunden</dt>
              <dd className="font-semibold text-slate-950">{formatHours(state.preview.paid_hours)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Netto</dt>
              <dd className="font-semibold text-slate-950">{formatEuro(state.preview.subtotal_net)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">USt</dt>
              <dd className="font-semibold text-slate-950">{formatEuro(state.preview.vat_amount)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Brutto</dt>
              <dd className="font-semibold text-slate-950">{formatEuro(state.preview.total_gross)}</dd>
            </div>
          </dl>
          {state.preview.shift_count === 0 && (
            <p className="mt-3 text-sm text-amber-700">
              Für diesen Zeitraum gibt es keine freigegebenen, noch nicht abgerechneten Schichten.
            </p>
          )}
        </Card>
      )}

      <div className="flex flex-wrap gap-3">
        <Button type="submit" name="intent" value="preview" variant="secondary">
          Vorschau prüfen
        </Button>
        <Button type="submit" name="intent" value="create" disabled={state.preview?.shift_count === 0}>
          Rechnung erstellen
        </Button>
        <Link
          href="/rechnungen"
          className="inline-flex items-center rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          Abbrechen
        </Link>
      </div>
    </form>
  );
}
