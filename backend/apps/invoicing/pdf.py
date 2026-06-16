"""PDF-Erzeugung für Rechnungen (xhtml2pdf, keine nativen Abhängigkeiten)."""

import os
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from xhtml2pdf import pisa


def _company_from_org(org) -> dict:
    """Rechnungskopf aus der Organisation. Kein Rückgriff auf fremde Firmendaten:
    leere Felder bleiben leer, damit niemals fremde Bank-/Steuerdaten erscheinen.
    """
    if org is None:
        return settings.COMPANY
    zip_city = " ".join(p for p in (org.zip_code, org.city) if p).strip()
    logo_path = None
    if org.logo:
        try:
            if os.path.isfile(org.logo.path):
                logo_path = org.logo.path
        except (ValueError, NotImplementedError):
            logo_path = None
    return {
        "name": org.display_legal_name,
        "street": org.street,
        "zip_city": zip_city,
        "phone": org.phone,
        "email": org.email,
        "vat_id": org.vat_id,
        "tax_number": org.tax_number,
        "bank_name": org.bank_name or org.display_legal_name,
        "iban": org.iban,
        "bic": org.bic,
        "logo_path": logo_path,
    }


def _link_callback(uri, rel):
    """Lässt xhtml2pdf lokale Dateipfade (z. B. das Logo) auflösen."""
    if uri and os.path.isfile(uri):
        return uri
    return uri


def _de(value, decimals: int = 2) -> str:
    """Deutsche Zahlenformatierung: 1078.00 -> '1.078,00'."""
    q = Decimal(value).quantize(Decimal("1." + "0" * decimals))
    s = f"{q:,.{decimals}f}"  # 1,078.00
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _date(d) -> str:
    return d.strftime("%d.%m.%Y") if d else ""


def build_context(invoice) -> dict:
    lines = []
    for line in invoice.lines.all().order_by("position"):
        lines.append({
            "no": line.position,
            "desc": line.description,
            "std": _de(line.quantity_hours) if line.quantity_hours is not None else "-",
            "factor": _de(line.factor) if line.factor is not None else "-",
            "betrag": _de(line.amount),
        })
    return {
        "company": _company_from_org(invoice.organization),
        "customer": invoice.customer,
        "invoice": invoice,
        "invoice_date": _date(invoice.invoice_date),
        "period_start": _date(invoice.period_start),
        "period_end": _date(invoice.period_end),
        "due_date": _date(invoice.due_date),
        "lines": lines,
        "subtotal": _de(invoice.subtotal_net),
        "vat_rate": _de(invoice.vat_rate, 0),
        "vat": _de(invoice.vat_amount),
        "gross": _de(invoice.total_gross),
        "is_small_business": invoice.is_small_business,
        "small_business_note": (
            "Gemäß § 19 UStG wird keine Umsatzsteuer berechnet."
        ),
    }


def render_invoice_pdf(invoice) -> bytes:
    html = render_to_string("invoicing/invoice.html", build_context(invoice))
    buffer = BytesIO()
    result = pisa.CreatePDF(src=html, dest=buffer, encoding="utf-8", link_callback=_link_callback)
    if result.err:
        raise RuntimeError("PDF-Erstellung fehlgeschlagen.")
    return buffer.getvalue()


def build_and_store_pdf(invoice) -> bytes:
    """Erzeugt das PDF und speichert es am Invoice.pdf_file. Gibt die Bytes zurück."""
    data = render_invoice_pdf(invoice)
    invoice.pdf_file.save(f"{invoice.number}.pdf", ContentFile(data), save=True)
    return data
