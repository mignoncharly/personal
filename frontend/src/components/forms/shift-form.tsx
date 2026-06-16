"use client";

import { useActionState } from "react";
import Link from "next/link";

import type { ActionState } from "@/actions/shifts";
import { SubmitButton } from "@/components/submit-button";
import { Alert, Field, Input, Select, Textarea } from "@/components/ui";
import type { CustomerChoice, Employee, Shift } from "@/lib/types";

const SHIFT_TYPES = [
  { value: "frueh", label: "Frühdienst" },
  { value: "spaet", label: "Spätdienst" },
  { value: "nacht", label: "Nachtdienst" },
];

interface ShiftFormProps {
  action: (prev: ActionState, formData: FormData) => Promise<ActionState>;
  customers: CustomerChoice[];
  employees?: Employee[];
  shift?: Shift;
  submitLabel: string;
  cancelHref: string;
}

export function ShiftForm({
  action,
  customers,
  employees,
  shift,
  submitLabel,
  cancelHref,
}: ShiftFormProps) {
  const [state, formAction] = useActionState<ActionState, FormData>(action, {});

  return (
    <form action={formAction} className="space-y-5">
      {shift && <input type="hidden" name="id" value={shift.id} />}
      {state.error && <Alert kind="error">{state.error}</Alert>}

      {employees && (
        <Field label="Mitarbeiter" htmlFor="employee" hint="Leer lassen für sich selbst.">
          <Select
            id="employee"
            name="employee"
            defaultValue={shift?.employee ?? ""}
          >
            <option value="">— Eigene Schicht —</option>
            {employees.map((e) => (
              <option key={e.user_id} value={e.user_id}>
                {e.full_name || e.email}
              </option>
            ))}
          </Select>
        </Field>
      )}

      <Field label="Kunde / Einrichtung" htmlFor="customer">
        <Select id="customer" name="customer" required defaultValue={shift?.customer ?? ""}>
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
        <Field label="Schichtart" htmlFor="shift_type">
          <Select
            id="shift_type"
            name="shift_type"
            required
            defaultValue={shift?.shift_type ?? ""}
          >
            <option value="" disabled>
              Bitte wählen …
            </option>
            {SHIFT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="Datum" htmlFor="date">
          <Input id="date" name="date" type="date" required defaultValue={shift?.date ?? ""} />
        </Field>
      </div>

      <div className="grid gap-5 sm:grid-cols-3">
        <Field label="Startzeit" htmlFor="start_time">
          <Input
            id="start_time"
            name="start_time"
            type="time"
            required
            defaultValue={shift?.start_time?.slice(0, 5) ?? ""}
          />
        </Field>
        <Field label="Endzeit" htmlFor="end_time" hint="Über Mitternacht erlaubt.">
          <Input
            id="end_time"
            name="end_time"
            type="time"
            required
            defaultValue={shift?.end_time?.slice(0, 5) ?? ""}
          />
        </Field>
        <Field label="Pause (Minuten)" htmlFor="break_minutes">
          <Input
            id="break_minutes"
            name="break_minutes"
            type="number"
            min={0}
            step={5}
            defaultValue={shift?.break_minutes ?? 0}
          />
        </Field>
      </div>

      <Field label="Bemerkung" htmlFor="note">
        <Textarea id="note" name="note" rows={3} defaultValue={shift?.note ?? ""} />
      </Field>

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
