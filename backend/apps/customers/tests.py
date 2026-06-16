"""Kunden- und Vertrags-API: CRUD, Validierung, Löschschutz, Mandantentrennung."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.customers.models import Customer
from apps.organizations.models import Organization

User = get_user_model()


class CustomerApiTests(APITestCase):
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

    def test_admin_creates_customer_stamped_with_org(self):
        self.client.force_authenticate(self.admin)
        res = self.client.post(
            "/api/customers/", {"name": "Pflegehaus", "bundesland": "HE"}
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(Customer.objects.get(name="Pflegehaus").organization_id, self.org.id)

    def test_employee_cannot_create_customer(self):
        self.client.force_authenticate(self.employee)
        res = self.client.post(
            "/api/customers/", {"name": "X", "bundesland": "HE"}
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_contract_and_active_contract(self):
        self.client.force_authenticate(self.admin)
        customer = Customer.objects.create(
            name="Haus", bundesland="HE", organization=self.org
        )
        res = self.client.post("/api/contracts/", {
            "customer": customer.id,
            "valid_from": "2026-01-01",
            "is_active": True,
            "base_hourly_rate": "30.00",
            "night_surcharge_pct": "25",
            "saturday_surcharge_pct": "0",
            "sunday_surcharge_pct": "50",
            "holiday_surcharge_pct": "100",
            "night_start": "20:00",
            "night_end": "06:00",
            "invoice_rhythm": "monthly",
            "payment_term_days": 14,
            "vat_rate": "19",
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        customer.refresh_from_db()
        self.assertIsNotNone(customer.active_contract)
        self.assertEqual(customer.active_contract.base_hourly_rate, Decimal("30.00"))

    def test_customer_with_invoice_is_protected_from_delete(self):
        from apps.invoicing.models import Invoice

        self.client.force_authenticate(self.admin)
        customer = Customer.objects.create(
            name="Haus", bundesland="HE", organization=self.org
        )
        Invoice.objects.create(
            organization=self.org, customer=customer, number="RECH-1-20260101",
            sequence=1, invoice_date=date(2026, 1, 1),
            period_start=date(2026, 1, 1), period_end=date(2026, 1, 31),
        )
        # PROTECT-FK -> saubere 400 (kein 500) und Kunde bleibt bestehen.
        res = self.client.delete(f"/api/customers/{customer.id}/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Customer.objects.filter(id=customer.id).exists())
