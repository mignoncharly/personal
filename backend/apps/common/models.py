from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """Abstrakte Basis: speichert Erstell- und Änderungszeitpunkt."""

    created_at = models.DateTimeField(_("erstellt am"), auto_now_add=True)
    updated_at = models.DateTimeField(_("geändert am"), auto_now=True)

    class Meta:
        abstract = True


class AuditLog(models.Model):
    """Nachvollziehbarkeit: wer hat was wann geändert (Schichten, Rechnungen, Stammdaten)."""

    class Action(models.TextChoices):
        CREATE = "create", _("Erstellt")
        UPDATE = "update", _("Geändert")
        DELETE = "delete", _("Gelöscht")
        SUBMIT = "submit", _("Eingereicht")
        APPROVE = "approve", _("Freigegeben")
        REJECT = "reject", _("Abgelehnt")
        INVOICE = "invoice", _("Abgerechnet")

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_entries",
        verbose_name=_("Akteur"),
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="audit_entries",
        verbose_name=_("Organisation"),
    )
    action = models.CharField(_("Aktion"), max_length=20, choices=Action.choices)
    entity_type = models.CharField(_("Objekttyp"), max_length=80)
    entity_id = models.CharField(_("Objekt-ID"), max_length=40, blank=True)
    summary = models.CharField(_("Zusammenfassung"), max_length=255, blank=True)
    changes = models.JSONField(_("Änderungen"), default=dict, blank=True)
    created_at = models.DateTimeField(_("Zeitpunkt"), auto_now_add=True)

    class Meta:
        verbose_name = _("Audit-Eintrag")
        verbose_name_plural = _("Audit-Log")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.action} {self.entity_type}#{self.entity_id}"
