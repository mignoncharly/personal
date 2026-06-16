from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class Organization(TimeStampedModel):
    """Mandant: eine Pflegefirma, die die Plattform nutzt.

    Jede Organisation ist vollständig von den anderen isoliert. Kunden, Schichten,
    Rechnungen und Benutzer gehören jeweils genau zu einer Organisation. Die hier
    gespeicherte Firmenidentität (Adresse, USt-IdNr., Bankverbindung, Logo) erscheint
    auf den Rechnungen dieser Organisation.
    """

    # Identität
    name = models.CharField(_("Name"), max_length=200)
    slug = models.SlugField(_("Kürzel"), max_length=60, unique=True)
    is_active = models.BooleanField(_("aktiv"), default=True)

    # Firmen-/Rechnungsidentität (erscheint auf der Rechnung)
    legal_name = models.CharField(
        _("Firmenname (rechtlich)"), max_length=200, blank=True,
        help_text=_("Vollständiger Firmenname für den Rechnungskopf. Fällt auf 'Name' zurück, wenn leer."),
    )
    street = models.CharField(_("Straße"), max_length=200, blank=True)
    zip_code = models.CharField(_("PLZ"), max_length=10, blank=True)
    city = models.CharField(_("Ort"), max_length=120, blank=True)
    phone = models.CharField(_("Telefonnummer"), max_length=40, blank=True)
    email = models.EmailField(_("E-Mail-Adresse"), blank=True)

    vat_id = models.CharField(_("USt-IdNr."), max_length=30, blank=True)
    tax_number = models.CharField(_("Steuernummer"), max_length=30, blank=True)

    is_small_business = models.BooleanField(
        _("Kleinunternehmer (§ 19 UStG)"), default=False,
        help_text=_(
            "Wenn aktiviert, wird auf Rechnungen keine Umsatzsteuer ausgewiesen "
            "und der gesetzliche Hinweis nach § 19 UStG aufgedruckt."
        ),
    )

    bank_name = models.CharField(_("Bank"), max_length=120, blank=True)
    iban = models.CharField(_("IBAN"), max_length=40, blank=True)
    bic = models.CharField(_("BIC"), max_length=20, blank=True)

    logo = models.ImageField(
        _("Logo"), upload_to="org_logos/", null=True, blank=True,
        help_text=_("Wird im Rechnungskopf angezeigt."),
    )

    # Rechnungsnummerierung – pro Organisation eigener, fortlaufender Zähler
    invoice_number_prefix = models.CharField(
        _("Rechnungsnummern-Präfix"), max_length=12, default="RECH",
    )
    invoice_sequence_counter = models.PositiveIntegerField(
        _("aktueller Rechnungszähler"), default=0,
        validators=[MinValueValidator(0)],
        help_text=_("Letzte vergebene laufende Nummer dieser Organisation."),
    )

    class Meta:
        verbose_name = _("Organisation")
        verbose_name_plural = _("Organisationen")
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:60]
        super().save(*args, **kwargs)

    @property
    def display_legal_name(self) -> str:
        """Name für den Rechnungskopf: rechtlicher Firmenname, sonst der Anzeigename."""
        return self.legal_name or self.name
