"use client";

import { useActionState } from "react";
import Link from "next/link";

import type { ActionState } from "@/actions/customers";
import { SubmitButton } from "@/components/submit-button";
import { Alert, Checkbox, Field, Input, Select } from "@/components/ui";
import type { Customer } from "@/lib/types";

export function CustomerForm({
  action,
  customer,
  submitLabel,
  cancelHref,
}: {
  action: (prev: ActionState, formData: FormData) => Promise<ActionState>;
  customer?: Customer;
  submitLabel: string;
  cancelHref: string;
}) {
  const [state, formAction] = useActionState<ActionState, FormData>(action, {});

  return (
    <form action={formAction} className="space-y-5">
      {customer && <input type="hidden" name="id" value={customer.id} />}
      {state.error && <Alert kind="error">{state.error}</Alert>}

      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="Name / Einrichtung" htmlFor="name">
          <Input id="name" name="name" required defaultValue={customer?.name ?? ""} />
        </Field>
        <Field label="Kundennummer" htmlFor="customer_number">
          <Input
            id="customer_number"
            name="customer_number"
            defaultValue={customer?.customer_number ?? ""}
          />
        </Field>
      </div>

      <Field label="Ansprechpartner" htmlFor="contact_person">
        <Input
          id="contact_person"
          name="contact_person"
          defaultValue={customer?.contact_person ?? ""}
        />
      </Field>

      <Field label="Straße" htmlFor="street">
        <Input id="street" name="street" defaultValue={customer?.street ?? ""} />
      </Field>

      <div className="grid gap-5 sm:grid-cols-3">
        <Field label="PLZ" htmlFor="zip_code">
          <Input id="zip_code" name="zip_code" defaultValue={customer?.zip_code ?? ""} />
        </Field>
        <Field label="Ort" htmlFor="city">
          <Input id="city" name="city" defaultValue={customer?.city ?? ""} />
        </Field>
        <Field label="Bundesland" htmlFor="bundesland" hint="Steuert die Feiertage.">
          <Select
            id="bundesland"
            name="bundesland"
            required
            defaultValue={customer?.bundesland ?? ""}
          >
            <option value="" disabled>
              Bitte wählen …
            </option>
            <option value="HE">Hessen</option>
            <option value="RP">Rheinland-Pfalz</option>
          </Select>
        </Field>
      </div>

      <div className="grid gap-5 sm:grid-cols-3">
        <Field label="Telefon" htmlFor="phone">
          <Input id="phone" name="phone" defaultValue={customer?.phone ?? ""} />
        </Field>
        <Field label="Fax" htmlFor="fax">
          <Input id="fax" name="fax" defaultValue={customer?.fax ?? ""} />
        </Field>
        <Field label="E-Mail" htmlFor="email">
          <Input id="email" name="email" type="email" defaultValue={customer?.email ?? ""} />
        </Field>
      </div>

      <Checkbox
        name="is_active"
        label="Kunde aktiv"
        defaultChecked={customer ? customer.is_active : true}
      />

      <div className="flex gap-3">
        <SubmitButton pendingLabel="Speichern …">{submitLabel}</SubmitButton>
        <Link
          href={cancelHref}
          className="inline-flex items-center rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          Abbrechen
        </Link>
      </div>
    </form>
  );
}
