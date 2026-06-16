import type { Metadata } from "next";

import { createEmployee } from "@/actions/employees";
import { EmployeeForm } from "@/components/forms/employee-form";
import { Card, PageHeader } from "@/components/ui";
import { requireAdmin } from "@/lib/dal";

export const metadata: Metadata = { title: "Mitarbeiter anlegen" };

export default async function NewEmployeePage() {
  await requireAdmin();
  return (
    <>
      <PageHeader title="Mitarbeiter anlegen" subtitle="Neue Pflegekraft mit Login anlegen." />
      <Card className="max-w-3xl">
        <EmployeeForm
          action={createEmployee}
          submitLabel="Mitarbeiter speichern"
          cancelHref="/mitarbeiter"
        />
      </Card>
    </>
  );
}
