import Link from "next/link";
import type { Metadata } from "next";

import { markInvoicePaid, remindInvoice, sendInvoice } from "@/actions/invoices";
import { SubmitButton } from "@/components/submit-button";
import {
  Badge,
  Button,
  ButtonLink,
  Card,
  EmptyState,
  Input,
  KpiCard,
  PageHeader,
  Pagination,
  Table,
  Td,
  Th,
} from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { requireAdmin } from "@/lib/dal";
import { formatDate, formatEuro } from "@/lib/format";
import type { Invoice, InvoiceSummary, Paginated } from "@/lib/types";

export const metadata: Metadata = { title: "Rechnungen" };

function InvoiceDashboardStatus({ invoice }: { invoice: Invoice }) {
  if (invoice.is_overdue) return <Badge color="red">Überfällig</Badge>;
  if (invoice.status === "paid") return <Badge color="green">Bezahlt</Badge>;
  if (invoice.status === "draft") return <Badge color="amber">Entwurf</Badge>;
  if (invoice.status === "cancelled") return <Badge color="red">Storniert</Badge>;
  return <Badge color="blue">Offen</Badge>;
}


const FILTERS = [
  { value: "", label: "Alle" },
  { value: "draft", label: "Entwurf" },
  { value: "open", label: "Offen" },
  { value: "overdue", label: "Überfällig" },
  { value: "paid", label: "Bezahlt" },
  { value: "cancelled", label: "Storniert" },
];

function sumInvoices(invoices: Invoice[], key: "total_gross" | "subtotal_net") {
  return invoices.reduce((sum, invoice) => sum + Number(invoice[key] || 0), 0);
}

export default async function InvoicesPage(props: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  await requireAdmin();
  const params = await props.searchParams;
  const q = typeof params.q === "string" ? params.q.trim() : "";
  const status = typeof params.status === "string" ? params.status : "";
  const page = Number(typeof params.page === "string" ? params.page : "1") || 1;
  const [data, summary, paidPage, totalsPage] = await Promise.all([
    apiFetch<Paginated<Invoice>>("/invoices/", { query: { page, q: q || undefined, status: status || undefined } }),
    apiFetch<InvoiceSummary>("/invoices/summary/"),
    apiFetch<Paginated<Invoice>>("/invoices/", { query: { status: "paid", page_size: 200 } }),
    apiFetch<Paginated<Invoice>>("/invoices/", { query: { page_size: 200 } }),
  ]);
  const invoices = data.results;
  const totalPages = Math.max(1, Math.ceil(data.count / 50));
  const paidTotal = sumInvoices(paidPage.results, "total_gross");
  const netTotal = sumInvoices(totalsPage.results, "subtotal_net");

  return (
    <>
      <PageHeader
        title="Rechnungen"
        subtitle="Forderungen, Fälligkeiten und Zahlungsstatus im Überblick."
        actions={
          <>
            {invoices.length > 0 && (
              <ButtonLink
                href={`/rechnungen/export?${new URLSearchParams({
                  ...(status ? { status } : {}),
                  ...(q ? { q } : {}),
                }).toString()}`}
                variant="secondary"
                download
              >
                Exportieren
              </ButtonLink>
            )}
            <ButtonLink href="/rechnungen/neu">Rechnung erstellen</ButtonLink>
          </>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Offene Forderungen"
          value={formatEuro(summary.open_total)}
          hint={`${summary.open_count} offene Rechnung(en)`}
          accent="indigo"
        />
        <KpiCard
          label="Überfällig"
          value={formatEuro(summary.overdue_total)}
          hint={`${summary.overdue_count} Rechnung(en)`}
          accent="rose"
        />
        <KpiCard
          label="Bezahlt"
          value={formatEuro(paidTotal)}
          hint={`${paidPage.count} bezahlte Rechnung(en)`}
          accent="emerald"
        />
        <KpiCard
          label="Netto-Summe"
          value={formatEuro(netTotal)}
          hint="aus den letzten 200 Rechnungen"
          accent="blue"
        />
      </div>

      <Card className="my-5">
        <form className="grid gap-3 lg:grid-cols-[1fr_auto]" action="/rechnungen">
          {status && <input type="hidden" name="status" value={status} />}
          <div>
            <label htmlFor="invoice-search" className="text-sm font-semibold text-slate-700">
              Suche
            </label>
            <Input
              id="invoice-search"
              name="q"
              defaultValue={q}
              placeholder="Rechnungsnummer, Kunde oder Status suchen"
              className="mt-2"
            />
          </div>
          <div className="flex items-end gap-2">
            <Button type="submit" variant="secondary">Suchen</Button>
            {(q || status) && <ButtonLink href="/rechnungen" variant="ghost">Zurücksetzen</ButtonLink>}
          </div>
        </form>
        <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-100 pt-4">
          {FILTERS.map((filter) => {
            const active = status === filter.value;
            const href = `/rechnungen${
              filter.value || q
                ? `?${new URLSearchParams({
                    ...(filter.value ? { status: filter.value } : {}),
                    ...(q ? { q } : {}),
                  }).toString()}`
                : ""
            }`;
            return (
              <Link
                key={filter.value || "all"}
                href={href}
                className={`rounded-full px-3 py-1.5 text-sm font-semibold transition-colors ring-1 ring-inset ${
                  active
                    ? "bg-indigo-600 text-white ring-indigo-600"
                    : "bg-white text-slate-600 ring-slate-200 hover:bg-slate-50"
                }`}
              >
                {filter.label}
              </Link>
            );
          })}
        </div>
      </Card>

      {invoices.length === 0 ? (
        <EmptyState>
          Noch keine Rechnungen erstellt. {" "}
          <Link href="/rechnungen/neu" className="font-semibold text-indigo-600 hover:underline">
            Rechnung erstellen
          </Link>
        </EmptyState>
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>Rechnungsnummer</Th>
              <Th>Kunde</Th>
              <Th>Datum</Th>
              <Th>Fällig am</Th>
              <Th className="text-right">Betrag</Th>
              <Th>Status</Th>
              <Th className="text-right">Aktionen</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {invoices.map((inv) => {
              const isOpen = inv.status === "finalized" || inv.status === "sent";
              return (
                <tr key={inv.id} className="hover:bg-slate-50">
                  <Td>
                    <Link href={`/rechnungen/${inv.id}`} className="font-semibold text-slate-950 hover:underline">
                      {inv.number}
                    </Link>
                  </Td>
                  <Td>{inv.customer_name}</Td>
                  <Td>{formatDate(inv.invoice_date)}</Td>
                  <Td>{formatDate(inv.due_date)}</Td>
                  <Td className="text-right font-semibold text-slate-950">
                    {formatEuro(inv.total_gross)}
                  </Td>
                  <Td>
                    <InvoiceDashboardStatus invoice={inv} />
                  </Td>
                  <Td className="text-right">
                    <div className="flex flex-wrap justify-end gap-2">
                      <ButtonLink href={`/rechnungen/${inv.id}`} variant="ghost" size="sm">
                        Details
                      </ButtonLink>

                      {inv.is_overdue && (
                        <form action={remindInvoice} className="inline">
                          <input type="hidden" name="id" value={inv.id} />
                          <input
                            type="hidden"
                            name="next"
                            value={`/rechnungen?${new URLSearchParams({
                              ...(status ? { status } : {}),
                              ...(q ? { q } : {}),
                              page: String(page),
                            }).toString()}`}
                          />
                          <SubmitButton variant="secondary" size="sm" pendingLabel="Sendet ...">
                            Mahnung senden
                          </SubmitButton>
                        </form>
                      )}
                      {isOpen && (
                        <form action={sendInvoice} className="inline">
                          <input type="hidden" name="id" value={inv.id} />
                          <SubmitButton variant="secondary" size="sm" pendingLabel="Sendet ...">
                            {inv.status === "sent" ? "Erneut senden" : "Versenden"}
                          </SubmitButton>
                        </form>
                      )}
                      {isOpen && (
                        <form action={markInvoicePaid} className="inline">
                          <input type="hidden" name="id" value={inv.id} />
                          <SubmitButton variant="secondary" size="sm" pendingLabel="...">
                            Bezahlt
                          </SubmitButton>
                        </form>
                      )}
                    </div>
                  </Td>
                </tr>
              );
            })}
          </tbody>
        </Table>
      )}

      <Pagination
        page={page}
        totalPages={totalPages}
        count={data.count}
        makeHref={(p) =>
          `/rechnungen?${new URLSearchParams({
            ...(status ? { status } : {}),
            ...(q ? { q } : {}),
            page: String(p),
          }).toString()}`
        }
      />
    </>
  );
}
