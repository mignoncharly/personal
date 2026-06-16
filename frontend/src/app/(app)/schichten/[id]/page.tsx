import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";

import {
  approveShift,
  calculateShift,
  deleteShift,
  submitShift,
  updateShift,
} from "@/actions/shifts";
import { ConfirmButton } from "@/components/confirm-button";
import { RejectShiftForm } from "@/components/forms/reject-shift-form";
import { ShiftForm } from "@/components/forms/shift-form";
import { ShiftStatusBadge } from "@/components/status";
import {
  Alert,
  ButtonLink,
  Card,
  PageHeader,
  Table,
  Td,
  Th,
} from "@/components/ui";
import { SubmitButton } from "@/components/submit-button";
import { apiFetch, ApiError } from "@/lib/api";
import { requireUser } from "@/lib/dal";
import {
  formatDate,
  formatDateTime,
  formatEuro,
  formatHours,
  formatTime,
} from "@/lib/format";
import type {
  Customer,
  CustomerChoice,
  Employee,
  Shift,
  ShiftCalculation,
} from "@/lib/types";

export const metadata: Metadata = { title: "Schicht" };

const EDITABLE = new Set(["draft", "rejected"]);

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

function CalculationTable({ calc }: { calc: ShiftCalculation }) {
  const rows: { label: string; hours?: string; amount: string }[] = [
    { label: "Grundstunden", hours: calc.paid_hours, amount: calc.base_amount },
    { label: "Nachtzuschlag", hours: calc.night_hours, amount: calc.night_amount },
    { label: "Samstagzuschlag", hours: calc.saturday_hours, amount: calc.saturday_amount },
    { label: "Sonntagszuschlag", hours: calc.sunday_hours, amount: calc.sunday_amount },
    { label: "Feiertagszuschlag", hours: calc.holiday_hours, amount: calc.holiday_amount },
    { label: "Spezialzuschläge", amount: calc.special_amount },
    { label: "Fahrkosten", amount: calc.travel_amount },
  ];
  const visible = rows.filter((r) => Number(r.amount) !== 0 || r.label === "Grundstunden");

  return (
    <Table>
      <thead>
        <tr>
          <Th>Position</Th>
          <Th className="text-right">Stunden</Th>
          <Th className="text-right">Betrag</Th>
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
        {visible.map((r) => (
          <tr key={r.label}>
            <Td>{r.label}</Td>
            <Td className="text-right">{r.hours ? formatHours(r.hours) : "–"}</Td>
            <Td className="text-right">{formatEuro(r.amount)}</Td>
          </tr>
        ))}
        <tr className="bg-slate-50 font-semibold dark:bg-slate-800">
          <Td>Netto gesamt</Td>
          <Td className="text-right">{formatHours(calc.paid_hours)}</Td>
          <Td className="text-right">{formatEuro(calc.net_total)}</Td>
        </tr>
      </tbody>
    </Table>
  );
}

export default async function ShiftDetailPage(props: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const user = await requireUser();
  const { id } = await props.params;
  const { edit, error } = await props.searchParams;
  const editing = edit === "1";
  const actionError = typeof error === "string" ? error : undefined;

  let shift: Shift;
  try {
    shift = await apiFetch<Shift>(`/shifts/${id}/`);
  } catch (err) {
    if (err instanceof ApiError && (err.status === 404 || err.status === 403)) {
      notFound();
    }
    throw err;
  }

  const isOwner = shift.employee === user.id;
  const isEditable = EDITABLE.has(shift.status);
  const canEdit = user.is_admin || (isOwner && isEditable);
  const canSubmit = (user.is_admin || isOwner) && isEditable;
  const canReview = user.is_admin && shift.status === "submitted";
  const canRecalculate = user.is_admin && shift.status === "approved";

  // Freigabe/Berechnung scheitern ohne aktiven Vertrag des Kunden. Nur für Admins
  // und nur in den relevanten Status den Kunden laden, um die Schichtliste nicht
  // mit N+1-Abfragen zu belasten.
  let customerNeedsContract = false;
  if (canReview || canRecalculate) {
    try {
      const customer = await apiFetch<Customer>(`/customers/${shift.customer}/`);
      customerNeedsContract = !customer.active_contract;
    } catch {
      // Hinweis ist best effort – bei Fehler einfach nicht anzeigen.
    }
  }

  // Bearbeitungsmodus
  if (editing && canEdit) {
    const customers = await apiFetch<CustomerChoice[]>("/customer-choices/");
    const employees = user.is_admin
      ? await apiFetch<Employee[]>("/employees/", { query: { is_active: "true" } })
      : undefined;
    return (
      <>
        <PageHeader title="Schicht bearbeiten" subtitle={`${shift.customer_name} · ${formatDate(shift.date)}`} />
        <Card className="max-w-2xl">
          <ShiftForm
            action={updateShift}
            customers={customers}
            employees={employees}
            shift={shift}
            submitLabel="Änderungen speichern"
            cancelHref={`/schichten/${shift.id}`}
          />
        </Card>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title={shift.customer_name}
        subtitle={`${formatDate(shift.date)} · ${shift.shift_type_display}`}
        actions={
          <>
            <ButtonLink href="/schichten" variant="ghost">
              Zurück
            </ButtonLink>
            {canEdit && (
              <ButtonLink href={`/schichten/${shift.id}?edit=1`} variant="secondary">
                Bearbeiten
              </ButtonLink>
            )}
          </>
        }
      />

      {actionError && (
        <div className="mb-4">
          <Alert kind="error">{actionError}</Alert>
        </div>
      )}

      {shift.status === "rejected" && shift.correction_reason && (
        <div className="mb-4">
          <Alert kind="error">
            <strong>Abgelehnt:</strong> {shift.correction_reason}
          </Alert>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Schichtdaten</h2>
            <ShiftStatusBadge status={shift.status} label={shift.status_display} />
          </div>
          <dl className="divide-y divide-slate-100 dark:divide-slate-700/60">
            {user.is_admin && <Row label="Mitarbeiter" value={shift.employee_name || "—"} />}
            <Row label="Kunde" value={shift.customer_name} />
            <Row label="Schichtart" value={shift.shift_type_display} />
            <Row label="Datum" value={formatDate(shift.date)} />
            <Row
              label="Zeit"
              value={`${formatTime(shift.start_time)} – ${formatTime(shift.end_time)}`}
            />
            <Row label="Pause" value={`${shift.break_minutes} Min.`} />
            {shift.note && <Row label="Bemerkung" value={shift.note} />}
            {shift.submitted_at && (
              <Row label="Eingereicht am" value={formatDateTime(shift.submitted_at)} />
            )}
            {shift.reviewed_at && (
              <Row label="Geprüft am" value={formatDateTime(shift.reviewed_at)} />
            )}
          </dl>
        </Card>

        <Card>
          <h2 className="mb-3 text-lg font-semibold">Aktionen</h2>
          <div className="space-y-3">
            {customerNeedsContract && (
              <Alert kind="info">
                Für{" "}
                <Link
                  href={`/kunden/${shift.customer}`}
                  className="font-medium underline underline-offset-2"
                >
                  {shift.customer_name}
                </Link>{" "}
                ist kein aktiver Vertrag hinterlegt. Ohne Vertrag kann diese Schicht
                nicht freigegeben oder berechnet werden – bitte zuerst einen Vertrag
                anlegen.
              </Alert>
            )}

            {canSubmit && (
              <form action={submitShift}>
                <input type="hidden" name="id" value={shift.id} />
                <SubmitButton className="w-full" pendingLabel="Wird eingereicht …">
                  Zur Prüfung einreichen
                </SubmitButton>
              </form>
            )}

            {canReview && (
              <>
                <form action={approveShift}>
                  <input type="hidden" name="id" value={shift.id} />
                  <SubmitButton className="w-full" pendingLabel="Wird freigegeben …">
                    Freigeben &amp; berechnen
                  </SubmitButton>
                </form>
                <div className="border-t border-slate-100 pt-3 dark:border-slate-700">
                  <RejectShiftForm shiftId={shift.id} />
                </div>
              </>
            )}

            {canRecalculate && (
              <form action={calculateShift}>
                <input type="hidden" name="id" value={shift.id} />
                <SubmitButton
                  className="w-full"
                  variant="secondary"
                  pendingLabel="Wird berechnet …"
                >
                  Neu berechnen
                </SubmitButton>
              </form>
            )}

            {canEdit && (
              <form action={deleteShift} className="border-t border-slate-100 pt-3 dark:border-slate-700">
                <input type="hidden" name="id" value={shift.id} />
                <ConfirmButton message="Diese Schicht wirklich löschen?">
                  Schicht löschen
                </ConfirmButton>
              </form>
            )}

            {!canSubmit && !canReview && !canRecalculate && !canEdit && (
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Keine Aktionen verfügbar.
              </p>
            )}
          </div>
        </Card>
      </div>

      {shift.calculation && (
        <div className="mt-6">
          <h2 className="mb-3 text-lg font-semibold">
            Berechnung
            {shift.calculation.is_holiday && shift.calculation.holiday_name
              ? ` · Feiertag: ${shift.calculation.holiday_name}`
              : ""}
          </h2>
          <CalculationTable calc={shift.calculation} />
          {shift.calculation.calculated_at && (
            <p className="mt-2 text-xs text-slate-400">
              Berechnet am {formatDateTime(shift.calculation.calculated_at)}
            </p>
          )}
        </div>
      )}
    </>
  );
}
