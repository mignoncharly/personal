"""Smoke-Test Phase 2: legt verbundene Objekte an und prüft Beziehungen/Properties."""
from datetime import date, time
from decimal import Decimal

from django.contrib.auth import get_user_model

from apps.customers.models import (
    Bundesland, Customer, CustomerContract, InvoiceRhythm,
    SurchargeRule, TravelCostRule, TravelDistance,
)
from apps.employees.models import EmployeeProfile
from apps.invoicing.models import Invoice, InvoiceLine
from apps.shifts.models import Shift, ShiftCalculation

User = get_user_model()

# Aufräumen evtl. vorhandener Testdaten
Customer.objects.filter(name="SMOKE Testkunde").delete()
User.objects.filter(email="smoke.employee@example.com").delete()

emp = User.objects.create_user(
    email="smoke.employee@example.com", password="x", first_name="Test", last_name="Kraft",
)
EmployeeProfile.objects.create(
    user=emp, qualification=EmployeeProfile.Qualification.SPECIALIST, city="Mainz",
)

cust = Customer.objects.create(
    name="SMOKE Testkunde", bundesland=Bundesland.HESSEN, city="Wiesbaden",
)
contract = CustomerContract.objects.create(
    customer=cust, valid_from=date(2025, 1, 1),
    base_hourly_rate=Decimal("49.00"), invoice_rhythm=InvoiceRhythm.MONTHLY,
)
SurchargeRule.objects.create(contract=contract, label="Sonderaufschlag", percent=Decimal("10"))
TravelCostRule.objects.create(contract=contract, rate_per_km=Decimal("0.30"))
TravelDistance.objects.create(employee=emp, customer=cust, one_way_km=Decimal("15"))

shift = Shift.objects.create(
    employee=emp, customer=cust, shift_type=Shift.ShiftType.NIGHT,
    date=date(2025, 9, 1), start_time=time(20, 30), end_time=time(6, 30),
    break_minutes=60, created_by=emp,
)
ShiftCalculation.objects.create(shift=shift, paid_hours=Decimal("9.50"), base_amount=Decimal("465.50"))

inv = Invoice.objects.create(
    customer=cust, number="RECH-SMOKE-20250901", sequence=999,
    invoice_date=date(2025, 9, 30), period_start=date(2025, 9, 1), period_end=date(2025, 9, 30),
    payment_term_days=14,
)
InvoiceLine.objects.create(
    invoice=inv, position=1, line_type=InvoiceLine.LineType.BASE_HOURS,
    description="Netto Stunden ohne Pausen", quantity_hours=Decimal("9.50"),
    factor=Decimal("49.00"), amount=Decimal("465.50"),
)
shift.invoice = inv
shift.status = Shift.Status.INVOICED
shift.save()

print("active_contract:", cust.active_contract)
print("contract surcharges:", contract.surcharge_rules.count())
print("travel rule per km:", contract.travel_cost_rule.rate_per_km)
print("distance:", TravelDistance.objects.get(employee=emp, customer=cust).one_way_km, "km")
print("shift.is_billable (invoiced):", shift.is_billable)
print("calc.net_total:", shift.calculation.net_total)
print("invoice.due_date:", inv.due_date, "| lines:", inv.lines.count())
print("OK: alle Beziehungen funktionieren")

# Aufräumen
inv.delete()
cust.delete()
emp.delete()
print("CLEANUP done")
