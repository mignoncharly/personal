import type { Metadata } from "next";

import { OrganizationForm } from "@/components/forms/organization-form";
import { Card, PageHeader } from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { requireAdmin } from "@/lib/dal";
import type { OrganizationSettings } from "@/lib/types";

export const metadata: Metadata = { title: "Organisation" };

export default async function OrganizationSettingsPage() {
  await requireAdmin();
  const organization = await apiFetch<OrganizationSettings>("/organization/");

  return (
    <>
      <PageHeader
        title="Organisation"
        subtitle="Firmenangaben für die Navigation und den Rechnungsbriefkopf."
      />
      <Card className="max-w-3xl">
        <OrganizationForm organization={organization} />
      </Card>
    </>
  );
}
