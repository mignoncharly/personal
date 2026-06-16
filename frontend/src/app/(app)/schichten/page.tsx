import Link from "next/link";
import type { Metadata } from "next";

import { ShiftStatusBadge } from "@/components/status";
import {
  Button,
  ButtonLink,
  Card,
  EmptyState,
  Input,
  PageHeader,
  Pagination,
  Table,
  Td,
  Th,
  cn,
} from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { requireUser } from "@/lib/dal";
import { formatDate, formatEuro, formatHours, formatTime } from "@/lib/format";
import type { Paginated, Shift, ShiftStatus } from "@/lib/types";

export const metadata: Metadata = { title: "Schichten" };

const FILTERS: { value: string; label: string }[] = [
  { value: "", label: "Alle" },
  { value: "draft", label: "Entwurf" },
  { value: "submitted", label: "Eingereicht" },
  { value: "approved", label: "Freigegeben" },
  { value: "invoiced", label: "Abgerechnet" },
];

export default async function ShiftsPage(props: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const user = await requireUser();
  const params = await props.searchParams;
  const status = typeof params.status === "string" ? params.status : "";
  const q = typeof params.q === "string" ? params.q.trim() : "";
  const page = Number(typeof params.page === "string" ? params.page : "1") || 1;

  const data = await apiFetch<Paginated<Shift>>("/shifts/", {
    query: { status: status || undefined, q: q || undefined, page },
  });
  const shifts = data.results;
  const totalPages = Math.max(1, Math.ceil(data.count / 50));
  const makeHref = (p: number) =>
    `/schichten?${new URLSearchParams({
      ...(status ? { status } : {}),
      ...(q ? { q } : {}),
      page: String(p),
    }).toString()}`;

  return (
    <>
      <PageHeader
        title="Schichten"
        subtitle={
          user.is_admin
            ? "Schichten prüfen, abrechnen und nach Status organisieren."
            : "Ihre erfassten Schichten und der aktuelle Prüfstatus."
        }
        actions={
          <>
            {user.is_admin && (
              <ButtonLink
                href={`/schichten/export?${new URLSearchParams({ ...(status ? { status } : {}), ...(q ? { q } : {}) }).toString()}`}
                variant="secondary"
                download
              >
                Exportieren
              </ButtonLink>
            )}
            <ButtonLink href="/schichten/neu">Schicht erstellen</ButtonLink>
          </>
        }
      />

      <Card className="mb-5">
        <form className="grid gap-3 lg:grid-cols-[1fr_auto]" action="/schichten">
          <div>
            <label htmlFor="shift-search" className="text-sm font-semibold text-slate-700">
              Suche
            </label>
            <Input
              id="shift-search"
              name="q"
              defaultValue={q}
              placeholder="Datum, Kunde, Mitarbeiter oder Status suchen"
              className="mt-2"
            />
            {status && <input type="hidden" name="status" value={status} />}
          </div>
          <div className="flex items-end gap-2">
            <Button type="submit" variant="secondary">Suchen</Button>
            {(q || status) && (
              <ButtonLink href="/schichten" variant="ghost">Zurücksetzen</ButtonLink>
            )}
          </div>
        </form>
        <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-100 pt-4">
          {FILTERS.map((f) => {
            const active = status === f.value;
            const href = `/schichten${
              f.value || q
                ? `?${new URLSearchParams({
                    ...(f.value ? { status: f.value } : {}),
                    ...(q ? { q } : {}),
                  }).toString()}`
                : ""
            }`;
            return (
              <Link
                key={f.value || "all"}
                href={href}
                className={cn(
                  "rounded-full px-3 py-1.5 text-sm font-semibold transition-colors ring-1 ring-inset",
                  active
                    ? "bg-indigo-600 text-white ring-indigo-600"
                    : "bg-white text-slate-600 ring-slate-200 hover:bg-slate-50",
                )}
              >
                {f.label}
              </Link>
            );
          })}
        </div>
      </Card>

      {shifts.length === 0 ? (
        <EmptyState>
          Keine Schichten gefunden. {" "}
          <Link href="/schichten/neu" className="font-semibold text-indigo-600 hover:underline">
            Schicht erstellen
          </Link>
        </EmptyState>
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>Datum</Th>
              <Th>Kunde</Th>
              <Th>Mitarbeiter</Th>
              <Th>Beginn</Th>
              <Th>Ende</Th>
              <Th>Stunden</Th>
              <Th>Status</Th>
              <Th className="text-right">Betrag</Th>
              <Th className="text-right">Aktionen</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {shifts.map((shift) => (
              <tr key={shift.id} className="hover:bg-slate-50">
                <Td className="font-semibold text-slate-950">{formatDate(shift.date)}</Td>
                <Td>{shift.customer_name}</Td>
                <Td>{shift.employee_name || "-"}</Td>
                <Td>{formatTime(shift.start_time)}</Td>
                <Td>{formatTime(shift.end_time)}</Td>
                <Td>
                  {shift.calculation ? formatHours(shift.calculation.paid_hours) : "-"}
                </Td>
                <Td>
                  <ShiftStatusBadge
                    status={shift.status as ShiftStatus}
                    label={shift.status_display}
                  />
                </Td>
                <Td className="text-right font-semibold text-slate-950">
                  {shift.calculation ? formatEuro(shift.calculation.net_total) : "-"}
                </Td>
                <Td className="text-right">
                  <Link
                    href={`/schichten/${shift.id}`}
                    className="font-semibold text-indigo-600 hover:underline"
                  >
                    Details
                  </Link>
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      <Pagination
        page={page}
        totalPages={totalPages}
        count={data.count}
        makeHref={makeHref}
      />
    </>
  );
}
