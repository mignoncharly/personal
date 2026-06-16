"use client";

import { useActionState } from "react";

import type { ActionState } from "@/actions/organization";
import { updateOrganization } from "@/actions/organization";
import { SubmitButton } from "@/components/submit-button";
import { Alert, Checkbox, Field, Input } from "@/components/ui";
import type { OrganizationSettings } from "@/lib/types";

export function OrganizationForm({
  organization,
}: {
  organization: OrganizationSettings;
}) {
  const [state, formAction] = useActionState<ActionState, FormData>(
    updateOrganization,
    {},
  );

  return (
    <form action={formAction} className="space-y-8">
      {state.error && <Alert kind="error">{state.error}</Alert>}
      {state.success && (
        <Alert kind="success">Organisation gespeichert.</Alert>
      )}

      <section className="space-y-5">
        <h2 className="text-lg font-semibold">Firmenidentität</h2>
        <div className="grid gap-5 sm:grid-cols-2">
          <Field
            label="Anzeigename"
            htmlFor="name"
            hint="Erscheint in der Navigation."
          >
            <Input id="name" name="name" required defaultValue={organization.name} />
          </Field>
          <Field
            label="Firmenname (rechtlich)"
            htmlFor="legal_name"
            hint="Für den Rechnungskopf. Fällt auf den Anzeigenamen zurück, wenn leer."
          >
            <Input
              id="legal_name"
              name="legal_name"
              defaultValue={organization.legal_name}
            />
          </Field>
        </div>

        <Field label="Straße" htmlFor="street">
          <Input id="street" name="street" defaultValue={organization.street} />
        </Field>

        <div className="grid gap-5 sm:grid-cols-2">
          <Field label="PLZ" htmlFor="zip_code">
            <Input id="zip_code" name="zip_code" defaultValue={organization.zip_code} />
          </Field>
          <Field label="Ort" htmlFor="city">
            <Input id="city" name="city" defaultValue={organization.city} />
          </Field>
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <Field label="Telefon" htmlFor="phone">
            <Input id="phone" name="phone" defaultValue={organization.phone} />
          </Field>
          <Field label="E-Mail" htmlFor="email">
            <Input
              id="email"
              name="email"
              type="email"
              defaultValue={organization.email}
            />
          </Field>
        </div>
      </section>

      <section className="space-y-5">
        <h2 className="text-lg font-semibold">Steuer &amp; Bank</h2>
        <div className="grid gap-5 sm:grid-cols-2">
          <Field label="USt-IdNr." htmlFor="vat_id">
            <Input id="vat_id" name="vat_id" defaultValue={organization.vat_id} />
          </Field>
          <Field label="Steuernummer" htmlFor="tax_number">
            <Input
              id="tax_number"
              name="tax_number"
              defaultValue={organization.tax_number}
            />
          </Field>
        </div>

        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800/50">
          <Checkbox
            name="is_small_business"
            label="Kleinunternehmer nach § 19 UStG"
            defaultChecked={organization.is_small_business}
          />
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
            Wenn aktiviert, weisen neue Rechnungen keine Umsatzsteuer aus und
            tragen den gesetzlichen Hinweis nach § 19 UStG. Bereits erstellte
            Rechnungen bleiben unverändert.
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-3">
          <Field label="Bank" htmlFor="bank_name">
            <Input id="bank_name" name="bank_name" defaultValue={organization.bank_name} />
          </Field>
          <Field label="IBAN" htmlFor="iban">
            <Input id="iban" name="iban" defaultValue={organization.iban} />
          </Field>
          <Field label="BIC" htmlFor="bic">
            <Input id="bic" name="bic" defaultValue={organization.bic} />
          </Field>
        </div>
      </section>

      <section className="space-y-5">
        <h2 className="text-lg font-semibold">Rechnungsnummern</h2>
        <Field
          label="Präfix"
          htmlFor="invoice_number_prefix"
          hint="Vorangestellt vor die laufende Nummer, z. B. RECH-1-20260615."
        >
          <Input
            id="invoice_number_prefix"
            name="invoice_number_prefix"
            defaultValue={organization.invoice_number_prefix}
            className="sm:max-w-xs"
          />
        </Field>
        <p className="text-xs text-slate-400 dark:text-slate-500">
          Das Logo wird derzeit im Admin-Bereich gepflegt.
        </p>
      </section>

      <div className="flex gap-3">
        <SubmitButton pendingLabel="Speichern …">Änderungen speichern</SubmitButton>
      </div>
    </form>
  );
}
