from datetime import time
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class Bundesland(models.TextChoices):
    HESSEN = "HE", _("Hessen")
    RHEINLAND_PFALZ = "RP", _("Rheinland-Pfalz")


class InvoiceRhythm(models.TextChoices):
    WEEKLY = "weekly", _("Wöchentlich")
    MONTHLY = "monthly", _("Monatlich")
    FLEXIBLE = "flexible", _("Flexibel")


class Customer(TimeStampedModel):
    """Kunde / Pflegeeinrichtung mit Stammdaten und Einsatzort."""

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.PROTECT,
        related_name="customers", verbose_name=_("Organisation"),
    )
    name = models.CharField(_("Name / Einrichtung"), max_length=200)
    customer_number = models.CharField(_("Kundennummer"), max_length=40, blank=True)
    contact_person = models.CharField(_("Ansprechpartner"), max_length=120, blank=True)

    street = models.CharField(_("Straße"), max_length=200, blank=True)
    zip_code = models.CharField(_("PLZ"), max_length=10, blank=True)
    city = models.CharField(_("Ort"), max_length=120, blank=True)
    bundesland = models.CharField(
        _("Bundesland"), max_length=2, choices=Bundesland.choices,
        help_text=_("Steuert die Feiertagslogik."),
    )

    phone = models.CharField(_("Telefonnummer"), max_length=40, blank=True)
    fax = models.CharField(_("Fax"), max_length=40, blank=True)
    email = models.EmailField(_("E-Mail-Adresse"), blank=True)

    is_active = models.BooleanField(_("aktiv"), default=True)

    class Meta:
        verbose_name = _("Kunde")
        verbose_name_plural = _("Kunden")
        ordering = ("name",)

    def __str__(self):
        return self.name

    @property
    def active_contract(self):
        return self.contracts.filter(is_active=True).order_by("-valid_from").first()


class CustomerContract(TimeStampedModel):
    """Vertrag eines Kunden: Preise, Standard-Zuschläge, Rhythmus, USt.

    Die vier Standard-Zuschläge (Nacht/Samstag/Sonntag/Feiertag) liegen direkt am
    Vertrag, da sie festen Positionen der Rechnung entsprechen. Weitere/abweichende
    Zuschläge werden über SurchargeRule abgebildet.
    """

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="contracts",
        verbose_name=_("Kunde"),
    )
    valid_from = models.DateField(_("gültig ab"))
    is_active = models.BooleanField(_("aktiv"), default=True)

    base_hourly_rate = models.DecimalField(
        _("Kundenstundensatz (€)"), max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        help_text=_("Basis für Grundstunden und prozentuale Zuschläge."),
    )

    # Standard-Zuschläge in Prozent (Faktor = Prozent × Stundensatz)
    night_surcharge_pct = models.DecimalField(
        _("Nachtzuschlag (%)"), max_digits=5, decimal_places=2, default=Decimal("25"),
    )
    saturday_surcharge_pct = models.DecimalField(
        _("Samstagzuschlag (%)"), max_digits=5, decimal_places=2, default=Decimal("25"),
    )
    sunday_surcharge_pct = models.DecimalField(
        _("Sonntagszuschlag (%)"), max_digits=5, decimal_places=2, default=Decimal("50"),
    )
    holiday_surcharge_pct = models.DecimalField(
        _("Feiertagszuschlag (%)"), max_digits=5, decimal_places=2, default=Decimal("100"),
    )

    cumulative_surcharges = models.BooleanField(
        _("Zuschläge kumulieren"), default=True,
        help_text=_("Mehrere Zuschläge auf dieselbe Stunde gleichzeitig zulassen."),
    )

    # Nachtfenster (kundenspezifisch konfigurierbar)
    night_start = models.TimeField(_("Nacht beginnt"), default=time(20, 0))
    night_end = models.TimeField(_("Nacht endet"), default=time(6, 0))

    invoice_rhythm = models.CharField(
        _("Rechnungsrhythmus"), max_length=20, choices=InvoiceRhythm.choices,
        default=InvoiceRhythm.MONTHLY,
    )
    payment_term_days = models.PositiveSmallIntegerField(_("Zahlungsziel (Tage)"), default=14)
    vat_rate = models.DecimalField(
        _("Umsatzsteuersatz (%)"), max_digits=5, decimal_places=2, default=Decimal("19"),
    )

    class Meta:
        verbose_name = _("Vertrag")
        verbose_name_plural = _("Verträge")
        ordering = ("customer", "-valid_from")

    def __str__(self):
        return f"{self.customer} – Vertrag ab {self.valid_from} ({self.base_hourly_rate} €)"


class SurchargeRule(TimeStampedModel):
    """Zusätzlicher / spezieller Zuschlag über die vier Standardzuschläge hinaus."""

    contract = models.ForeignKey(
        CustomerContract, on_delete=models.CASCADE, related_name="surcharge_rules",
        verbose_name=_("Vertrag"),
    )
    label = models.CharField(_("Bezeichnung"), max_length=120)
    percent = models.DecimalField(_("Zuschlag (%)"), max_digits=5, decimal_places=2)
    is_active = models.BooleanField(_("aktiv"), default=True)

    class Meta:
        verbose_name = _("Spezialzuschlag")
        verbose_name_plural = _("Spezialzuschläge")

    def __str__(self):
        return f"{self.label} ({self.percent} %)"


class TravelCostRule(TimeStampedModel):
    """Fahrkostenregel pro Vertrag."""

    contract = models.OneToOneField(
        CustomerContract, on_delete=models.CASCADE, related_name="travel_cost_rule",
        verbose_name=_("Vertrag"),
    )
    enabled = models.BooleanField(_("Fahrkosten aktiv"), default=True)
    rate_per_km = models.DecimalField(
        _("Kilometerpauschale (€/km)"), max_digits=6, decimal_places=2, default=Decimal("0.30"),
    )
    round_trip = models.BooleanField(_("Hin- und Rückfahrt"), default=True)
    min_amount = models.DecimalField(
        _("Mindestpauschale (€)"), max_digits=8, decimal_places=2, null=True, blank=True,
    )
    max_amount = models.DecimalField(
        _("Maximalbetrag (€)"), max_digits=8, decimal_places=2, null=True, blank=True,
    )
    show_on_invoice = models.BooleanField(_("auf Rechnung ausweisen"), default=True)

    class Meta:
        verbose_name = _("Fahrkostenregel")
        verbose_name_plural = _("Fahrkostenregeln")

    def __str__(self):
        return f"Fahrkosten {self.contract.customer} – {self.rate_per_km} €/km"


class TravelDistance(TimeStampedModel):
    """Gespeicherte einfache Entfernung Mitarbeiter ↔ Kunde (MVP, stabil)."""

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="travel_distances", verbose_name=_("Mitarbeiter"),
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="travel_distances",
        verbose_name=_("Kunde"),
    )
    one_way_km = models.DecimalField(
        _("Entfernung einfach (km)"), max_digits=7, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        verbose_name = _("Entfernung")
        verbose_name_plural = _("Entfernungen")
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "customer"], name="unique_employee_customer_distance"
            )
        ]

    def __str__(self):
        return f"{self.employee} → {self.customer}: {self.one_way_km} km"
