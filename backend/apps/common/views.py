from django.db import connection
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdmin

from .models import AuditLog
from .pagination import StandardPagination
from .serializers import AuditLogSerializer
from .tenancy import scope_queryset


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Schreibgeschütztes Audit-Log (nur Admin), auf die eigene Organisation begrenzt."""

    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = scope_queryset(
            AuditLog.objects.select_related("actor"), self.request.user
        )
        params = self.request.query_params
        if action := params.get("action"):
            qs = qs.filter(action=action)
        if entity_type := params.get("entity_type"):
            qs = qs.filter(entity_type=entity_type)
        return qs


class SystemStatusView(APIView):
    """Kompakter Admin-Status für Betrieb und Stammdatenqualität."""

    permission_classes = [IsAdmin]

    def get(self, request):
        from apps.customers.models import Customer, TravelCostRule
        from apps.employees.models import EmployeeProfile
        from apps.invoicing.models import Invoice
        from apps.shifts.models import Shift

        db_ok = True
        try:
            connection.ensure_connection()
        except Exception:
            db_ok = False

        customers = scope_queryset(
            Customer.objects.prefetch_related("contracts"), request.user,
        ).filter(is_active=True)
        customers_without_contract = [
            {"id": c.id, "name": c.name}
            for c in customers
            if c.active_contract is None
        ]
        customers_without_email = [
            {"id": c.id, "name": c.name}
            for c in customers
            if not c.email
        ]

        employees = scope_queryset(
            EmployeeProfile.objects.select_related("user"), request.user,
            field="user__organization",
        ).filter(is_active=True)
        travel_costs_enabled = scope_queryset(
            TravelCostRule.objects.select_related("contract__customer"), request.user,
            field="contract__customer__organization",
        ).filter(enabled=True, contract__is_active=True).exists()
        employees_without_address = []
        if travel_costs_enabled:
            employees_without_address = [
                {
                    "id": e.id,
                    "user_id": e.user_id,
                    "name": e.user.get_full_name() or e.user.email,
                }
                for e in employees
                if not (e.street and e.zip_code and e.city)
            ]

        billable_shifts = scope_queryset(
            Shift.objects.select_related("customer", "employee"), request.user,
        ).filter(status=Shift.Status.APPROVED, invoice__isnull=True)
        approved_not_invoiced = [
            {
                "id": s.id,
                "date": s.date.isoformat(),
                "customer": s.customer.name,
                "employee": s.employee.get_full_name() or s.employee.email,
            }
            for s in billable_shifts.order_by("-date")[:10]
        ]

        open_invoices = scope_queryset(Invoice.objects.all(), request.user).filter(
            status__in=(Invoice.Status.FINALIZED, Invoice.Status.SENT)
        )
        overdue_count = sum(1 for inv in open_invoices if inv.is_overdue)

        return Response({
            "service": {
                "status": "ok" if db_ok else "degraded",
                "database": "ok" if db_ok else "error",
            },
            "data_quality": {
                "customers_without_contract": customers_without_contract[:10],
                "customers_without_contract_count": len(customers_without_contract),
                "customers_without_email": customers_without_email[:10],
                "customers_without_email_count": len(customers_without_email),
                "travel_costs_enabled": travel_costs_enabled,
                "employees_without_address": employees_without_address[:10],
                "employees_without_address_count": len(employees_without_address),
                "approved_not_invoiced": approved_not_invoiced,
                "approved_not_invoiced_count": billable_shifts.count(),
                "overdue_invoices_count": overdue_count,
            },
        })
