"""Auswertungen (betriebswirtschaftliche Kennzahlen) für die Organisation.

Reine Lese-Aggregationen über vorhandene Daten – keine eigenen Modelle. Alle
Abfragen sind über ``scope_queryset`` strikt mandantengebunden.
"""

from datetime import date as date_cls
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils.dateparse import parse_date
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin
from apps.common.csv_export import csv_response
from apps.common.tenancy import scope_queryset
from apps.shifts.models import Shift

from .models import Invoice

ZERO = Decimal("0")
# Rechnungen, die zum Umsatz zählen (Entwürfe und Stornos bleiben außen vor).
COUNTING_STATUSES = (
    Invoice.Status.FINALIZED,
    Invoice.Status.SENT,
    Invoice.Status.PAID,
)


def _default_range() -> tuple[date_cls, date_cls]:
    today = date_cls.today()
    return date_cls(today.year, 1, 1), today


def _parse_range(params) -> tuple[date_cls, date_cls]:
    default_from, default_to = _default_range()
    start = parse_date(params.get("from", "")) or default_from
    end = parse_date(params.get("to", "")) or default_to
    if start > end:
        start, end = end, start
    return start, end


class ReportView(APIView):
    """GET /api/reports/?from=YYYY-MM-DD&to=YYYY-MM-DD[&format=csv]

    Liefert Umsatz im Zeitraum, Aufschlüsselung je Monat und je Kunde, die
    geleisteten Stunden je Mitarbeiter sowie eine Momentaufnahme der offenen und
    überfälligen Forderungen.
    """

    permission_classes = [IsAdmin]

    def get(self, request):
        start, end = _parse_range(request.query_params)

        invoices = scope_queryset(Invoice.objects.all(), request.user).filter(
            status__in=COUNTING_STATUSES,
            invoice_date__gte=start,
            invoice_date__lte=end,
        )

        by_customer = list(
            invoices.values("customer__name")
            .annotate(net=Sum("subtotal_net"), gross=Sum("total_gross"), count=Count("id"))
            .order_by("-gross")
        )

        # Hinweis: NICHT "format" verwenden – das ist in DRF für die
        # Content-Negotiation reserviert und würde mangels CSV-Renderer 404 liefern.
        if request.query_params.get("download") == "csv":
            return self._csv(by_customer, start, end)

        totals = invoices.aggregate(
            net=Sum("subtotal_net"), gross=Sum("total_gross"), count=Count("id")
        )

        by_month = [
            {
                "month": row["month"].strftime("%Y-%m"),
                "net": row["net"] or ZERO,
                "gross": row["gross"] or ZERO,
                "count": row["count"],
            }
            for row in invoices.annotate(month=TruncMonth("invoice_date"))
            .values("month")
            .annotate(net=Sum("subtotal_net"), gross=Sum("total_gross"), count=Count("id"))
            .order_by("month")
        ]

        shifts = (
            scope_queryset(Shift.objects.all(), request.user)
            .filter(
                date__gte=start,
                date__lte=end,
                status__in=(Shift.Status.APPROVED, Shift.Status.INVOICED),
                calculation__isnull=False,
            )
            .values("employee__first_name", "employee__last_name", "employee__email")
            .annotate(hours=Sum("calculation__paid_hours"), shifts=Count("id"))
            .order_by("-hours")
        )
        by_employee = [
            {
                "employee": (
                    f"{row['employee__first_name']} {row['employee__last_name']}".strip()
                    or row["employee__email"]
                ),
                "hours": row["hours"] or ZERO,
                "shifts": row["shifts"],
            }
            for row in shifts
        ]

        return Response({
            "from": start.isoformat(),
            "to": end.isoformat(),
            "totals": {
                "net": totals["net"] or ZERO,
                "gross": totals["gross"] or ZERO,
                "count": totals["count"] or 0,
            },
            "by_month": by_month,
            "by_customer": [
                {
                    "customer": row["customer__name"],
                    "net": row["net"] or ZERO,
                    "gross": row["gross"] or ZERO,
                    "count": row["count"],
                }
                for row in by_customer
            ],
            "by_employee": by_employee,
            "receivables": self._receivables(request),
        })

    def _receivables(self, request) -> dict:
        """Momentaufnahme: offene und überfällige Forderungen (zeitraumunabhängig)."""
        open_qs = scope_queryset(Invoice.objects.all(), request.user).filter(
            status__in=(Invoice.Status.FINALIZED, Invoice.Status.SENT)
        )
        today = date_cls.today()
        open_total = overdue_total = ZERO
        open_count = overdue_count = 0
        for inv in open_qs:
            open_total += inv.total_gross
            open_count += 1
            if inv.due_date < today:
                overdue_count += 1
                overdue_total += inv.total_gross
        return {
            "open_count": open_count,
            "open_total": open_total,
            "overdue_count": overdue_count,
            "overdue_total": overdue_total,
        }

    def _csv(self, by_customer, start, end):
        header = ["Kunde", "Anzahl Rechnungen", "Netto (EUR)", "Brutto (EUR)"]

        def rows():
            for row in by_customer:
                yield [
                    row["customer__name"],
                    row["count"],
                    row["net"] or ZERO,
                    row["gross"] or ZERO,
                ]

        return csv_response(f"umsatz_{start.isoformat()}_{end.isoformat()}.csv", header, rows())
