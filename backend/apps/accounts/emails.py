"""Versand von Konto-E-Mails (Einladung, Passwort-Reset).

Beide Flows nutzen denselben Token-Mechanismus (``default_token_generator``)
und dieselbe Frontend-Seite ``/passwort-reset?uid=…&token=…``: Der Eingeladene
legt darüber sein erstes Passwort fest.
"""

import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

logger = logging.getLogger(__name__)


def _send(*, subject, message, recipient, kind):
    """E-Mail versenden, ohne den aufrufenden Flow zu unterbrechen.

    Schlägt der Versand fehl, wird eine Warnung geloggt (statt den Fehler
    stillschweigend zu verschlucken); Mitarbeiter-Anlage bzw. Reset-Anfrage
    laufen trotzdem erfolgreich durch.
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception:
        logger.warning("%s-E-Mail an %s konnte nicht versendet werden.", kind, recipient, exc_info=True)


def make_token(user) -> dict:
    """uid/token-Paar für den Passwort-Reset-Link erzeugen."""
    return {
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": default_token_generator.make_token(user),
    }


def frontend_origin(request=None) -> str:
    """Basis-URL des Frontends.

    Bevorzugt den Origin-Header der Anfrage (gleiche Domain wie der aufrufende
    Admin), fällt sonst auf ``settings.FRONTEND_BASE_URL`` zurück.
    """
    if request is not None:
        origin = request.headers.get("Origin")
        if origin:
            return origin.rstrip("/")
    return (settings.FRONTEND_BASE_URL or "").rstrip("/")


def _reset_link(origin: str, tokens: dict) -> str:
    return f"{origin}/passwort-reset?uid={tokens['uid']}&token={tokens['token']}"


def send_password_reset_email(user, request=None) -> None:
    """E-Mail zum Zurücksetzen des Passworts an einen bestehenden Nutzer."""
    tokens = make_token(user)
    link = _reset_link(frontend_origin(request), tokens)
    _send(
        subject="Passwort zurücksetzen – Mouvin Personal",
        message=(
            "Sie haben das Zurücksetzen Ihres Passworts angefordert.\n\n"
            f"UID: {tokens['uid']}\nToken: {tokens['token']}\n\n"
            f"Link: {link}\n\n"
            "Falls Sie das nicht waren, ignorieren Sie diese E-Mail."
        ),
        recipient=user.email,
        kind="Passwort-Reset",
    )


def send_invite_email(user, request=None) -> None:
    """Einladungs-E-Mail an einen neu angelegten Mitarbeiter.

    Lädt den Nutzer ein, über den Passwort-Reset-Link sein erstes Passwort zu
    setzen und sich anzumelden.
    """
    org_name = user.organization.name if user.organization_id else "Mouvin Personal"
    greeting_name = user.get_full_name() or user.email
    tokens = make_token(user)
    link = _reset_link(frontend_origin(request), tokens)
    _send(
        subject=f"Willkommen bei {org_name} – Zugang aktivieren",
        message=(
            f"Hallo {greeting_name},\n\n"
            f"für Sie wurde ein Zugang bei {org_name} (Mouvin Personal) angelegt.\n"
            "Bitte legen Sie über den folgenden Link Ihr Passwort fest, um sich "
            "anzumelden:\n\n"
            f"{link}\n\n"
            "Aus Sicherheitsgründen ist dieser Link nur begrenzt gültig. Sollte er "
            "abgelaufen sein, können Sie auf der Anmeldeseite jederzeit ein neues "
            "Passwort anfordern.\n\n"
            f"Ihr Login ist Ihre E-Mail-Adresse: {user.email}\n"
        ),
        recipient=user.email,
        kind="Einladungs",
    )
