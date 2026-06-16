import Link from "next/link";
import type { Metadata } from "next";

import {
  Badge,
  EmptyState,
  PageHeader,
  Table,
  Td,
  Th,
} from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { requireAdmin } from "@/lib/dal";
import { formatDateTime } from "@/lib/format";
import type { AuditEntry, Paginated } from "@/lib/types";

export const metadata: Metadata = { title: "Protokoll" };

const ENTITY_LABEL: Record<string, string> = {
  Shift: "Schicht",
  Invoice: "Rechnung",
  Customer: "Kunde",
  EmployeeProfile: "Mitarbeiter",
  User: "Benutzer",
};

const ACTION_COLOR: Record<string, "slate" | "green" | "red" | "amber" | "blue" | "indigo"> = {
  create: "green",
  update: "amber",
  delete: "red",
  submit: "blue",
  approve: "green",
  reject: "red",
  invoice: "indigo",
};

export default async function ProtokollPage(props: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  await requireAdmin();
  const params = await props.searchParams;
  const page = Number(typeof params.page === "string" ? params.page : "1") || 1;

  const data = await apiFetch<Paginated<AuditEntry>>("/audit-log/", {
    query: { page },
  });

  const totalPages = Math.max(1, Math.ceil(data.count / 50));

  return (
    <>
      <PageHeader
        title="Protokoll"
        subtitle="Wer hat was wann geändert (Schichten, Rechnungen, Stammdaten)."
      />

      {data.results.length === 0 ? (
        <EmptyState>Noch keine Protokolleinträge.</EmptyState>
      ) : (
        <>
          <Table>
            <thead>
              <tr>
                <Th>Zeitpunkt</Th>
                <Th>Akteur</Th>
                <Th>Aktion</Th>
                <Th>Objekt</Th>
                <Th>Zusammenfassung</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
              {data.results.map((entry) => (
                <tr key={entry.id}>
                  <Td className="whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                    {formatDateTime(entry.created_at)}
                  </Td>
                  <Td>{entry.actor_name}</Td>
                  <Td>
                    <Badge color={ACTION_COLOR[entry.action] ?? "slate"}>
                      {entry.action_display}
                    </Badge>
                  </Td>
                  <Td className="text-sm">
                    {(ENTITY_LABEL[entry.entity_type] ?? entry.entity_type)}
                    {entry.entity_id ? ` #${entry.entity_id}` : ""}
                  </Td>
                  <Td className="text-sm text-slate-600 dark:text-slate-300">
                    {entry.summary}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>

          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between text-sm">
              <span className="text-slate-500 dark:text-slate-400">
                Seite {page} von {totalPages} · {data.count} Einträge
              </span>
              <div className="flex gap-2">
                {data.previous && (
                  <Link
                    href={`/protokoll?page=${page - 1}`}
                    className="rounded-md border border-slate-300 px-3 py-1 font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
                  >
                    Zurück
                  </Link>
                )}
                {data.next && (
                  <Link
                    href={`/protokoll?page=${page + 1}`}
                    className="rounded-md border border-slate-300 px-3 py-1 font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
                  >
                    Weiter
                  </Link>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </>
  );
}
