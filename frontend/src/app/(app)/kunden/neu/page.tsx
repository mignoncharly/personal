import type { Metadata } from "next";

import { createCustomer } from "@/actions/customers";
import { CustomerForm } from "@/components/forms/customer-form";
import { Card, PageHeader } from "@/components/ui";
import { requireAdmin } from "@/lib/dal";

export const metadata: Metadata = { title: "Kunde anlegen" };

export default async function NewCustomerPage() {
  await requireAdmin();
  return (
    <>
      <PageHeader
        title="Kunde anlegen"
        subtitle="Den Vertrag mit Konditionen legen Sie anschließend auf der Detailseite an."
      />
      <Card className="max-w-3xl">
        <CustomerForm
          action={createCustomer}
          submitLabel="Kunde speichern"
          cancelHref="/kunden"
        />
      </Card>
    </>
  );
}
