from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import is_admin_user
from apps.common.audit import log_action
from apps.common.csv_export import csv_response
from apps.common.models import AuditLog
from apps.common.pagination import StandardPagination
from apps.common.tenancy import assert_org_match, get_current_org, scope_queryset

from .emails import send_shift_approved_email, send_shift_rejected_email
from .models import Shift
from .serializers import ShiftSerializer
from .services import recalculate_shift


def _shift_interval(date, start_time, end_time):
    start = datetime.combine(date, start_time)
    end = datetime.combine(date, end_time)
    if end <= start:
        end += timedelta(days=1)
    return start, end


def _ensure_no_overlap(*, employee, date, start_time, end_time, exclude_id=None):
    """Verhindert überlappende Schichten pro Mitarbeiter, auch über Mitternacht."""
    start, end = _shift_interval(date, start_time, end_time)
    candidates = Shift.objects.filter(
        employee=employee,
        date__gte=date - timedelta(days=1),
        date__lte=date + timedelta(days=1),
    ).exclude(status=Shift.Status.REJECTED)
    if exclude_id:
        candidates = candidates.exclude(pk=exclude_id)

    for existing in candidates:
        existing_start, existing_end = _shift_interval(
            existing.date, existing.start_time, existing.end_time,
        )
        if start < existing_end and end > existing_start:
            raise ValidationError({
                "date": (
                    "Diese Schicht überschneidet sich mit einer vorhandenen Schicht "
                    f"am {existing.date:%d.%m.%Y} von "
                    f"{existing.start_time:%H:%M} bis {existing.end_time:%H:%M}."
                )
            })

# Zustände, in denen eine Pflegekraft ihre Schicht noch ändern darf.
EMPLOYEE_EDITABLE = {Shift.Status.DRAFT, Shift.Status.REJECTED}


class ShiftViewSet(viewsets.ModelViewSet):
    """Schichterfassung & Admin-Prüfung. Mitarbeiter sehen nur eigene Schichten."""

    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = (
            Shift.objects.select_related("customer", "employee", "created_by")
            .prefetch_related("calculation")
        )
        user = self.request.user
        qs = scope_queryset(qs, user)
        if not is_admin_user(user):
            qs = qs.filter(employee=user)

        params = self.request.query_params
        if status_param := params.get("status"):
            qs = qs.filter(status=status_param)
        if customer := params.get("customer"):
            qs = qs.filter(customer_id=customer)
        if employee := params.get("employee"):
            if is_admin_user(user):
                qs = qs.filter(employee_id=employee)
        if date_from := params.get("date_from"):
            qs = qs.filter(date__gte=date_from)
        if date_to := params.get("date_to"):
            qs = qs.filter(date__lte=date_to)
        if q := params.get("q"):
            q = q.strip()
            if q:
                query = (
                    Q(customer__name__icontains=q)
                    | Q(employee__first_name__icontains=q)
                    | Q(employee__last_name__icontains=q)
                    | Q(employee__email__icontains=q)
                )
                if parsed := parse_date(q):
                    query |= Q(date=parsed)
                qs = qs.filter(query)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        org = get_current_org(user)
        employee = serializer.validated_data.get("employee")
        # Mitarbeiter dürfen nur für sich selbst erfassen.
        if not is_admin_user(user) or employee is None:
            employee = user
        # Kunde und Mitarbeiter müssen zur Organisation des Erfassers gehören.
        customer = serializer.validated_data.get("customer")
        if customer is not None:
            assert_org_match(user, customer.organization_id)
        assert_org_match(user, employee.organization_id)
        _ensure_no_overlap(
            employee=employee,
            date=serializer.validated_data["date"],
            start_time=serializer.validated_data["start_time"],
            end_time=serializer.validated_data["end_time"],
        )
        shift = serializer.save(
            employee=employee, created_by=user, status=Shift.Status.DRAFT,
            organization=org or employee.organization,
        )
        log_action(user, AuditLog.Action.CREATE, shift, summary=f"Schicht {shift.date} angelegt")

    def _guard_editable(self, instance):
        """Mitarbeiter dürfen nur eigene Schichten im Entwurf/Abgelehnt ändern."""
        user = self.request.user
        if is_admin_user(user):
            return
        if instance.employee_id != user.id:
            raise PermissionDenied("Sie können nur eigene Schichten bearbeiten.")
        if instance.status not in EMPLOYEE_EDITABLE:
            raise PermissionDenied(
                "Eingereichte oder freigegebene Schichten können nicht mehr bearbeitet werden."
            )

    def perform_update(self, serializer):
        self._guard_editable(serializer.instance)
        instance = serializer.instance
        data = serializer.validated_data
        employee = data.get("employee") or instance.employee
        _ensure_no_overlap(
            employee=employee,
            date=data.get("date", instance.date),
            start_time=data.get("start_time", instance.start_time),
            end_time=data.get("end_time", instance.end_time),
            exclude_id=instance.id,
        )
        shift = serializer.save()
        summary = "Korrigiert durch Admin" if is_admin_user(self.request.user) else "Bearbeitet"
        log_action(self.request.user, AuditLog.Action.UPDATE, shift, summary=summary)

    def perform_destroy(self, instance):
        self._guard_editable(instance)
        log_action(self.request.user, AuditLog.Action.DELETE, instance,
                   summary=f"Schicht {instance.date} gelöscht")
        instance.delete()

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """Schicht zur Prüfung einreichen (Entwurf/Abgelehnt -> Eingereicht)."""
        shift = self.get_object()
        user = request.user
        if not is_admin_user(user) and shift.employee_id != user.id:
            raise PermissionDenied("Sie können nur eigene Schichten einreichen.")
        if shift.status not in EMPLOYEE_EDITABLE:
            raise ValidationError("Nur Entwürfe oder abgelehnte Schichten können eingereicht werden.")
        shift.status = Shift.Status.SUBMITTED
        shift.submitted_at = timezone.now()
        shift.correction_reason = ""
        shift.save(update_fields=["status", "submitted_at", "correction_reason", "updated_at"])
        log_action(user, AuditLog.Action.SUBMIT, shift, summary="Zur Prüfung eingereicht")
        return Response(self.get_serializer(shift).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Schicht freigeben (nur Admin): SUBMITTED -> APPROVED, berechnet automatisch."""
        if not is_admin_user(request.user):
            raise PermissionDenied("Nur Administratoren dürfen Schichten freigeben.")
        shift = self.get_object()
        if shift.status != Shift.Status.SUBMITTED:
            raise ValidationError("Nur eingereichte Schichten können freigegeben werden.")
        try:
            recalculate_shift(shift)
        except ValueError as exc:
            raise ValidationError(str(exc))
        shift.status = Shift.Status.APPROVED
        shift.reviewed_by = request.user
        shift.reviewed_at = timezone.now()
        shift.correction_reason = ""
        shift.save(update_fields=["status", "reviewed_by", "reviewed_at", "correction_reason", "updated_at"])
        log_action(request.user, AuditLog.Action.APPROVE, shift, summary="Freigegeben + berechnet")
        send_shift_approved_email(shift)
        shift.refresh_from_db()
        return Response(self.get_serializer(shift).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """Schicht ablehnen (nur Admin): SUBMITTED -> REJECTED, Grund erforderlich."""
        if not is_admin_user(request.user):
            raise PermissionDenied("Nur Administratoren dürfen Schichten ablehnen.")
        shift = self.get_object()
        if shift.status != Shift.Status.SUBMITTED:
            raise ValidationError("Nur eingereichte Schichten können abgelehnt werden.")
        reason = (request.data.get("reason") or request.data.get("correction_reason") or "").strip()
        if not reason:
            raise ValidationError({"reason": "Ein Ablehnungsgrund ist erforderlich."})
        shift.status = Shift.Status.REJECTED
        shift.reviewed_by = request.user
        shift.reviewed_at = timezone.now()
        shift.correction_reason = reason
        shift.save(update_fields=["status", "reviewed_by", "reviewed_at", "correction_reason", "updated_at"])
        log_action(request.user, AuditLog.Action.REJECT, shift, summary=f"Abgelehnt: {reason}")
        send_shift_rejected_email(shift, reason)
        return Response(self.get_serializer(shift).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def calculate(self, request, pk=None):
        """Schicht (neu) berechnen und das Ergebnis speichern (nur Admin)."""
        if not is_admin_user(request.user):
            raise PermissionDenied("Nur Administratoren dürfen Schichten berechnen.")
        shift = self.get_object()
        try:
            recalculate_shift(shift)
        except ValueError as exc:
            raise ValidationError(str(exc))
        log_action(request.user, AuditLog.Action.UPDATE, shift, summary="Neu berechnet")
        shift.refresh_from_db()
        return Response(self.get_serializer(shift).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def export(self, request):
        """Exportiert die (gefilterten) Schichten als CSV (nur Admin)."""
        if not is_admin_user(request.user):
            raise PermissionDenied("Nur Administratoren dürfen exportieren.")
        header = [
            "Datum", "Mitarbeiter", "Kunde", "Schichtart", "Start", "Ende",
            "Pause (Min)", "Status", "Bezahlte Stunden", "Netto (EUR)",
        ]

        def rows():
            for s in self.get_queryset():
                calc = getattr(s, "calculation", None)
                yield [
                    s.date.isoformat(),
                    s.employee.get_full_name() or s.employee.email,
                    s.customer.name,
                    s.get_shift_type_display(),
                    s.start_time.strftime("%H:%M"),
                    s.end_time.strftime("%H:%M"),
                    s.break_minutes,
                    s.get_status_display(),
                    calc.paid_hours if calc else "",
                    calc.net_total if calc else "",
                ]

        return csv_response("schichten.csv", header, rows())

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Kennzahlen über die (rollen-/mandantengescopte) Schichtmenge.

        Admins sehen die Werte ihrer Organisation, Mitarbeiter nur die eigenen –
        das Scoping steckt bereits in ``get_queryset``.
        """
        qs = self.get_queryset()

        employees, customers = set(), set()
        gesamtstunden = zahlbare_stunden = Decimal("0")
        pausen_minuten = 0
        netto = Decimal("0")
        status_counts: dict[str, int] = {}

        for shift in qs:
            employees.add(shift.employee_id)
            customers.add(shift.customer_id)
            pausen_minuten += shift.break_minutes
            status_counts[shift.status] = status_counts.get(shift.status, 0) + 1
            calc = getattr(shift, "calculation", None)
            if calc is not None:
                gesamtstunden += calc.total_hours
                zahlbare_stunden += calc.paid_hours
                netto += calc.net_total

        return Response({
            "anzahl_schichten": qs.count(),
            "gesamtpersonal": len(employees),
            "gesamtkunden": len(customers),
            "gesamtstunden": gesamtstunden,
            "zahlbare_stunden": zahlbare_stunden,
            "pausenzeit_minuten": pausen_minuten,
            "netto_summe": netto,
            "status_counts": status_counts,
        })
