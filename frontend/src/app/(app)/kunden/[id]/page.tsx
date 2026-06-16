import { notFound } from "next/navigation";
import type { Metadata } from "next";

import { deleteCustomer, updateCustomer } from "@/actions/customers";
import { ConfirmButton } from "@/components/confirm-button";
import { ContractForm } from "@/components/forms/contract-form";
import { CustomerForm } from "@/components/forms/customer-form";
import {
  Alert,
  Badge,
  ButtonLink,
  Card,
  PageHeader,
} from "@/components/ui";
import { apiFetch, ApiError } from "@/lib/api";
import { requireAdmin } from "@/lib/dal";
import { formatDate, formatEuro, formatPercent } from "@/lib/format";
import type { Customer } from "@/lib/types";

export const metadata: Metadata = { title: "Kunde" };

const BL: Record<string, string> = { HE: "Hessen", RP: "Rheinland-Pfalz" };
const RHYTHM: Record<string, string> = {
  weekly: "Wöchentlich",
  monthly: "Monatlich",
  flexible: "Flexibel",
};

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4 py-2">
      <dt className="text-sm text-slate-500 dark:text-slate-400">{label}</dt>
      <dd className="text-right text-sm font-medium text-slate-900 dark:text-slate-100">
        {value}
      </dd>
    </div>
  );
}

export default async function CustomerDetailPage(props: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  await requireAdmin();
  const { id } = await props.params;
  const { edit, error } = await props.searchParams;
  const actionError = typeof error === "string" ? error : undefined;

  let customer: Customer;
  try {
    customer = await apiFetch<Customer>(`/customers/${id}/`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  if (edit === "1") {
    return (
      <>
        <PageHeader title="Kunde bearbeiten" subtitle={customer.name} />
        <Card className="max-w-3xl">
          <CustomerForm
            action={updateCustomer}
            customer={customer}
            submitLabel="Änderungen speichern"
            cancelHref={`/kunden/${customer.id}`}
          />
        </Card>
      </>
    );
  }

  const contract = customer.active_contract;

  return (
    <>
      <PageHeader
        title={customer.name}
        subtitle={[customer.city, BL[customer.bundesland]].filter(Boolean).join(" · ")}
        actions={
          <>
            <ButtonLink href="/kunden" variant="ghost">
              Zurück
            </ButtonLink>
            <ButtonLink href={`/kunden/${customer.id}?edit=1`} variant="secondary">
              Bearbeiten
            </ButtonLink>
          </>
        }
      />

      {actionError && (
        <div className="mb-4">
          <Alert kind="error">{actionError}</Alert>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Stammdaten</h2>
            {customer.is_active ? (
              <Badge color="green">aktiv</Badge>
            ) : (
              <Badge color="slate">inaktiv</Badge>
            )}
          </div>
          <dl className="divide-y divide-slate-100 dark:divide-slate-700/60">
            {customer.customer_number && (
              <Row label="Kundennummer" value={customer.customer_number} />
            )}
            {customer.contact_person && (
              <Row label="Ansprechpartner" value={customer.contact_person} />
            )}
            <Row
              label="Adresse"
              value={
                [
                  customer.street,
                  [customer.zip_code, customer.city].filter(Boolean).join(" "),
                ]
                  .filter(Boolean)
                  .join(", ") || "—"
              }
            />
            <Row label="Bundesland" value={BL[customer.bundesland] ?? customer.bundesland} />
            {customer.phone && <Row label="Telefon" value={customer.phone} />}
            {customer.email && <Row label="E-Mail" value={customer.email} />}
          </dl>

          <form action={deleteCustomer} className="mt-4 border-t border-slate-100 pt-4 dark:border-slate-700">
            <input type="hidden" name="id" value={customer.id} />
            <ConfirmButton message="Diesen Kunden wirklich löschen?">
              Kunde löschen
            </ConfirmButton>
          </form>
        </Card>

        <Card>
          <h2 className="mb-3 text-lg font-semibold">Aktueller Vertrag</h2>
          {contract ? (
            <dl className="divide-y divide-slate-100 dark:divide-slate-700/60">
              <Row label="Gültig ab" value={formatDate(contract.valid_from)} />
              <Row label="Stundensatz" value={formatEuro(contract.base_hourly_rate)} />
              <Row label="Nacht" value={formatPercent(contract.night_surcharge_pct)} />
              <Row label="Samstag" value={formatPercent(contract.saturday_surcharge_pct)} />
              <Row label="Sonntag" value={formatPercent(contract.sunday_surcharge_pct)} />
              <Row label="Feiertag" value={formatPercent(contract.holiday_surcharge_pct)} />
              <Row
                label="Nachtfenster"
                value={`${contract.night_start.slice(0, 5)}–${contract.night_end.slice(0, 5)}`}
              />
              <Row label="Rhythmus" value={RHYTHM[contract.invoice_rhythm] ?? contract.invoice_rhythm} />
              <Row label="Zahlungsziel" value={`${contract.payment_term_days} Tage`} />
              <Row label="USt" value={formatPercent(contract.vat_rate)} />
              {contract.travel_cost_rule && (
                <Row
                  label="Fahrkosten"
                  value={
                    contract.travel_cost_rule.enabled
                      ? `${formatEuro(contract.travel_cost_rule.rate_per_km)} / km${contract.travel_cost_rule.round_trip ? " (Hin & Rück)" : ""}`
                      : "deaktiviert"
                  }
                />
              )}
            </dl>
          ) : (
            <Alert kind="info">
              Noch kein aktiver Vertrag. Ohne Vertrag können Schichten dieses Kunden
              nicht berechnet oder abgerechnet werden.
            </Alert>
          )}

          {contract && contract.surcharge_rules.length > 0 && (
            <div className="mt-4">
              <h3 className="mb-1 text-sm font-medium text-slate-600 dark:text-slate-300">
                Spezialzuschläge
              </h3>
              <ul className="text-sm text-slate-600 dark:text-slate-300">
                {contract.surcharge_rules.map((r) => (
                  <li key={r.id}>
                    {r.label}: {formatPercent(r.percent)}
                    {!r.is_active && " (inaktiv)"}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      </div>

      <div className="mt-6">
        <h2 className="mb-3 text-lg font-semibold">
          {contract ? "Vertrag bearbeiten" : "Vertrag anlegen"}
        </h2>
        <Card className="max-w-3xl">
          <ContractForm customerId={customer.id} contract={contract} />
        </Card>
      </div>
    </>
  );
}
