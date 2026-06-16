import type { Metadata } from "next";

import {
  Button,
  ButtonLink,
  Card,
  EmptyState,
  Input,
  KpiCard,
  PageHeader,
  Table,
  Td,
  Th,
} from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { requireAdmin } from "@/lib/dal";
import { formatEuro, formatHours } from "@/lib/format";
import type { Report } from "@/lib/types";

export const metadata: Metadata = { title: "Auswertungen" };

const MONTHS = [
  "Januar", "Februar", "März", "April", "Mai", "Juni",
  "Juli", "August", "September", "Oktober", "November", "Dezember",
];

function monthLabel(value: string): string {
  const [year, month] = value.split("-");
  const idx = Number(month) - 1;
  return `${MONTHS[idx] ?? month} ${year}`;
}

export default async function ReportsPage(props: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  await requireAdmin();
  const params = await props.searchParams;
  const from = typeof params.from === "string" ? params.from : "";
  const to = typeof params.to === "string" ? params.to : "";

  const report = await apiFetch<Report>("/reports/", {
    query: { from: from || undefined, to: to || undefined },
  });

  const exportQuery = new URLSearchParams({
    ...(report.from ? { from: report.from } : {}),
    ...(report.to ? { to: report.to } : {}),
  }).toString();

  return (
    <>
      <PageHeader
        title="Auswertungen"
        subtitle="Umsatz, Forderungen und geleistete Stunden im gewählten Zeitraum."
        actions={
          report.by_customer.length > 0 ? (
            <ButtonLink
              href={`/auswertungen/export?${exportQuery}`}
              variant="secondary"
              download
            >
              Umsatz je Kunde (CSV)
            </ButtonLink>
          ) : undefined
        }
      />

      <Card className="mb-5">
        <form className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]" action="/auswertungen">
          <div>
            <label htmlFor="from" className="text-sm font-semibold text-slate-700">
              Von
            </label>
            <Input id="from" name="from" type="date" defaultValue={report.from} className="mt-2" />
          </div>
          <div>
            <label htmlFor="to" className="text-sm font-semibold text-slate-700">
              Bis
            </label>
            <Input id="to" name="to" type="date" defaultValue={report.to} className="mt-2" />
          </div>
          <div className="flex items-end">
            <Button type="submit" variant="secondary">Anzeigen</Button>
          </div>
        </form>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Umsatz (brutto)" value={formatEuro(report.totals.gross)} accent="emerald" />
        <KpiCard
          label="Umsatz (netto)"
          value={formatEuro(report.totals.net)}
          hint={`${report.totals.count} Rechnung(en)`}
          accent="blue"
        />
        <KpiCard
          label="Offene Forderungen"
          value={formatEuro(report.receivables.open_total)}
          hint={`${report.receivables.open_count} offen`}
          accent="indigo"
        />
        <KpiCard
          label="Überfällig"
          value={formatEuro(report.receivables.overdue_total)}
          hint={`${report.receivables.overdue_count} überfällig`}
          accent="rose"
        />
      </div>

      <section className="mt-8">
        <h2 className="mb-3 text-base font-semibold text-slate-950">Umsatz je Monat</h2>
        {report.by_month.length === 0 ? (
          <EmptyState>Keine Rechnungen im gewählten Zeitraum.</EmptyState>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Monat</Th>
                <Th className="text-right">Rechnungen</Th>
                <Th className="text-right">Netto</Th>
                <Th className="text-right">Brutto</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {report.by_month.map((row) => (
                <tr key={row.month} className="hover:bg-slate-50">
                  <Td>{monthLabel(row.month)}</Td>
                  <Td className="text-right">{row.count}</Td>
                  <Td className="text-right">{formatEuro(row.net)}</Td>
                  <Td className="text-right font-semibold text-slate-950">{formatEuro(row.gross)}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </section>

      <section className="mt-8">
        <h2 className="mb-3 text-base font-semibold text-slate-950">Umsatz je Kunde</h2>
        {report.by_customer.length === 0 ? (
          <EmptyState>Keine Rechnungen im gewählten Zeitraum.</EmptyState>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Kunde</Th>
                <Th className="text-right">Rechnungen</Th>
                <Th className="text-right">Netto</Th>
                <Th className="text-right">Brutto</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {report.by_customer.map((row) => (
                <tr key={row.customer} className="hover:bg-slate-50">
                  <Td>{row.customer}</Td>
                  <Td className="text-right">{row.count}</Td>
                  <Td className="text-right">{formatEuro(row.net)}</Td>
                  <Td className="text-right font-semibold text-slate-950">{formatEuro(row.gross)}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </section>

      <section className="mt-8">
        <h2 className="mb-3 text-base font-semibold text-slate-950">Stunden je Mitarbeiter</h2>
        {report.by_employee.length === 0 ? (
          <EmptyState>Keine freigegebenen Schichten im gewählten Zeitraum.</EmptyState>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Mitarbeiter</Th>
                <Th className="text-right">Schichten</Th>
                <Th className="text-right">Bezahlte Stunden</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {report.by_employee.map((row) => (
                <tr key={row.employee} className="hover:bg-slate-50">
                  <Td>{row.employee}</Td>
                  <Td className="text-right">{row.shifts}</Td>
                  <Td className="text-right font-semibold text-slate-950">{formatHours(row.hours)}</Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </section>
    </>
  );
}
