import { Badge } from "@/components/ui";
import type { InvoiceStatus, ShiftStatus } from "@/lib/types";

type Color = "slate" | "amber" | "green" | "red" | "indigo" | "blue";

const shiftColor: Record<ShiftStatus, Color> = {
  draft: "slate",
  submitted: "amber",
  approved: "green",
  rejected: "red",
  invoiced: "blue",
};

const shiftLabel: Record<ShiftStatus, string> = {
  draft: "Entwurf",
  submitted: "Eingereicht",
  approved: "Freigegeben",
  rejected: "Abgelehnt",
  invoiced: "Abgerechnet",
};

export function ShiftStatusBadge({
  status,
  label,
}: {
  status: ShiftStatus;
  label?: string;
}) {
  return <Badge color={shiftColor[status]}>{label ?? shiftLabel[status]}</Badge>;
}

const invoiceColor: Record<InvoiceStatus, Color> = {
  draft: "amber",
  finalized: "indigo",
  sent: "blue",
  paid: "green",
  cancelled: "red",
};

const invoiceLabel: Record<InvoiceStatus, string> = {
  draft: "Entwurf",
  finalized: "Festgeschrieben",
  sent: "Versendet",
  paid: "Bezahlt",
  cancelled: "Storniert",
};

export function InvoiceStatusBadge({
  status,
  label,
}: {
  status: InvoiceStatus;
  label?: string;
}) {
  return (
    <Badge color={invoiceColor[status]}>{label ?? invoiceLabel[status]}</Badge>
  );
}
