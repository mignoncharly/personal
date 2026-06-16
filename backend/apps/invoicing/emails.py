"""Versand von Rechnungen per E-Mail (PDF im Anhang)."""

import logging

from django.conf import settings
from django.core.mail import EmailMessage

from .pdf import build_and_store_pdf

logger = logging.getLogger(__name__)


def _build_email(invoice, *, subject, body, pdf_bytes):
    org = invoice.organization
    bcc = [org.email] if org and org.email else []
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[(invoice.customer.email or "").strip()],
        bcc=bcc,
    )
    email.attach(f"{invoice.number}.pdf", pdf_bytes, "application/pdf")
    return email


def _require_customer_email(invoice) -> str:
    recipient = (invoice.customer.email or "").strip()
    if not recipient:
        raise ValueError(
            "Für diesen Kunden ist keine E-Mail-Adresse hinterlegt. "
            "Bitte zuerst eine Adresse beim Kunden eintragen."
        )
    return recipient


def send_reminder_email(invoice) -> str:
    """Sendet eine Zahlungserinnerung (mit PDF) an den Kunden; BCC an die Organisation."""
    recipient = _require_customer_email(invoice)
    pdf_bytes = build_and_store_pdf(invoice)

    org = invoice.organization
    org_name = org.name if org else "Mouvin Personal"
    body = (
        "Sehr geehrte Damen und Herren,\n\n"
        f"unsere Rechnung {invoice.number} vom {invoice.invoice_date:%d.%m.%Y} über "
        f"{invoice.total_gross:.2f} € war am {invoice.due_date:%d.%m.%Y} zur Zahlung "
        "fällig und ist nach unseren Unterlagen noch offen.\n\n"
        "Wir möchten Sie höflich an den Ausgleich erinnern. Sollte sich Ihre Zahlung "
        "mit dieser E-Mail überschnitten haben, betrachten Sie diese Erinnerung bitte "
        "als gegenstandslos.\n\n"
        f"Mit freundlichen Grüßen\n{org_name}\n"
    )
    email = _build_email(
        invoice,
        subject=f"Zahlungserinnerung zu Rechnung {invoice.number} – {org_name}",
        body=body,
        pdf_bytes=pdf_bytes,
    )
    email.send(fail_silently=False)
    logger.info("Zahlungserinnerung zu %s an %s versendet.", invoice.number, recipient)
    return recipient


def send_invoice_email(invoice) -> str:
    """Sendet die Rechnung als PDF an die E-Mail-Adresse des Kunden.

    Eine Kopie geht per BCC an die Organisation (falls hinterlegt). Erzeugt das
    PDF frisch und speichert es am Invoice. Gibt die Empfängeradresse zurück.

    Wirft ``ValueError`` bei fehlender Kundenadresse und propagiert Versandfehler
    (der Aufrufer übersetzt sie in eine Fehlermeldung für den Nutzer).
    """
    recipient = (invoice.customer.email or "").strip()
    if not recipient:
        raise ValueError(
            "Für diesen Kunden ist keine E-Mail-Adresse hinterlegt. "
            "Bitte zuerst eine Adresse beim Kunden eintragen."
        )

    pdf_bytes = build_and_store_pdf(invoice)

    org = invoice.organization
    org_name = org.name if org else "Mouvin Personal"
    bcc = [org.email] if org and org.email else []

    period = f"{invoice.period_start:%d.%m.%Y} – {invoice.period_end:%d.%m.%Y}"
    body = (
        f"Sehr geehrte Damen und Herren,\n\n"
        f"anbei erhalten Sie die Rechnung {invoice.number} "
        f"für den Leistungszeitraum {period}.\n\n"
        f"Rechnungsbetrag: {invoice.total_gross:.2f} € brutto\n"
        f"Zahlbar bis: {invoice.due_date:%d.%m.%Y}\n\n"
        f"Mit freundlichen Grüßen\n{org_name}\n"
    )

    email = EmailMessage(
        subject=f"Rechnung {invoice.number} – {org_name}",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
        bcc=bcc,
    )
    email.attach(f"{invoice.number}.pdf", pdf_bytes, "application/pdf")
    email.send(fail_silently=False)
    logger.info("Rechnung %s an %s versendet.", invoice.number, recipient)
    return recipient
