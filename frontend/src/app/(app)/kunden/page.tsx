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
import { formatEuro } from "@/lib/format";
import type { Customer } from "@/lib/types";

export const metadata: Metadata = { title: "Kunden" };

const BL: Record<string, string> = { HE: "Hessen", RP: "Rheinland-Pfalz" };

export default async function CustomersPage() {
  await requireAdmin();
  const customers = await apiFetch<Customer[]>("/customers/");

  return (
    <>
      <PageHeader
        title="Kunden"
        subtitle="Pflegeeinrichtungen, Verträge und Konditionen."
        actions={<ButtonLink href="/kunden/neu">Kunde anlegen</ButtonLink>}
      />

      {customers.length === 0 ? (
        <EmptyState>Noch keine Kunden angelegt.</EmptyState>
      ) : (
        <Table>
          <thead>
            <tr>
              <Th>Name</Th>
              <Th>Ort</Th>
              <Th>Bundesland</Th>
              <Th>Stundensatz</Th>
              <Th>Status</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {customers.map((c) => (
              <tr key={c.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/40">
                <Td>
                  <Link href={`/kunden/${c.id}`} className="block font-medium">
                    {c.name}
                  </Link>
                </Td>
                <Td>{c.city || "—"}</Td>
                <Td>{BL[c.bundesland] ?? c.bundesland}</Td>
                <Td>
                  {c.active_contract
                    ? formatEuro(c.active_contract.base_hourly_rate)
                    : "kein Vertrag"}
                </Td>
                <Td>
                  {c.is_active ? (
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
