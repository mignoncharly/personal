import Link from "next/link";
import type { Metadata } from "next";

import {
  Badge,
  ButtonLink,
  EmptyState,
  PageHeader,
  Table,
  Td,
  Th,
} from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { requireAdmin } from "@/lib/dal";
import type { Employee } from "@/lib/types";

export const metadata: Metadata = { title: "Mitarbeiter" };

const QUAL: Record<string, string> = {
  pflegehilfskraft: "Pflegehilfskraft",
  pflegefachkraft: "Pflegefachkraft",
};

export default async function EmployeesPage() {
  await requireAdmin();
  const employees = await apiFetch<Employee[]>("/employees/");

  return (
    <>
      <PageHeader
        title="Mitarbeiter"
        subtitle="Pflegekräfte und deren Zugänge."
        actions={<ButtonLink href="/mitarbeiter/neu">Mitarbeiter anlegen</ButtonLink>}
      />

      {employees.length === 0 ? (
        <EmptyState>Noch keine Mitarbeiter angelegt.</EmptyState>
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>Name</Th>
              <Th>E-Mail</Th>
              <Th>Qualifikation</Th>
              <Th>Ort</Th>
              <Th>Status</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {employees.map((e) => (
              <tr key={e.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/40">
                <Td>
                  <Link href={`/mitarbeiter/${e.id}`} className="block font-medium">
                    {e.full_name || "—"}
                  </Link>
                </Td>
                <Td>{e.email}</Td>
                <Td>{QUAL[e.qualification] ?? e.qualification}</Td>
                <Td>{e.city || "—"}</Td>
                <Td>
                  {e.is_active ? (
                    <Badge color="green">aktiv</Badge>
                  ) : (
                    <Badge color="slate">inaktiv</Badge>
                  )}
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </>
  );
}
