import { notFound } from "next/navigation";
import type { Metadata } from "next";

import { deleteEmployee, updateEmployee } from "@/actions/employees";
import { ConfirmButton } from "@/components/confirm-button";
import { EmployeeForm } from "@/components/forms/employee-form";
import { Alert, Badge, ButtonLink, Card, PageHeader } from "@/components/ui";
import { apiFetch, ApiError } from "@/lib/api";
import { requireAdmin } from "@/lib/dal";
import { formatDate } from "@/lib/format";
import type { Employee } from "@/lib/types";

export const metadata: Metadata = { title: "Mitarbeiter" };

const QUAL: Record<string, string> = {
  pflegehilfskraft: "Pflegehilfskraft",
  pflegefachkraft: "Pflegefachkraft",
};

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

export default async function EmployeeDetailPage(props: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  await requireAdmin();
  const { id } = await props.params;
  const { edit, error } = await props.searchParams;
  const actionError = typeof error === "string" ? error : undefined;

  let employee: Employee;
  try {
    employee = await apiFetch<Employee>(`/employees/${id}/`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  if (edit === "1") {
    return (
      <>
        <PageHeader title="Mitarbeiter bearbeiten" subtitle={employee.full_name || employee.email} />
        <Card className="max-w-3xl">
          <EmployeeForm
            action={updateEmployee}
            employee={employee}
            submitLabel="Änderungen speichern"
            cancelHref={`/mitarbeiter/${employee.id}`}
          />
        </Card>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title={employee.full_name || employee.email}
        subtitle={QUAL[employee.qualification] ?? employee.qualification}
        actions={
          <>
            <ButtonLink href="/mitarbeiter" variant="ghost">
              Zurück
            </ButtonLink>
            <ButtonLink href={`/mitarbeiter/${employee.id}?edit=1`} variant="secondary">
              Bearbeiten
            </ButtonLink>
          </>
        }
      />

      {actionError && (
        <div className="mb-4">
          <Alert kind="error">{actionError}</Alert>
        </div>
      )}

      <Card className="max-w-2xl">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Stammdaten</h2>
          {employee.is_active ? (
            <Badge color="green">aktiv</Badge>
          ) : (
            <Badge color="slate">inaktiv</Badge>
          )}
        </div>
        <dl className="divide-y divide-slate-100 dark:divide-slate-700/60">
          <Row label="E-Mail" value={employee.email} />
          {employee.phone && <Row label="Telefon" value={employee.phone} />}
          <Row label="Qualifikation" value={QUAL[employee.qualification] ?? employee.qualification} />
          <Row
            label="Adresse"
            value={
              [
                employee.street,
                [employee.zip_code, employee.city].filter(Boolean).join(" "),
              ]
                .filter(Boolean)
                .join(", ") || "—"
            }
          />
          <Row label="Angelegt am" value={formatDate(employee.created_at)} />
        </dl>

        <form action={deleteEmployee} className="mt-4 border-t border-slate-100 pt-4 dark:border-slate-700">
          <input type="hidden" name="id" value={employee.id} />
          <ConfirmButton message="Diesen Mitarbeiter wirklich löschen?">
            Mitarbeiter löschen
          </ConfirmButton>
        </form>
      </Card>
    </>
  );
}
