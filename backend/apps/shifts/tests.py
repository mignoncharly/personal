from datetime import date, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.customers.models import Customer
from apps.organizations.models import Organization
from apps.shifts.models import Shift
from apps.shifts.services import calculate_shift_values

User = get_user_model()

# Standard-Nachtfenster wie im Konzept (Nacht beginnt ≤ 20:30, endet 06:00)
NIGHT_START = time(20, 0)
NIGHT_END = time(6, 0)


def D(x):
    return Decimal(str(x))


class EngineConceptExamplesTests(SimpleTestCase):
    """Verifikation gegen die Beispiele aus /concept."""

    def test_example_a_night_shift_image1(self):
        """image1: 20:30–06:30, 1 h Pause, Satz 40 → Grund 360, Nacht 85, gesamt 445."""
        v = calculate_shift_values(
            date=date(2025, 1, 15),  # Mittwoch -> Donnerstag (kein Feiertag/WE)
            start_time=time(20, 30), end_time=time(6, 30), break_minutes=60,
            base_rate=D("40"), night_pct=D("25"), sat_pct=D("25"),
            sun_pct=D("50"), hol_pct=D("100"),
            night_start=NIGHT_START, night_end=NIGHT_END, bundesland="HE",
        )
        self.assertEqual(v["paid_hours"], D("9.00"))
        self.assertEqual(v["night_hours"], D("8.50"))
        self.assertEqual(v["base_amount"], D("360.00"))
        self.assertEqual(v["night_amount"], D("85.00"))
        self.assertEqual(v["saturday_hours"], D("0.00"))
        self.assertEqual(v["sunday_hours"], D("0.00"))
        net = (v["base_amount"] + v["night_amount"] + v["saturday_amount"]
               + v["sunday_amount"] + v["holiday_amount"])
        self.assertEqual(net, D("445.00"))

    def test_cumulative_night_and_sunday(self):
        """Schriftliche Spec: 1 Std Nacht+Sonntag bei Satz 49 → 49 + 12,25 + 24,50 = 85,75."""
        v = calculate_shift_values(
            date=date(2025, 1, 19),  # Sonntag
            start_time=time(2, 0), end_time=time(3, 0), break_minutes=0,
            base_rate=D("49"), night_pct=D("25"), sat_pct=D("25"),
            sun_pct=D("50"), hol_pct=D("100"),
            night_start=NIGHT_START, night_end=NIGHT_END, bundesland="HE",
        )
        self.assertEqual(v["paid_hours"], D("1.00"))
        self.assertEqual(v["night_hours"], D("1.00"))
        self.assertEqual(v["sunday_hours"], D("1.00"))
        self.assertEqual(v["base_amount"], D("49.00"))
        self.assertEqual(v["night_amount"], D("12.25"))
        self.assertEqual(v["sunday_amount"], D("24.50"))
        net = v["base_amount"] + v["night_amount"] + v["sunday_amount"]
        self.assertEqual(net, D("85.75"))

    def test_saturday_day_shift(self):
        """Samstag-Tagschicht (kein Nacht): 8 h, Satz 49 → Grund 392, Samstag 98."""
        v = calculate_shift_values(
            date=date(2025, 1, 18),  # Samstag
            start_time=time(8, 0), end_time=time(16, 0), break_minutes=0,
            base_rate=D("49"), night_pct=D("25"), sat_pct=D("25"),
            sun_pct=D("50"), hol_pct=D("100"),
            night_start=NIGHT_START, night_end=NIGHT_END, bundesland="HE",
        )
        self.assertEqual(v["paid_hours"], D("8.00"))
        self.assertEqual(v["saturday_hours"], D("8.00"))
        self.assertEqual(v["night_hours"], D("0.00"))
        self.assertEqual(v["base_amount"], D("392.00"))
        self.assertEqual(v["saturday_amount"], D("98.00"))

    def test_holiday_hessen(self):
        """Feiertag HE (03.10.2025, Freitag): 8 h, Satz 49 → Grund 392, Feiertag 392."""
        v = calculate_shift_values(
            date=date(2025, 10, 3),
            start_time=time(8, 0), end_time=time(16, 0), break_minutes=0,
            base_rate=D("49"), night_pct=D("25"), sat_pct=D("25"),
            sun_pct=D("50"), hol_pct=D("100"),
            night_start=NIGHT_START, night_end=NIGHT_END, bundesland="HE",
        )
        self.assertTrue(v["is_holiday"])
        self.assertEqual(v["holiday_hours"], D("8.00"))
        self.assertEqual(v["base_amount"], D("392.00"))
        self.assertEqual(v["holiday_amount"], D("392.00"))
        self.assertEqual(v["saturday_hours"], D("0.00"))

    def test_non_cumulative_takes_highest(self):
        """Nicht kumulativ: Nacht+Sonntag → nur Sonntag (50% > 25%)."""
        v = calculate_shift_values(
            date=date(2025, 1, 19),  # Sonntag
            start_time=time(2, 0), end_time=time(3, 0), break_minutes=0,
            base_rate=D("49"), night_pct=D("25"), sat_pct=D("25"),
            sun_pct=D("50"), hol_pct=D("100"),
            night_start=NIGHT_START, night_end=NIGHT_END, bundesland="HE",
            cumulative=False,
        )
        self.assertEqual(v["sunday_hours"], D("1.00"))
        self.assertEqual(v["night_hours"], D("0.00"))
        self.assertEqual(v["sunday_amount"], D("24.50"))
        self.assertEqual(v["night_amount"], D("0.00"))

    def test_break_deducted_once_from_highest_surcharge(self):
        """Pause nur einmal, aus dem höchstbezuschlagten Segment (Fri→Sat über Mitternacht)."""
        v = calculate_shift_values(
            date=date(2025, 1, 17),  # Freitag -> Samstag
            start_time=time(20, 30), end_time=time(7, 0), break_minutes=60,
            base_rate=D("40"), night_pct=D("25"), sat_pct=D("25"),
            sun_pct=D("50"), hol_pct=D("100"),
            night_start=NIGHT_START, night_end=NIGHT_END, bundesland="HE",
        )
        # Span 10,5 h, Pause 1 h -> bezahlt 9,5 h
        self.assertEqual(v["paid_hours"], D("9.50"))
        self.assertEqual(v["base_amount"], D("380.00"))
        # Höchstes Segment ist Sa 00:00–06:00 (Nacht+Samstag = 50%); Pause dort abgezogen
        # Sa-Nacht 5 h + Fr-Nacht 3,5 h = 8,5 h Nacht; Samstag 5 h + 1 h = 6 h
        self.assertEqual(v["night_hours"], D("8.50"))
        self.assertEqual(v["saturday_hours"], D("6.00"))


class ShiftApiTests(APITestCase):
    """API-Verhalten: Paginierung der Liste und Summary-Zugriff je Rolle."""

    @classmethod
    def setUpTestData(cls):
        cls.org = Organization.objects.create(name="Firma A", slug="firma-a")
        cls.admin = User.objects.create_user(
            email="admin@a.de", password="pw-secret-123", role=User.Role.ADMIN,
            organization=cls.org,
        )
        cls.employee = User.objects.create_user(
            email="emp@a.de", password="pw-secret-123", role=User.Role.EMPLOYEE,
            organization=cls.org,
        )
        cls.customer = Customer.objects.create(
            name="Haus", bundesland="HE", organization=cls.org
        )
        for d in (1, 2, 3):
            Shift.objects.create(
                organization=cls.org, employee=cls.employee, customer=cls.customer,
                created_by=cls.employee, date=date(2026, 6, d),
                start_time=time(8, 0), end_time=time(16, 0), break_minutes=30,
                status=Shift.Status.DRAFT,
            )

    def test_shift_list_is_paginated(self):
        self.client.force_authenticate(self.admin)
        res = self.client.get("/api/shifts/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("results", res.data)
        self.assertEqual(res.data["count"], 3)

    def test_employee_can_access_summary_for_own_shifts(self):
        self.client.force_authenticate(self.employee)
        res = self.client.get("/api/shifts/summary/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["anzahl_schichten"], 3)

    def test_rejecting_shift_notifies_employee(self):
        from django.core import mail

        shift = Shift.objects.create(
            organization=self.org, employee=self.employee, customer=self.customer,
            created_by=self.employee, date=date(2026, 6, 10),
            start_time=time(8, 0), end_time=time(16, 0), break_minutes=30,
            status=Shift.Status.SUBMITTED,
        )
        self.client.force_authenticate(self.admin)
        res = self.client.post(
            f"/api/shifts/{shift.id}/reject/", {"reason": "Zeiten unklar"}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["emp@a.de"])
        self.assertIn("abgelehnt", mail.outbox[0].subject.lower())


class ShiftOverlapTests(APITestCase):
    """Schutz vor überlappenden Schichten je Mitarbeiter (auch über Mitternacht)."""

    @classmethod
    def setUpTestData(cls):
        cls.org = Organization.objects.create(name="Firma O", slug="firma-o")
        cls.employee = User.objects.create_user(
            email="o-emp@o.de", password="pw-secret-123",
            role=User.Role.EMPLOYEE, organization=cls.org,
        )
        cls.employee2 = User.objects.create_user(
            email="o-emp2@o.de", password="pw-secret-123",
            role=User.Role.EMPLOYEE, organization=cls.org,
        )
        cls.customer = Customer.objects.create(
            name="Haus O", bundesland="HE", organization=cls.org,
        )

    def setUp(self):
        self.client.force_authenticate(self.employee)

    def _post(self, **overrides):
        payload = {
            "customer": self.customer.id, "shift_type": "frueh",
            "date": "2026-07-10", "start_time": "08:00", "end_time": "16:00",
            "break_minutes": 0,
        }
        payload.update(overrides)
        return self.client.post("/api/shifts/", payload)

    def test_overlapping_shift_is_rejected(self):
        self.assertEqual(self._post().status_code, status.HTTP_201_CREATED)
        res = self._post(start_time="12:00", end_time="18:00")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("überschneidet", str(res.data))

    def test_back_to_back_shifts_are_allowed(self):
        r1 = self._post(start_time="08:00", end_time="12:00")
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED, r1.data)
        r2 = self._post(start_time="12:00", end_time="16:00")
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED, r2.data)

    def test_overlap_across_midnight_is_rejected(self):
        # Nachtschicht 22:00–06:00 (läuft in den Folgetag).
        r1 = self._post(date="2026-07-10", start_time="22:00", end_time="06:00")
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED, r1.data)
        # Folgetag 05:00–07:00 überschneidet das Nacht-Ende (06:00).
        r2 = self._post(date="2026-07-11", start_time="05:00", end_time="07:00")
        self.assertEqual(r2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("überschneidet", str(r2.data))

    def test_rejected_shift_does_not_block(self):
        Shift.objects.create(
            organization=self.org, employee=self.employee, customer=self.customer,
            created_by=self.employee, shift_type="frueh", date=date(2026, 7, 10),
            start_time=time(8, 0), end_time=time(16, 0), break_minutes=0,
            status=Shift.Status.REJECTED,
        )
        res = self._post(start_time="08:00", end_time="16:00")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)

    def test_overlap_is_per_employee(self):
        self.assertEqual(self._post().status_code, status.HTTP_201_CREATED)
        # Ein anderer Mitarbeiter darf zur selben Zeit arbeiten.
        self.client.force_authenticate(self.employee2)
        self.assertEqual(self._post().status_code, status.HTTP_201_CREATED)
