"use client";

import { useActionState } from "react";

import { saveContract, type ActionState } from "@/actions/customers";
import { SubmitButton } from "@/components/submit-button";
import { Alert, Checkbox, Field, Input, Select } from "@/components/ui";
import type { CustomerContract } from "@/lib/types";

export function ContractForm({
  customerId,
  contract,
}: {
  customerId: number;
  contract?: CustomerContract | null;
}) {
  const [state, formAction] = useActionState<ActionState, FormData>(
    saveContract,
    {},
  );
  const today = new Date().toISOString().slice(0, 10);

  return (
    <form action={formAction} className="space-y-5">
      <input type="hidden" name="customer" value={customerId} />
      {contract && <input type="hidden" name="contract_id" value={contract.id} />}
      {state.error && <Alert kind="error">{state.error}</Alert>}

      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="Gültig ab" htmlFor="valid_from">
          <Input
            id="valid_from"
            name="valid_from"
            type="date"
            required
            defaultValue={contract?.valid_from ?? today}
          />
        </Field>
        <Field label="Kundenstundensatz (€)" htmlFor="base_hourly_rate">
          <Input
            id="base_hourly_rate"
            name="base_hourly_rate"
            type="number"
            step="0.01"
            min="0"
            required
            defaultValue={contract?.base_hourly_rate ?? ""}
          />
        </Field>
      </div>

      <fieldset className="rounded-lg border border-slate-200 p-4 dark:border-slate-700">
        <legend className="px-1 text-sm font-medium text-slate-600 dark:text-slate-300">
          Standard-Zuschläge (%)
        </legend>
        <div className="grid gap-5 sm:grid-cols-4">
          <Field label="Nacht" htmlFor="night_surcharge_pct">
            <Input
              id="night_surcharge_pct"
              name="night_surcharge_pct"
              type="number"
              step="0.01"
              defaultValue={contract?.night_surcharge_pct ?? "25"}
            />
          </Field>
          <Field label="Samstag" htmlFor="saturday_surcharge_pct">
            <Input
              id="saturday_surcharge_pct"
              name="saturday_surcharge_pct"
              type="number"
              step="0.01"
              defaultValue={contract?.saturday_surcharge_pct ?? "25"}
            />
          </Field>
          <Field label="Sonntag" htmlFor="sunday_surcharge_pct">
            <Input
              id="sunday_surcharge_pct"
              name="sunday_surcharge_pct"
              type="number"
              step="0.01"
              defaultValue={contract?.sunday_surcharge_pct ?? "50"}
            />
          </Field>
          <Field label="Feiertag" htmlFor="holiday_surcharge_pct">
            <Input
              id="holiday_surcharge_pct"
              name="holiday_surcharge_pct"
              type="number"
              step="0.01"
              defaultValue={contract?.holiday_surcharge_pct ?? "100"}
            />
          </Field>
        </div>
      </fieldset>

      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="Nacht beginnt" htmlFor="night_start">
          <Input
            id="night_start"
            name="night_start"
            type="time"
            defaultValue={contract?.night_start?.slice(0, 5) ?? "20:00"}
          />
        </Field>
        <Field label="Nacht endet" htmlFor="night_end">
          <Input
            id="night_end"
            name="night_end"
            type="time"
            defaultValue={contract?.night_end?.slice(0, 5) ?? "06:00"}
          />
        </Field>
      </div>

      <div className="grid gap-5 sm:grid-cols-3">
        <Field label="Rechnungsrhythmus" htmlFor="invoice_rhythm">
          <Select
            id="invoice_rhythm"
            name="invoice_rhythm"
            defaultValue={contract?.invoice_rhythm ?? "monthly"}
          >
            <option value="weekly">Wöchentlich</option>
            <option value="monthly">Monatlich</option>
            <option value="flexible">Flexibel</option>
          </Select>
        </Field>
        <Field label="Zahlungsziel (Tage)" htmlFor="payment_term_days">
          <Input
            id="payment_term_days"
            name="payment_term_days"
            type="number"
            min="0"
            defaultValue={contract?.payment_term_days ?? 14}
          />
        </Field>
        <Field label="USt-Satz (%)" htmlFor="vat_rate">
          <Input
            id="vat_rate"
            name="vat_rate"
            type="number"
            step="0.01"
            defaultValue={contract?.vat_rate ?? "19"}
          />
        </Field>
      </div>

      <div className="flex flex-col gap-3">
        <Checkbox
          name="cumulative_surcharges"
          label="Zuschläge kumulieren (mehrere gleichzeitig auf dieselbe Stunde)"
          defaultChecked={contract ? contract.cumulative_surcharges : true}
        />
        <Checkbox
          name="is_active"
          label="Vertrag aktiv"
          defaultChecked={contract ? contract.is_active : true}
        />
      </div>

      <SubmitButton pendingLabel="Speichern …">
        {contract ? "Vertrag aktualisieren" : "Vertrag anlegen"}
      </SubmitButton>
    </form>
  );
}
