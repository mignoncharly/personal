import type { Metadata } from "next";

import { InvoiceGenerateForm } from "@/components/forms/invoice-generate-form";
import { Card, PageHeader } from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { requireAdmin } from "@/lib/dal";
import type { CustomerChoice } from "@/lib/types";

export const metadata: Metadata = { title: "Rechnung erstellen" };

export default async function NewInvoicePage() {
  await requireAdmin();
  const customers = await apiFetch<CustomerChoice[]>("/customer-choices/");

  return (
    <>
      <PageHeader
        title="Rechnung erstellen"
        subtitle="Aus freigegebenen Schichten eines Kunden im gewählten Zeitraum."
      />
      <Card className="max-w-2xl">
        <InvoiceGenerateForm customers={customers} />
      </Card>
    </>
  );
}
