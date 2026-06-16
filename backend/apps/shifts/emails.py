"""Benachrichtigungen an Mitarbeiter bei Freigabe/Ablehnung ihrer Schichten.

Der Versand ist „best effort": Schlägt er fehl, wird eine Warnung geloggt, der
Freigabe-/Ablehnungsvorgang läuft aber trotzdem erfolgreich durch.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _notify(shift, *, subject, message, kind):
    recipient = (getattr(shift.employee, "email", "") or "").strip()
    if not recipient:
        return
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception:
        logger.warning(
            "%s-Benachrichtigung zu Schicht %s an %s fehlgeschlagen.",
            kind, shift.id, recipient, exc_info=True,
        )


def send_shift_approved_email(shift):
    org_name = shift.organization.name if shift.organization_id else "Mouvin Personal"
    _notify(
        shift,
        subject=f"Schicht freigegeben – {shift.date:%d.%m.%Y}",
        message=(
            f"Hallo {shift.employee.get_full_name() or ''},\n\n"
            f"Ihre Schicht am {shift.date:%d.%m.%Y} bei {shift.customer.name} wurde "
            "freigegeben und abgerechnet.\n\n"
            f"{org_name}\n"
        ),
        kind="Freigabe",
    )


def send_shift_rejected_email(shift, reason: str):
    org_name = shift.organization.name if shift.organization_id else "Mouvin Personal"
    _notify(
        shift,
        subject=f"Schicht abgelehnt – {shift.date:%d.%m.%Y}",
        message=(
            f"Hallo {shift.employee.get_full_name() or ''},\n\n"
            f"Ihre Schicht am {shift.date:%d.%m.%Y} bei {shift.customer.name} wurde "
            "abgelehnt.\n\n"
            f"Grund: {reason}\n\n"
            "Bitte korrigieren Sie die Schicht und reichen Sie sie erneut ein.\n\n"
            f"{org_name}\n"
        ),
        kind="Ablehnung",
    )
