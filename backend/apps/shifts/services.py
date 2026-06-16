"""Berechnungsengine für Schichten.

Ableitung der Regeln aus dem Konzept (`/concept`):

* Schichten über Mitternacht werden minutengenau in Zeitfenster zerlegt.
* Die Pause wird **einmal** abgezogen, und zwar aus den am höchsten bezuschlagten
  Minuten zuerst – so werden Zuschläge nicht künstlich erhöht (Beispiel `image1`:
  20:30–06:30, 1 h Pause → Nacht 8,5 h statt 9,5 h).
* Zuschläge sind **kumulativ** und werden auf den **Kundenstundensatz** berechnet
  (Faktor = Prozent × Stundensatz). Eine Stunde, die gleichzeitig Nacht und Sonntag
  ist, erhält beide Zuschläge (schriftliche Spec: 49 + 12,25 + 24,50 = 85,75).
* Feiertage werden je Bundesland (HE/RLP) über die `holidays`-Bibliothek erkannt.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

import holidays as holidays_lib

CENT = Decimal("0.01")
HUNDRED = Decimal("100")
MINUTES_PER_HOUR = Decimal("60")

_holiday_cache: dict[tuple[str, int], object] = {}


def get_holidays(bundesland: str, year: int):
    key = (bundesland, year)
    if key not in _holiday_cache:
        _holiday_cache[key] = holidays_lib.country_holidays(
            "DE", subdiv=bundesland, years=year
        )
    return _holiday_cache[key]


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _hours(minutes: int) -> Decimal:
    return (Decimal(minutes) / MINUTES_PER_HOUR).quantize(CENT, rounding=ROUND_HALF_UP)


def _is_night(t: time, night_start: time, night_end: time) -> bool:
    if night_start == night_end:
        return False
    if night_start < night_end:
        return night_start <= t < night_end
    # Fenster über Mitternacht (z. B. 20:00–06:00)
    return t >= night_start or t < night_end


def calculate_shift_values(
    *,
    date,
    start_time: time,
    end_time: time,
    break_minutes: int,
    base_rate: Decimal,
    night_pct: Decimal,
    sat_pct: Decimal,
    sun_pct: Decimal,
    hol_pct: Decimal,
    night_start: time,
    night_end: time,
    bundesland: str,
    cumulative: bool = True,
    special_pcts: list[Decimal] | None = None,
    travel_amount: Decimal = Decimal("0"),
) -> dict:
    """Reine Berechnung ohne DB-Zugriff. Gibt Stunden und Beträge (gerundet) zurück."""

    base_rate = Decimal(base_rate)
    start_dt = datetime.combine(date, start_time)
    end_dt = datetime.combine(date, end_time)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)  # Schicht über Mitternacht

    total_minutes = int((end_dt - start_dt).total_seconds() // 60)

    # Jede Minute klassifizieren
    flags: list[tuple[Decimal, bool, bool, bool, bool]] = []
    holiday_name = ""
    for i in range(total_minutes):
        m_dt = start_dt + timedelta(minutes=i)
        t, d, wd = m_dt.time(), m_dt.date(), m_dt.weekday()
        is_night = _is_night(t, night_start, night_end)
        is_sat = wd == 5
        is_sun = wd == 6
        hols = get_holidays(bundesland, d.year)
        is_hol = d in hols
        if is_hol and not holiday_name:
            holiday_name = str(hols.get(d, ""))

        if cumulative:
            pct = Decimal(0)
            if is_night:
                pct += night_pct
            if is_sat:
                pct += sat_pct
            if is_sun:
                pct += sun_pct
            if is_hol:
                pct += hol_pct
            flags.append((pct, is_night, is_sat, is_sun, is_hol))
        else:
            # Nicht kumulativ: nur der höchste Einzelzuschlag zählt
            candidates = []
            if is_hol:
                candidates.append((hol_pct, "hol"))
            if is_sun:
                candidates.append((sun_pct, "sun"))
            if is_sat:
                candidates.append((sat_pct, "sat"))
            if is_night:
                candidates.append((night_pct, "night"))
            if candidates:
                best_pct, kind = max(candidates, key=lambda c: c[0])
                flags.append((
                    best_pct, kind == "night", kind == "sat", kind == "sun", kind == "hol",
                ))
            else:
                flags.append((Decimal(0), False, False, False, False))

    # Pause aus den am höchsten bezuschlagten Minuten zuerst abziehen
    break_min = max(0, min(int(break_minutes), total_minutes))
    order = sorted(range(total_minutes), key=lambda i: flags[i][0], reverse=True)
    unpaid = set(order[:break_min])

    paid_min = night_min = sat_min = sun_min = hol_min = 0
    for i in range(total_minutes):
        if i in unpaid:
            continue
        _, is_night, is_sat, is_sun, is_hol = flags[i]
        paid_min += 1
        night_min += is_night
        sat_min += is_sat
        sun_min += is_sun
        hol_min += is_hol

    paid_h = _hours(paid_min)
    night_h = _hours(night_min)
    sat_h = _hours(sat_min)
    sun_h = _hours(sun_min)
    hol_h = _hours(hol_min)
    break_h = _hours(break_min)
    total_h = _hours(total_minutes)

    def factor(pct: Decimal) -> Decimal:
        return base_rate * (Decimal(pct) / HUNDRED)

    base_amount = _money(base_rate * paid_h)
    night_amount = _money(factor(night_pct) * night_h)
    sat_amount = _money(factor(sat_pct) * sat_h)
    sun_amount = _money(factor(sun_pct) * sun_h)
    hol_amount = _money(factor(hol_pct) * hol_h)

    special_amount = Decimal("0")
    for sp in special_pcts or []:
        special_amount += factor(sp) * paid_h
    special_amount = _money(special_amount)

    travel_amount = _money(Decimal(travel_amount))

    return {
        "total_hours": total_h,
        "break_hours": break_h,
        "paid_hours": paid_h,
        "night_hours": night_h,
        "saturday_hours": sat_h,
        "sunday_hours": sun_h,
        "holiday_hours": hol_h,
        "is_holiday": hol_min > 0,
        "holiday_name": holiday_name,
        "base_amount": base_amount,
        "night_amount": night_amount,
        "saturday_amount": sat_amount,
        "sunday_amount": sun_amount,
        "holiday_amount": hol_amount,
        "special_amount": special_amount,
        "travel_amount": travel_amount,
    }


def compute_travel_amount(shift, contract) -> Decimal:
    """Fahrkosten für eine Schicht anhand Fahrkostenregel + gespeicherter Entfernung."""
    from apps.customers.models import TravelDistance

    rule = getattr(contract, "travel_cost_rule", None)
    if rule is None or not rule.enabled:
        return Decimal("0")
    dist = TravelDistance.objects.filter(
        employee=shift.employee, customer=shift.customer
    ).first()
    if dist is None:
        return Decimal("0")
    km = dist.one_way_km * (Decimal("2") if rule.round_trip else Decimal("1"))
    amount = km * rule.rate_per_km
    if rule.min_amount is not None and amount < rule.min_amount:
        amount = rule.min_amount
    if rule.max_amount is not None and amount > rule.max_amount:
        amount = rule.max_amount
    return Decimal(amount)


def recalculate_shift(shift):
    """Berechnet eine Schicht anhand des aktiven Kundenvertrags und speichert das Ergebnis."""
    from django.utils import timezone

    from .models import ShiftCalculation

    contract = shift.customer.active_contract
    if contract is None:
        raise ValueError("Kein aktiver Vertrag für diesen Kunden hinterlegt.")

    travel = compute_travel_amount(shift, contract)
    specials = [r.percent for r in contract.surcharge_rules.filter(is_active=True)]

    values = calculate_shift_values(
        date=shift.date,
        start_time=shift.start_time,
        end_time=shift.end_time,
        break_minutes=shift.break_minutes,
        base_rate=contract.base_hourly_rate,
        night_pct=contract.night_surcharge_pct,
        sat_pct=contract.saturday_surcharge_pct,
        sun_pct=contract.sunday_surcharge_pct,
        hol_pct=contract.holiday_surcharge_pct,
        night_start=contract.night_start,
        night_end=contract.night_end,
        bundesland=shift.customer.bundesland,
        cumulative=contract.cumulative_surcharges,
        special_pcts=specials,
        travel_amount=travel,
    )
    values["calculated_at"] = timezone.now()
    calc, _ = ShiftCalculation.objects.update_or_create(shift=shift, defaults=values)
    return calc
