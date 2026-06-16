"""Erzeugung von Rechnungen aus freigegebenen Schichten."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction

from apps.common.audit import log_action
from apps.common.models import AuditLog
from apps.organizations.models import Organization
from apps.shifts.models import Shift
from apps.shifts.services import recalculate_shift

from .models import Invoice, InvoiceLine

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


def _money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def _pct_label(pct: Decimal) -> str:
    pct = Decimal(pct)
    text = f"{pct.normalize():f}"
    return text.rstrip(".") if "." in text else text


def next_sequence(organization) -> int:
    """Vergibt atomar die nächste laufende Rechnungsnummer der Organisation.

    Muss innerhalb einer Transaktion laufen (select_for_update sperrt die Zeile),
    damit parallele Abrechnungen keine doppelten Nummern erzeugen.
    """
    locked = Organization.objects.select_for_update().get(pk=organization.pk)
    locked.invoice_sequence_counter += 1
    locked.save(update_fields=["invoice_sequence_counter", "updated_at"])
    return locked.invoice_sequence_counter


def collect_invoice_preview(*, customer, period_start, period_end):
    """Berechnet eine Vorschau für die abrechenbaren Schichten ohne Rechnung anzulegen."""
    contract = customer.active_contract
    if contract is None:
        raise ValueError("Kein aktiver Vertrag für diesen Kunden hinterlegt.")

    shifts = list(
        Shift.objects.select_related("calculation").filter(
            customer=customer,
            status=Shift.Status.APPROVED,
            invoice__isnull=True,
            date__gte=period_start,
            date__lte=period_end,
        )
    )

    keys = [
        "base_h", "night_h", "sat_h", "sun_h", "hol_h",
        "base_a", "night_a", "sat_a", "sun_a", "hol_a", "special_a", "travel_a",
    ]
    acc = {k: Decimal("0") for k in keys}

    for s in shifts:
        calc = getattr(s, "calculation", None) or recalculate_shift(s)
        acc["base_h"] += calc.paid_hours
        acc["night_h"] += calc.night_hours
        acc["sat_h"] += calc.saturday_hours
        acc["sun_h"] += calc.sunday_hours
        acc["hol_h"] += calc.holiday_hours
        acc["base_a"] += calc.base_amount
        acc["night_a"] += calc.night_amount
        acc["sat_a"] += calc.saturday_amount
        acc["sun_a"] += calc.sunday_amount
        acc["hol_a"] += calc.holiday_amount
        acc["special_a"] += calc.special_amount
        acc["travel_a"] += calc.travel_amount

    org = customer.organization
    is_small_business = org.is_small_business
    vat_rate = Decimal("0") if is_small_business else contract.vat_rate
    subtotal = _money(sum((acc[key] for key in (
        "base_a", "night_a", "sat_a", "sun_a", "hol_a", "special_a", "travel_a",
    )), Decimal("0")))
    vat = _money(subtotal * vat_rate / HUNDRED)
    return {
        "customer": customer.id,
        "customer_name": customer.name,
        "period_start": period_start,
        "period_end": period_end,
        "shift_count": len(shifts),
        "paid_hours": _money(acc["base_h"]),
        "subtotal_net": subtotal,
        "vat_rate": vat_rate,
        "vat_amount": vat,
        "total_gross": _money(subtotal + vat),
        "is_small_business": is_small_business,
    }, contract, shifts, acc


@transaction.atomic
def generate_invoice(*, customer, period_start, period_end, invoice_date, user):
    """Erzeugt eine Rechnung für alle freigegebenen, nicht abgerechneten Schichten
    eines Kunden im angegebenen Zeitraum.
    """
    preview, contract, shifts, acc = collect_invoice_preview(
        customer=customer, period_start=period_start, period_end=period_end,
    )
    if not shifts:
        raise ValueError(
            "Keine abrechenbaren (freigegebenen, nicht abgerechneten) Schichten im Zeitraum."
        )

    rate = contract.base_hourly_rate

    def factor(pct: Decimal) -> Decimal:
        return _money(rate * (Decimal(pct) / HUNDRED))

    org = customer.organization
    sequence = next_sequence(org)
    # Kleinunternehmer (§ 19 UStG): keine USt ausweisen, unabhängig vom Vertragssatz.
    is_small_business = preview["is_small_business"]
    vat_rate = preview["vat_rate"]
    invoice = Invoice.objects.create(
        organization=org,
        customer=customer,
        number=f"{org.invoice_number_prefix}-{sequence}-{invoice_date:%Y%m%d}",
        sequence=sequence,
        invoice_date=invoice_date,
        period_start=period_start,
        period_end=period_end,
        vat_rate=vat_rate,
        is_small_business=is_small_business,
        payment_term_days=contract.payment_term_days,
        created_by=user if getattr(user, "is_authenticated", False) else None,
    )

    LT = InvoiceLine.LineType
    rows = [
        (LT.BASE_HOURS, "Netto Stunden ohne Pausen", acc["base_h"], rate, acc["base_a"]),
        (LT.NIGHT, f"Nachtarbeit Zuschlag {_pct_label(contract.night_surcharge_pct)}%",
         acc["night_h"], factor(contract.night_surcharge_pct), acc["night_a"]),
        (LT.SATURDAY, f"Samstag Zuschlag {_pct_label(contract.saturday_surcharge_pct)}%",
         acc["sat_h"], factor(contract.saturday_surcharge_pct), acc["sat_a"]),
        (LT.SUNDAY, f"Sonntag Zuschlag {_pct_label(contract.sunday_surcharge_pct)}%",
         acc["sun_h"], factor(contract.sunday_surcharge_pct), acc["sun_a"]),
        (LT.HOLIDAY, f"Feiertag Zuschlag {_pct_label(contract.holiday_surcharge_pct)}%",
         acc["hol_h"], factor(contract.holiday_surcharge_pct), acc["hol_a"]),
    ]
    if acc["special_a"] > 0:
        rows.append((LT.SPECIAL, "Spezialzuschlag", None, None, acc["special_a"]))
    rows.append((LT.TRAVEL, "Fahrkosten", None, None, acc["travel_a"]))

    lines = []
    for position, (line_type, desc, qty, fac, amount) in enumerate(rows, start=1):
        lines.append(InvoiceLine(
            invoice=invoice, position=position, line_type=line_type, description=desc,
            quantity_hours=(None if qty is None else _money(qty)),
            factor=(None if fac is None else _money(fac)),
            amount=_money(amount),
        ))
    InvoiceLine.objects.bulk_create(lines)

    invoice.subtotal_net = preview["subtotal_net"]
    invoice.vat_amount = preview["vat_amount"]
    invoice.total_gross = preview["total_gross"]
    invoice.save(update_fields=["subtotal_net", "vat_amount", "total_gross"])

    for s in shifts:
        s.invoice = invoice
        s.status = Shift.Status.INVOICED
        s.save(update_fields=["invoice", "status", "updated_at"])
        log_action(user, AuditLog.Action.INVOICE, s, summary=f"Abgerechnet in {invoice.number}")

    log_action(user, AuditLog.Action.CREATE, invoice,
               summary=f"Rechnung {invoice.number} über {len(shifts)} Schichten")
    return invoice


def release_invoice_shifts(invoice):
    """Setzt die Schichten einer (Entwurfs-)Rechnung zurück auf freigegeben."""
    for s in invoice.shifts.all():
        s.invoice = None
        s.status = Shift.Status.APPROVED
        s.save(update_fields=["invoice", "status", "updated_at"])
