from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel
from apps.customers.models import Customer


class Shift(TimeStampedModel):
    """Eine von einer Pflegekraft erfasste Schicht (Status-Workflow bis Abrechnung)."""

    class ShiftType(models.TextChoices):
        EARLY = "frueh", _("Frühdienst")
        LATE = "spaet", _("Spätdienst")
        NIGHT = "nacht", _("Nachtdienst")

    class Status(models.TextChoices):
        DRAFT = "draft", _("Entwurf")
        SUBMITTED = "submitted", _("Eingereicht")
        APPROVED = "approved", _("Freigegeben")
        REJECTED = "rejected", _("Abgelehnt")
        INVOICED = "invoiced", _("Abgerechnet")

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.PROTECT,
        related_name="shifts", verbose_name=_("Organisation"),
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="shifts", verbose_name=_("Mitarbeiter"),
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="shifts",
        verbose_name=_("Kunde"),
    )

    shift_type = models.CharField(_("Schichtart"), max_length=10, choices=ShiftType.choices)
    date = models.DateField(_("Datum"))
    start_time = models.TimeField(_("Startzeit"))
    end_time = models.TimeField(_("Endzeit"))
    break_minutes = models.PositiveSmallIntegerField(_("Pause (Minuten)"), default=0)
    note = models.TextField(_("Bemerkung"), blank=True)

    status = models.CharField(
        _("Status"), max_length=12, choices=Status.choices, default=Status.DRAFT,
    )

    # Nachvollziehbarkeit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="created_shifts", verbose_name=_("erstellt von"),
    )
    submitted_at = models.DateTimeField(_("eingereicht am"), null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_shifts", verbose_name=_("geprüft von"),
    )
    reviewed_at = models.DateTimeField(_("geprüft am"), null=True, blank=True)
    correction_reason = models.TextField(_("Korrektur-/Ablehnungsgrund"), blank=True)

    invoice = models.ForeignKey(
        "invoicing.Invoice", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="shifts", verbose_name=_("Rechnung"),
        help_text=_("Verknüpfte Rechnung; verhindert doppelte Abrechnung."),
    )

    class Meta:
        verbose_name = _("Schicht")
        verbose_name_plural = _("Schichten")
        ordering = ("-date", "start_time")
        indexes = [
            models.Index(fields=["customer", "status", "date"]),
            models.Index(fields=["employee", "date"]),
        ]

    def __str__(self):
        return f"{self.employee} @ {self.customer} – {self.date} ({self.get_shift_type_display()})"

    @property
    def is_billable(self) -> bool:
        return self.status == self.Status.APPROVED and self.invoice_id is None


class ShiftCalculation(TimeStampedModel):
    """Ergebnis der Berechnungsengine für eine Schicht (Logik folgt in Phase 6)."""

    shift = models.OneToOneField(
        Shift, on_delete=models.CASCADE, related_name="calculation",
        verbose_name=_("Schicht"),
    )

    # Zeiten (Stunden, dezimal)
    total_hours = models.DecimalField(_("Gesamtstunden"), max_digits=6, decimal_places=2, default=Decimal("0"))
    break_hours = models.DecimalField(_("Pausenstunden"), max_digits=6, decimal_places=2, default=Decimal("0"))
    paid_hours = models.DecimalField(_("bezahlte Stunden"), max_digits=6, decimal_places=2, default=Decimal("0"))

    # Zuschlagsstunden je Fenster
    night_hours = models.DecimalField(_("Nachtstunden"), max_digits=6, decimal_places=2, default=Decimal("0"))
    saturday_hours = models.DecimalField(_("Samstagstunden"), max_digits=6, decimal_places=2, default=Decimal("0"))
    sunday_hours = models.DecimalField(_("Sonntagstunden"), max_digits=6, decimal_places=2, default=Decimal("0"))
    holiday_hours = models.DecimalField(_("Feiertagstunden"), max_digits=6, decimal_places=2, default=Decimal("0"))

    is_holiday = models.BooleanField(_("Feiertag"), default=False)
    holiday_name = models.CharField(_("Feiertagsname"), max_length=120, blank=True)

    # Beträge (€), auf Basis des Kundenstundensatzes
    base_amount = models.DecimalField(_("Grundbetrag"), max_digits=10, decimal_places=2, default=Decimal("0"))
    night_amount = models.DecimalField(_("Nachtzuschlag"), max_digits=10, decimal_places=2, default=Decimal("0"))
    saturday_amount = models.DecimalField(_("Samstagzuschlag"), max_digits=10, decimal_places=2, default=Decimal("0"))
    sunday_amount = models.DecimalField(_("Sonntagszuschlag"), max_digits=10, decimal_places=2, default=Decimal("0"))
    holiday_amount = models.DecimalField(_("Feiertagszuschlag"), max_digits=10, decimal_places=2, default=Decimal("0"))
    special_amount = models.DecimalField(_("Spezialzuschläge"), max_digits=10, decimal_places=2, default=Decimal("0"))
    travel_amount = models.DecimalField(_("Fahrkosten"), max_digits=10, decimal_places=2, default=Decimal("0"))

    calculated_at = models.DateTimeField(_("berechnet am"), null=True, blank=True)

    class Meta:
        verbose_name = _("Schichtberechnung")
        verbose_name_plural = _("Schichtberechnungen")

    def __str__(self):
        return f"Berechnung zu {self.shift_id}: {self.paid_hours} Std"

    @property
    def net_total(self) -> Decimal:
        return (
            self.base_amount + self.night_amount + self.saturday_amount
            + self.sunday_amount + self.holiday_amount + self.special_amount
            + self.travel_amount
        )
