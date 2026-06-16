import type { Metadata } from "next";
import Link from "next/link";

import { Badge, Card, EmptyState, PageHeader } from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { requireAdmin } from "@/lib/dal";
import { formatDate } from "@/lib/format";
import type { SystemStatus, SystemStatusItem } from "@/lib/types";

export const metadata: Metadata = { title: "Systemstatus" };

function StatusList({
  title,
  count,
  items,
  render,
}: {
  title: string;
  count: number;
  items: SystemStatusItem[];
  render: (item: SystemStatusItem) => React.ReactNode;
}) {
  return (
    <Card>
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-base font-semibold text-slate-950">{title}</h2>
        <Badge color={count > 0 ? "amber" : "green"}>{count}</Badge>
      </div>
      {count === 0 ? (
        <p className="mt-3 text-sm text-slate-500">Keine Auffälligkeiten.</p>
      ) : (
        <ul className="mt-3 divide-y divide-slate-100 text-sm">
          {items.map((item) => (
            <li key={`${title}-${item.id}-${item.date ?? ""}`} className="py-2">
              {render(item)}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

export default async function SystemStatusPage() {
  await requireAdmin();
  const status = await apiFetch<SystemStatus>("/system/status/");
  const quality = status.data_quality;
  const totalWarnings =
    quality.customers_without_contract_count +
    quality.customers_without_email_count +
    quality.employees_without_address_count +
    quality.approved_not_invoiced_count +
    quality.overdue_invoices_count;

  return (
    <>
      <PageHeader
        title="Systemstatus"
        subtitle="Betriebsstatus und einfache Stammdatenprüfungen für den Alltag."
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card>
          <div className="text-sm text-slate-500">Backend</div>
          <div className="mt-2"><Badge color={status.service.status === "ok" ? "green" : "red"}>{status.service.status}</Badge></div>
        </Card>
        <Card>
          <div className="text-sm text-slate-500">Datenbank</div>
          <div className="mt-2"><Badge color={status.service.database === "ok" ? "green" : "red"}>{status.service.database}</Badge></div>
        </Card>
        <Card>
          <div className="text-sm text-slate-500">Hinweise</div>
          <div className="mt-2 text-2xl font-bold text-slate-950">{totalWarnings}</div>
        </Card>
        <Card>
          <div className="text-sm text-slate-500">Fahrkosten aktiv</div>
          <div className="mt-2"><Badge color={quality.travel_costs_enabled ? "blue" : "slate"}>{quality.travel_costs_enabled ? "Ja" : "Nein"}</Badge></div>
        </Card>
      </div>

      {totalWarnings === 0 ? (
        <EmptyState>Alle Basisprüfungen sehen gut aus.</EmptyState>
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          <StatusList
            title="Kunden ohne aktiven Vertrag"
            count={quality.customers_without_contract_count}
            items={quality.customers_without_contract}
            render={(item) => <Link href={`/kunden/${item.id}`} className="font-semibold text-indigo-600 hover:underline">{item.name}</Link>}
          />
          <StatusList
            title="Kunden ohne Rechnungs-E-Mail"
            count={quality.customers_without_email_count}
            items={quality.customers_without_email}
            render={(item) => <Link href={`/kunden/${item.id}`} className="font-semibold text-indigo-600 hover:underline">{item.name}</Link>}
          />
          <StatusList
            title="Mitarbeiter ohne Adresse"
            count={quality.employees_without_address_count}
            items={quality.employees_without_address}
            render={(item) => <Link href={`/mitarbeiter/${item.id}`} className="font-semibold text-indigo-600 hover:underline">{item.name}</Link>}
          />
          <StatusList
            title="Freigegebene Schichten ohne Rechnung"
            count={quality.approved_not_invoiced_count}
            items={quality.approved_not_invoiced}
            render={(item) => (
              <Link href={`/schichten/${item.id}`} className="font-semibold text-indigo-600 hover:underline">
                {formatDate(item.date)} · {item.customer} · {item.employee}
              </Link>
            )}
          />
        </div>
      )}
    </>
  );
}
