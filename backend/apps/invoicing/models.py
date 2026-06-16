from decimal import Decimal

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel
from apps.customers.models import Customer


def invoice_pdf_storage():
    """Eigener Speicher für Rechnungs-PDFs (getrennt von media)."""
    return FileSystemStorage(location=str(settings.INVOICE_ROOT), base_url=settings.INVOICE_URL)


class Invoice(TimeStampedModel):
    """Rechnung pro Kunde und Leistungszeitraum (Nr.-Format RECH-{seq}-{YYYYMMDD})."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Entwurf")
        FINALIZED = "finalized", _("Festgeschrieben")
        SENT = "sent", _("Versendet")
        PAID = "paid", _("Bezahlt")
        CANCELLED = "cancelled", _("Storniert")

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.PROTECT,
        related_name="invoices", verbose_name=_("Organisation"),
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="invoices",
        verbose_name=_("Kunde"),
    )
    number = models.CharField(_("Rechnungsnummer"), max_length=40)
    sequence = models.PositiveIntegerField(_("laufende Nummer"))
    invoice_date = models.DateField(_("Rechnungsdatum"))
    period_start = models.DateField(_("Leistungszeitraum von"))
    period_end = models.DateField(_("Leistungszeitraum bis"))

    status = models.CharField(
        _("Status"), max_length=12, choices=Status.choices, default=Status.DRAFT,
    )
    sent_at = models.DateTimeField(_("versendet am"), null=True, blank=True)
    paid_at = models.DateTimeField(_("bezahlt am"), null=True, blank=True)
    last_reminded_at = models.DateTimeField(_("zuletzt gemahnt am"), null=True, blank=True)

    subtotal_net = models.DecimalField(_("Zwischensumme netto"), max_digits=12, decimal_places=2, default=Decimal("0"))
    vat_rate = models.DecimalField(_("USt-Satz (%)"), max_digits=5, decimal_places=2, default=Decimal("19"))
    vat_amount = models.DecimalField(_("USt-Betrag"), max_digits=12, decimal_places=2, default=Decimal("0"))
    is_small_business = models.BooleanField(
        _("Kleinunternehmer (§ 19 UStG)"), default=False,
        help_text=_("Zum Zeitpunkt der Abrechnung übernommener Kleinunternehmer-Status."),
    )
    total_gross = models.DecimalField(_("Gesamtbetrag brutto"), max_digits=12, decimal_places=2, default=Decimal("0"))

    payment_term_days = models.PositiveSmallIntegerField(_("Zahlungsziel (Tage)"), default=14)

    pdf_file = models.FileField(
        _("PDF"), upload_to="", storage=invoice_pdf_storage, null=True, blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="created_invoices", verbose_name=_("erstellt von"),
    )

    class Meta:
        verbose_name = _("Rechnung")
        verbose_name_plural = _("Rechnungen")
        ordering = ("-invoice_date", "-sequence")
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "number"], name="unique_org_invoice_number",
            ),
            models.UniqueConstraint(
                fields=["organization", "sequence"], name="unique_org_invoice_sequence",
            ),
        ]

    def __str__(self):
        return f"{self.number} – {self.customer}"

    @property
    def due_date(self):
        from datetime import timedelta
        return self.invoice_date + timedelta(days=self.payment_term_days)

    @property
    def is_overdue(self) -> bool:
        """Offen (festgeschrieben/versendet) und Fälligkeitsdatum überschritten."""
        from datetime import date as date_cls
        if self.status not in (self.Status.FINALIZED, self.Status.SENT):
            return False
        return self.due_date < date_cls.today()


class InvoiceLine(models.Model):
    """Rechnungsposition. Typen entsprechen den festen Positionen 1–6 der Vorlage."""

    class LineType(models.TextChoices):
        BASE_HOURS = "base_hours", _("Netto Stunden ohne Pausen")
        NIGHT = "night", _("Nachtarbeit Zuschlag")
        SATURDAY = "saturday", _("Samstag Zuschlag")
        SUNDAY = "sunday", _("Sonntag Zuschlag")
        HOLIDAY = "holiday", _("Feiertag Zuschlag")
        SPECIAL = "special", _("Spezialzuschlag")
        TRAVEL = "travel", _("Fahrkosten")

    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="lines", verbose_name=_("Rechnung"),
    )
    position = models.PositiveSmallIntegerField(_("Position"))
    line_type = models.CharField(_("Typ"), max_length=12, choices=LineType.choices)
    description = models.CharField(_("Bezeichnung"), max_length=200)

    quantity_hours = models.DecimalField(
        _("Bezahlt (Std.)"), max_digits=8, decimal_places=2, null=True, blank=True,
    )
    factor = models.DecimalField(
        _("Faktor (€)"), max_digits=10, decimal_places=2, null=True, blank=True,
    )
    amount = models.DecimalField(_("Betrag (€)"), max_digits=12, decimal_places=2, default=Decimal("0"))

    class Meta:
        verbose_name = _("Rechnungsposition")
        verbose_name_plural = _("Rechnungspositionen")
        ordering = ("invoice", "position")

    def __str__(self):
        return f"{self.position}. {self.description}: {self.amount} €"
