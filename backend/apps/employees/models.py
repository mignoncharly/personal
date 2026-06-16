from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import TimeStampedModel


class EmployeeProfile(TimeStampedModel):
    """Profil einer Pflegekraft (1:1 zum User)."""

    class Qualification(models.TextChoices):
        HELPER = "pflegehilfskraft", _("Pflegehilfskraft")
        SPECIALIST = "pflegefachkraft", _("Pflegefachkraft")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="employee_profile", verbose_name=_("Benutzer"),
    )
    qualification = models.CharField(
        _("Qualifikation"), max_length=20, choices=Qualification.choices,
        default=Qualification.HELPER,
    )

    street = models.CharField(_("Straße"), max_length=200, blank=True)
    zip_code = models.CharField(_("PLZ"), max_length=10, blank=True)
    city = models.CharField(_("Wohnort"), max_length=120, blank=True)

    is_active = models.BooleanField(_("aktiv"), default=True)

    class Meta:
        verbose_name = _("Mitarbeiterprofil")
        verbose_name_plural = _("Mitarbeiterprofile")
        ordering = ("user__last_name", "user__first_name")

    def __str__(self):
        full = self.user.get_full_name()
        return full or self.user.email
