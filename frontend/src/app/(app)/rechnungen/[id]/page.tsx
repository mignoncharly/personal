import { notFound } from "next/navigation";
import type { Metadata } from "next";

import {
  cancelInvoice,
  deleteInvoice,
  finalizeInvoice,
  markInvoicePaid,
  markInvoiceUnpaid,
  remindInvoice,
  sendInvoice,
} from "@/actions/invoices";
import { ConfirmButton } from "@/components/confirm-button";
import { SubmitButton } from "@/components/submit-button";
import { InvoiceStatusBadge } from "@/components/status";
import {
  Alert,
  ButtonLink,
  Card,
  PageHeader,
  Table,
  Td,
  Th,
} from "@/components/ui";
import { apiFetch, ApiError } from "@/lib/api";
import { requireAdmin } from "@/lib/dal";
import {
  formatDate,
  formatDateTime,
  formatEuro,
  formatHours,
  formatPercent,
} from "@/lib/format";
import type { Invoice } from "@/lib/types";

export const metadata: Metadata = { title: "Rechnung" };

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

export default async function InvoiceDetailPage(props: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  await requireAdmin();
  const { id } = await props.params;
  const { error, sent, reminded } = await props.searchParams;
  const actionError = typeof error === "string" ? error : undefined;
  const justSent = sent === "1";
  const justReminded = reminded === "1";

  let invoice: Invoice;
  try {
    invoice = await apiFetch<Invoice>(`/invoices/${id}/`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  const isDraft = invoice.status === "draft";
  const isSent = invoice.status === "sent";
  const isPaid = invoice.status === "paid";
  const isCancelled = invoice.status === "cancelled";
  // Offen = festgeschrieben oder versendet (versendbar + als bezahlt markierbar).
  const isOpen = invoice.status === "finalized" || isSent;
  const canSend = isOpen;
  const canMarkPaid = isOpen;
  // Storno: alles außer Entwurf (wird gelöscht) und bereits storniert.
  const canCancel = !isDraft && !isCancelled;

  return (
    <>
      <PageHeader
        title={invoice.number}
        subtitle={`${invoice.customer_name} · ${formatDate(invoice.period_start)} – ${formatDate(invoice.period_end)}`}
        actions={
          <>
            <ButtonLink href="/rechnungen" variant="ghost">
              Zurück
            </ButtonLink>
            <a
              href={`/rechnungen/${invoice.id}/pdf?inline=1`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
            >
              PDF anzeigen
            </a>
          </>
        }
      />

      {actionError && (
        <div className="mb-4">
          <Alert kind="error">{actionError}</Alert>
        </div>
      )}
      {justSent && !actionError && (
        <div className="mb-4">
          <Alert kind="success">Die Rechnung wurde per E-Mail versendet.</Alert>
        </div>
      )}
      {justReminded && !actionError && (
        <div className="mb-4">
          <Alert kind="success">Die Zahlungserinnerung wurde versendet.</Alert>
        </div>
      )}
      {invoice.is_overdue && (
        <div className="mb-4">
          <Alert kind="error">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span>
                Diese Rechnung ist seit {formatDate(invoice.due_date)} überfällig und
                noch nicht als bezahlt markiert.
                {invoice.last_reminded_at && (
                  <>
                    {" "}Zuletzt gemahnt am {formatDateTime(invoice.last_reminded_at)}.
                  </>
                )}
              </span>
              <form action={remindInvoice}>
                <input type="hidden" name="id" value={invoice.id} />
                <SubmitButton
                  variant="secondary"
                  className="px-3 py-1 text-xs"
                  pendingLabel="Sendet …"
                >
                  Zahlungserinnerung senden
                </SubmitButton>
              </form>
            </div>
          </Alert>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Eckdaten</h2>
            <InvoiceStatusBadge status={invoice.status} label={invoice.status_display} />
          </div>
          <dl className="divide-y divide-slate-100 dark:divide-slate-700/60">
            <Row label="Kunde" value={invoice.customer_name} />
            <Row label="Rechnungsdatum" value={formatDate(invoice.invoice_date)} />
            <Row label="Fällig am" value={formatDate(invoice.due_date)} />
            <Row label="Zahlungsziel" value={`${invoice.payment_term_days} Tage`} />
            <Row label="Schichten" value={invoice.shift_count} />
            {invoice.sent_at && (
              <Row label="Versendet am" value={formatDateTime(invoice.sent_at)} />
            )}
            {invoice.paid_at && (
              <Row label="Bezahlt am" value={formatDateTime(invoice.paid_at)} />
            )}
          </dl>
        </Card>

        <Card className="lg:col-span-2">
          <h2 className="mb-3 text-lg font-semibold">Aktionen</h2>
          <div className="flex flex-wrap items-start gap-3">
            <a
              href={`/rechnungen/${invoice.id}/pdf`}
              className="inline-flex items-center rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              PDF herunterladen
            </a>

            {isDraft && (
              <form action={finalizeInvoice}>
                <input type="hidden" name="id" value={invoice.id} />
                <SubmitButton pendingLabel="Wird festgeschrieben …">
                  Festschreiben
                </SubmitButton>
              </form>
            )}

            {canSend && (
              <form action={sendInvoice}>
                <input type="hidden" name="id" value={invoice.id} />
                <SubmitButton pendingLabel="Wird versendet …">
                  {isSent ? "Erneut per E-Mail versenden" : "Per E-Mail versenden"}
                </SubmitButton>
              </form>
            )}

            {canMarkPaid && (
              <form action={markInvoicePaid}>
                <input type="hidden" name="id" value={invoice.id} />
                <SubmitButton variant="secondary" pendingLabel="Wird markiert …">
                  Als bezahlt markieren
                </SubmitButton>
              </form>
            )}

            {isPaid && (
              <form action={markInvoiceUnpaid}>
                <input type="hidden" name="id" value={invoice.id} />
                <SubmitButton variant="secondary" pendingLabel="Wird zurückgesetzt …">
                  Als unbezahlt markieren
                </SubmitButton>
              </form>
            )}

            {canCancel && (
              <form action={cancelInvoice}>
                <input type="hidden" name="id" value={invoice.id} />
                <ConfirmButton message="Diese Rechnung wirklich stornieren? Die Nummer bleibt erhalten, die Schichten werden wieder freigegeben.">
                  Stornieren
                </ConfirmButton>
              </form>
            )}

            {isDraft && (
              <form action={deleteInvoice}>
                <input type="hidden" name="id" value={invoice.id} />
                <ConfirmButton message="Diese Rechnung wirklich löschen? Die Schichten werden wieder freigegeben.">
                  Rechnung löschen
                </ConfirmButton>
              </form>
            )}
          </div>
          {isCancelled && (
            <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
              Diese Rechnung wurde storniert. Die Schichten wurden wieder freigegeben
              und können neu abgerechnet werden.
            </p>
          )}
          {isDraft && (
            <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
              Vor dem Versand muss die Rechnung festgeschrieben werden.
            </p>
          )}
          {(isOpen || isPaid) && (
            <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
              Festgeschriebene Rechnungen können nicht gelöscht werden (nur
              stornieren). Der Versand geht an die beim Kunden hinterlegte
              E-Mail-Adresse.
            </p>
          )}
        </Card>
      </div>

      <div className="mt-6">
        <h2 className="mb-3 text-lg font-semibold">Positionen</h2>
        <Table>
          <thead>
            <tr>
              <Th>Nr.</Th>
              <Th>Bezeichnung</Th>
              <Th className="text-right">Bezahlt (Std.)</Th>
              <Th className="text-right">Faktor (€)</Th>
              <Th className="text-right">Betrag</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {invoice.lines.map((line) => (
              <tr key={line.id}>
                <Td>{line.position}</Td>
                <Td>{line.description}</Td>
                <Td className="text-right">
                  {line.quantity_hours ? formatHours(line.quantity_hours) : "–"}
                </Td>
                <Td className="text-right">
                  {line.factor ? formatEuro(line.factor) : "–"}
                </Td>
                <Td className="text-right">{formatEuro(line.amount)}</Td>
              </tr>
            ))}
          </tbody>
          <tfoot className="divide-y divide-slate-200 dark:divide-slate-700">
            <tr>
              <Td className="text-right" />
              <Td />
              <Td />
              <Td className="text-right font-medium">Zwischensumme</Td>
              <Td className="text-right font-medium">{formatEuro(invoice.subtotal_net)}</Td>
            </tr>
            <tr>
              <Td className="text-right" />
              <Td />
              <Td />
              <Td className="text-right font-medium">
                USt ({formatPercent(invoice.vat_rate)})
              </Td>
              <Td className="text-right font-medium">{formatEuro(invoice.vat_amount)}</Td>
            </tr>
            <tr className="bg-slate-50 dark:bg-slate-800">
              <Td className="text-right" />
              <Td />
              <Td />
              <Td className="text-right text-base font-bold">Gesamt brutto</Td>
              <Td className="text-right text-base font-bold">
                {formatEuro(invoice.total_gross)}
              </Td>
            </tr>
          </tfoot>
        </Table>
      </div>
    </>
  );
}
