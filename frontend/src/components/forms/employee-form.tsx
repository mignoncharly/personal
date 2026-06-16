"use client";

import { useActionState } from "react";
import Link from "next/link";

import type { ActionState } from "@/actions/employees";
import { SubmitButton } from "@/components/submit-button";
import { Alert, Checkbox, Field, Input, Select } from "@/components/ui";
import type { Employee } from "@/lib/types";

export function EmployeeForm({
  action,
  employee,
  submitLabel,
  cancelHref,
}: {
  action: (prev: ActionState, formData: FormData) => Promise<ActionState>;
  employee?: Employee;
  submitLabel: string;
  cancelHref: string;
}) {
  const [state, formAction] = useActionState<ActionState, FormData>(action, {});
  const isEdit = Boolean(employee);

  return (
    <form action={formAction} className="space-y-5">
      {employee && <input type="hidden" name="id" value={employee.id} />}
      {state.error && <Alert kind="error">{state.error}</Alert>}

      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="Vorname" htmlFor="first_name">
          <Input id="first_name" name="first_name" defaultValue={employee?.first_name ?? ""} />
        </Field>
        <Field label="Nachname" htmlFor="last_name">
          <Input id="last_name" name="last_name" defaultValue={employee?.last_name ?? ""} />
        </Field>
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="E-Mail (Login)" htmlFor="email">
          <Input id="email" name="email" type="email" required defaultValue={employee?.email ?? ""} />
        </Field>
        <Field label="Telefon" htmlFor="phone">
          <Input id="phone" name="phone" defaultValue={employee?.phone ?? ""} />
        </Field>
      </div>

      <Field
        label="Passwort"
        htmlFor="password"
        hint={
          isEdit
            ? "Leer lassen, um das Passwort unverändert zu lassen."
            : "Leer lassen: Mitarbeiter setzt das Passwort per „Passwort vergessen“."
        }
      >
        <Input id="password" name="password" type="password" autoComplete="new-password" />
      </Field>

      <Field label="Qualifikation" htmlFor="qualification">
        <Select
          id="qualification"
          name="qualification"
          defaultValue={employee?.qualification ?? "pflegehilfskraft"}
        >
          <option value="pflegehilfskraft">Pflegehilfskraft</option>
          <option value="pflegefachkraft">Pflegefachkraft</option>
        </Select>
      </Field>

      <Field label="Straße" htmlFor="street">
        <Input id="street" name="street" defaultValue={employee?.street ?? ""} />
      </Field>

      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="PLZ" htmlFor="zip_code">
          <Input id="zip_code" name="zip_code" defaultValue={employee?.zip_code ?? ""} />
        </Field>
        <Field label="Wohnort" htmlFor="city">
          <Input id="city" name="city" defaultValue={employee?.city ?? ""} />
        </Field>
      </div>

      <Checkbox
        name="is_active"
        label="Mitarbeiter aktiv"
        defaultChecked={employee ? employee.is_active : true}
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
