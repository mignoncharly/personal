from decimal import Decimal

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin
from apps.common.audit import log_action
from apps.common.csv_export import csv_response
from apps.common.models import AuditLog
from apps.common.pagination import StandardPagination
from apps.common.tenancy import TenantScopedViewSet, assert_org_match

from .emails import send_invoice_email, send_reminder_email
from .models import Invoice
from .pdf import build_and_store_pdf
from .serializers import InvoiceGenerateSerializer, InvoiceSerializer
from .services import generate_invoice, release_invoice_shifts


class InvoiceViewSet(TenantScopedViewSet, viewsets.ModelViewSet):
    """Rechnungen (nur Admin). Erstellung ausschließlich über die generate-Action."""

    queryset = Invoice.objects.select_related("customer").prefetch_related("lines", "shifts")
    serializer_class = InvoiceSerializer
    permission_classes = [IsAdmin]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if customer := params.get("customer"):
            qs = qs.filter(customer_id=customer)
        if status_param := params.get("status"):
            qs = qs.filter(status=status_param)
        return qs

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed("POST", detail="Bitte /api/invoices/generate/ verwenden.")

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method, detail="Rechnungen können nicht direkt bearbeitet werden.")

    partial_update = update

    def perform_destroy(self, instance):
        if instance.status != Invoice.Status.DRAFT:
            raise ValidationError(
                "Nur Entwürfe können gelöscht werden. Festgeschriebene Rechnungen "
                "bitte stornieren."
            )
        # Schichten wieder freigeben, damit sie erneut abgerechnet werden können.
        release_invoice_shifts(instance)
        instance.delete()

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Erzeugt eine Rechnung aus freigegebenen Schichten (Kunde + Zeitraum)."""
        serializer = InvoiceGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Es darf nur für Kunden der eigenen Organisation abgerechnet werden.
        assert_org_match(request.user, serializer.validated_data["customer"].organization_id)
        try:
            invoice = generate_invoice(
                customer=serializer.validated_data["customer"],
                period_start=serializer.validated_data["period_start"],
                period_end=serializer.validated_data["period_end"],
                invoice_date=serializer.validated_data["invoice_date"],
                user=request.user,
            )
        except ValueError as exc:
            raise ValidationError(str(exc))
        return Response(self.get_serializer(invoice).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def finalize(self, request, pk=None):
        """Rechnung festschreiben (Entwurf -> festgeschrieben)."""
        invoice = self.get_object()
        if invoice.status != Invoice.Status.DRAFT:
            raise ValidationError("Nur Entwürfe können festgeschrieben werden.")
        invoice.status = Invoice.Status.FINALIZED
        invoice.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(invoice).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def export(self, request):
        """Exportiert die (gefilterten) Rechnungen als CSV."""
        header = [
            "Nummer", "Kunde", "Rechnungsdatum", "Zeitraum von", "Zeitraum bis",
            "Fällig am", "Status", "Netto (EUR)", "USt (EUR)", "Brutto (EUR)",
        ]

        def rows():
            for inv in self.get_queryset():
                yield [
                    inv.number,
                    inv.customer.name,
                    inv.invoice_date.isoformat(),
                    inv.period_start.isoformat(),
                    inv.period_end.isoformat(),
                    inv.due_date.isoformat(),
                    inv.get_status_display(),
                    inv.subtotal_net,
                    inv.vat_amount,
                    inv.total_gross,
                ]

        return csv_response("rechnungen.csv", header, rows())

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        """Versendet die Rechnung als PDF per E-Mail an den Kunden (BCC: Organisation).

        Nur möglich, sobald die Rechnung festgeschrieben ist. Bereits versendete
        Rechnungen können erneut verschickt werden.
        """
        invoice = self.get_object()
        if invoice.status not in (Invoice.Status.FINALIZED, Invoice.Status.SENT):
            raise ValidationError(
                "Nur festgeschriebene Rechnungen können versendet werden. "
                "Bitte zuerst festschreiben."
            )
        try:
            recipient = send_invoice_email(invoice)
        except ValueError as exc:
            raise ValidationError(str(exc))
        except Exception as exc:  # SMTP-/Versandfehler dem Nutzer verständlich melden
            raise ValidationError(f"E-Mail konnte nicht versendet werden: {exc}")
        invoice.status = Invoice.Status.SENT
        invoice.sent_at = timezone.now()
        invoice.save(update_fields=["status", "sent_at", "updated_at"])
        data = self.get_serializer(invoice).data
        data["sent_to"] = recipient
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def mark_paid(self, request, pk=None):
        """Rechnung als bezahlt markieren (festgeschrieben/versendet -> bezahlt)."""
        invoice = self.get_object()
        if invoice.status not in (Invoice.Status.FINALIZED, Invoice.Status.SENT):
            raise ValidationError(
                "Nur festgeschriebene oder versendete Rechnungen können als bezahlt "
                "markiert werden."
            )
        invoice.status = Invoice.Status.PAID
        invoice.paid_at = timezone.now()
        invoice.save(update_fields=["status", "paid_at", "updated_at"])
        return Response(self.get_serializer(invoice).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def mark_unpaid(self, request, pk=None):
        """Zahlungsmarkierung zurücknehmen (bezahlt -> versendet bzw. festgeschrieben)."""
        invoice = self.get_object()
        if invoice.status != Invoice.Status.PAID:
            raise ValidationError("Diese Rechnung ist nicht als bezahlt markiert.")
        invoice.status = (
            Invoice.Status.SENT if invoice.sent_at else Invoice.Status.FINALIZED
        )
        invoice.paid_at = None
        invoice.save(update_fields=["status", "paid_at", "updated_at"])
        return Response(self.get_serializer(invoice).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def remind(self, request, pk=None):
        """Sendet eine Zahlungserinnerung für eine überfällige Rechnung."""
        invoice = self.get_object()
        if not invoice.is_overdue:
            raise ValidationError(
                "Nur überfällige, noch offene Rechnungen können angemahnt werden."
            )
        try:
            recipient = send_reminder_email(invoice)
        except ValueError as exc:
            raise ValidationError(str(exc))
        except Exception as exc:
            raise ValidationError(f"E-Mail konnte nicht versendet werden: {exc}")
        invoice.last_reminded_at = timezone.now()
        invoice.save(update_fields=["last_reminded_at", "updated_at"])
        data = self.get_serializer(invoice).data
        data["sent_to"] = recipient
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Rechnung stornieren (festgeschrieben/versendet/bezahlt -> storniert).

        Die Rechnungsnummer bleibt erhalten (kein Löschen). Die enthaltenen
        Schichten werden wieder freigegeben, damit sie neu abgerechnet werden können.
        """
        invoice = self.get_object()
        if invoice.status == Invoice.Status.DRAFT:
            raise ValidationError("Entwürfe werden gelöscht, nicht storniert.")
        if invoice.status == Invoice.Status.CANCELLED:
            raise ValidationError("Diese Rechnung ist bereits storniert.")
        release_invoice_shifts(invoice)
        invoice.status = Invoice.Status.CANCELLED
        invoice.save(update_fields=["status", "updated_at"])
        log_action(
            request.user, AuditLog.Action.UPDATE, invoice,
            summary=f"Rechnung {invoice.number} storniert",
        )
        return Response(self.get_serializer(invoice).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Kennzahlen für das Dashboard: offene und überfällige Forderungen."""
        from datetime import date as date_cls

        open_qs = self.get_queryset().filter(
            status__in=(Invoice.Status.FINALIZED, Invoice.Status.SENT)
        )
        open_total = overdue_total = Decimal("0")
        open_count = overdue_count = 0
        today = date_cls.today()
        for inv in open_qs:
            open_total += inv.total_gross
            open_count += 1
            if inv.due_date < today:
                overdue_count += 1
                overdue_total += inv.total_gross
        return Response({
            "open_count": open_count,
            "open_total": open_total,
            "overdue_count": overdue_count,
            "overdue_total": overdue_total,
        })

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        """Erzeugt das Rechnungs-PDF, speichert es am Invoice und liefert es aus."""
        invoice = self.get_object()
        try:
            data = build_and_store_pdf(invoice)
        except RuntimeError as exc:
            raise ValidationError(str(exc))
        response = HttpResponse(data, content_type="application/pdf")
        disposition = "inline" if request.query_params.get("inline") else "attachment"
        response["Content-Disposition"] = f'{disposition}; filename="{invoice.number}.pdf"'
        return response
