import Link from "next/link";
import type { Metadata } from "next";

import { InvoiceStatusBadge, ShiftStatusBadge } from "@/components/status";
import {
  ButtonLink,
  Card,
  EmptyState,
  KpiCard,
  PageHeader,
} from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { requireUser } from "@/lib/dal";
import { formatDate, formatEuro, formatHours } from "@/lib/format";
import type {
  Invoice,
  InvoiceSummary,
  Paginated,
  Shift,
  ShiftSummary,
} from "@/lib/types";

export const metadata: Metadata = { title: "Dashboard" };

function SectionTitle({
  title,
  href,
}: {
  title: string;
  href?: string;
}) {
  return (
    <div className="mb-3 flex items-center justify-between gap-3">
      <h2 className="text-base font-semibold text-slate-950">{title}</h2>
      {href && (
        <Link href={href} className="text-sm font-semibold text-indigo-600 hover:underline">
          Alle anzeigen
        </Link>
      )}
    </div>
  );
}

export default async function DashboardPage() {
  const user = await requireUser();

  if (user.is_admin) {
    const [summary, reviewPage, invoices, recentInvoicePage] = await Promise.all([
      apiFetch<ShiftSummary>("/shifts/summary/"),
      apiFetch<Paginated<Shift>>("/shifts/", {
        query: { status: "submitted", page_size: 8 },
      }),
      apiFetch<InvoiceSummary>("/invoices/summary/"),
      apiFetch<Paginated<Invoice>>("/invoices/", { query: { page_size: 5 } }),
    ]);
    const review = reviewPage.results;
    const recentInvoices = recentInvoicePage.results;

    return (
      <>
        <PageHeader
          title={`Willkommen, ${user.first_name || user.full_name || "Admin"}`}
          subtitle="Übersicht über Schichten, Prüfungen und offene Forderungen."
          actions={<ButtonLink href="/rechnungen/neu">Rechnung erstellen</ButtonLink>}
        />

        <section>
          <SectionTitle title="Übersicht" />
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard label="Schichten gesamt" value={summary.anzahl_schichten} accent="indigo" />
            <KpiCard
              label="Wartet auf Prüfung"
              value={summary.status_counts.submitted ?? 0}
              hint="eingereichte Schichten"
              accent="amber"
            />
            <KpiCard
              label="Zahlbare Stunden"
              value={formatHours(summary.zahlbare_stunden)}
              accent="blue"
            />
            <KpiCard
              label="Netto-Summe"
              value={formatEuro(summary.netto_summe)}
              hint="berechnete Schichten"
              accent="emerald"
            />
          </div>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard
              label="Offene Forderungen"
              value={formatEuro(invoices.open_total)}
              hint={`${invoices.open_count} offene Rechnung(en)`}
              accent="indigo"
            />
            <KpiCard
              label="Überfällig"
              value={formatEuro(invoices.overdue_total)}
              hint={`${invoices.overdue_count} überfällig`}
              accent="rose"
            />
            <Card className="sm:col-span-2">
              <div className="text-sm font-medium text-slate-500">Schnellaktionen</div>
              <div className="mt-4 flex flex-wrap gap-2">
                <ButtonLink href="/rechnungen/neu">Rechnung erstellen</ButtonLink>
                <ButtonLink href="/schichten/neu" variant="secondary">
                  Schicht erstellen
                </ButtonLink>
                <ButtonLink href="/kunden/neu" variant="secondary">
                  Kunde anlegen
                </ButtonLink>
              </div>
            </Card>
          </div>
        </section>

        <div className="mt-8 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <section>
            <SectionTitle title="Wartet auf Prüfung" href="/schichten?status=submitted" />
            {review.length === 0 ? (
              <EmptyState>Keine eingereichten Schichten zur Prüfung.</EmptyState>
            ) : (
              <Card className="p-0">
                <ul className="divide-y divide-slate-200">
                  {review.map((shift) => (
                    <li key={shift.id}>
                      <Link
                        href={`/schichten/${shift.id}`}
                        className="flex flex-col gap-3 px-4 py-4 transition-colors hover:bg-slate-50 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div className="min-w-0">
                          <div className="font-semibold text-slate-950">{shift.employee_name}</div>
                          <div className="mt-1 text-sm text-slate-500">
                            {shift.customer_name} · {formatDate(shift.date)} · {shift.shift_type_display}
                          </div>
                        </div>
                        <ShiftStatusBadge status={shift.status} label={shift.status_display} />
                      </Link>
                    </li>
                  ))}
                </ul>
              </Card>
            )}
          </section>

          <section>
            <SectionTitle title="Letzte Rechnungen" href="/rechnungen" />
            {recentInvoices.length === 0 ? (
              <EmptyState>Noch keine Rechnungen erstellt.</EmptyState>
            ) : (
              <Card className="p-0">
                <ul className="divide-y divide-slate-200">
                  {recentInvoices.map((invoice) => (
                    <li key={invoice.id}>
                      <Link
                        href={`/rechnungen/${invoice.id}`}
                        className="block px-4 py-4 transition-colors hover:bg-slate-50"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div className="min-w-0">
                            <div className="truncate font-semibold text-slate-950">{invoice.number}</div>
                            <div className="mt-1 truncate text-sm text-slate-500">{invoice.customer_name}</div>
                          </div>
                          <div className="text-right text-sm font-semibold text-slate-950">
                            {formatEuro(invoice.total_gross)}
                          </div>
                        </div>
                        <div className="mt-3 flex items-center justify-between gap-2">
                          <span className="text-xs text-slate-500">Fällig {formatDate(invoice.due_date)}</span>
                          <InvoiceStatusBadge status={invoice.status} label={invoice.status_display} />
                        </div>
                      </Link>
                    </li>
                  ))}
                </ul>
              </Card>
            )}
          </section>
        </div>
      </>
    );
  }

  const [summary, recentPage] = await Promise.all([
    apiFetch<ShiftSummary>("/shifts/summary/"),
    apiFetch<Paginated<Shift>>("/shifts/", { query: { page_size: 8 } }),
  ]);
  const counts = summary.status_counts;
  const recent = recentPage.results;

  return (
    <>
      <PageHeader
        title={`Hallo, ${user.first_name || user.full_name || ""}`.trim()}
        subtitle="Ihre Schichten und Einreichungen auf einen Blick."
        actions={<ButtonLink href="/schichten/neu">Schicht erfassen</ButtonLink>}
      />

      <section>
        <SectionTitle title="Übersicht" />
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <KpiCard label="Entwürfe" value={counts.draft ?? 0} accent="slate" />
          <KpiCard label="Eingereicht" value={counts.submitted ?? 0} accent="amber" />
          <KpiCard label="Freigegeben" value={counts.approved ?? 0} accent="emerald" />
          <KpiCard label="Abgelehnt" value={counts.rejected ?? 0} accent="rose" />
        </div>
      </section>

      <section className="mt-8">
        <SectionTitle title="Letzte Schichten" href="/schichten" />
        {recent.length === 0 ? (
          <EmptyState>
            Noch keine Schichten erfasst. {" "}
            <Link href="/schichten/neu" className="font-semibold text-indigo-600 hover:underline">
              Jetzt die erste Schicht anlegen.
            </Link>
          </EmptyState>
        ) : (
          <Card className="p-0">
            <ul className="divide-y divide-slate-200">
              {recent.map((shift) => (
                <li key={shift.id}>
                  <Link
                    href={`/schichten/${shift.id}`}
                    className="flex flex-col gap-3 px-4 py-4 transition-colors hover:bg-slate-50 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="min-w-0">
                      <div className="font-semibold text-slate-950">{shift.customer_name}</div>
                      <div className="mt-1 text-sm text-slate-500">
                        {formatDate(shift.date)} · {shift.shift_type_display}
                      </div>
                    </div>
                    <ShiftStatusBadge status={shift.status} label={shift.status_display} />
                  </Link>
                </li>
              ))}
            </ul>
          </Card>
        )}
      </section>
    </>
  );
}
