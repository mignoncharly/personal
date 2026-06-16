import type { Metadata } from "next";

import { createShift } from "@/actions/shifts";
import { ShiftForm } from "@/components/forms/shift-form";
import { Card, PageHeader } from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { requireUser } from "@/lib/dal";
import type { CustomerChoice, Employee } from "@/lib/types";

export const metadata: Metadata = { title: "Schicht erfassen" };

export default async function NewShiftPage() {
  const user = await requireUser();
  const customers = await apiFetch<CustomerChoice[]>("/customer-choices/");
  const employees = user.is_admin
    ? await apiFetch<Employee[]>("/employees/", { query: { is_active: "true" } })
    : undefined;

  return (
    <>
      <PageHeader title="Schicht erfassen" subtitle="Neue Schicht anlegen." />
      <Card className="max-w-2xl">
        <ShiftForm
          action={createShift}
          customers={customers}
          employees={employees}
          submitLabel="Schicht speichern"
          cancelHref="/schichten"
        />
      </Card>
    </>
  );
}
