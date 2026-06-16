"""Mandantentrennung: eine Organisation darf Daten einer anderen weder sehen
noch verändern. Plattform-Superuser sehen organisationsübergreifend."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.customers.models import Customer
from apps.organizations.models import Organization

User = get_user_model()


class TenantIsolationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org_a = Organization.objects.create(name="Firma A", slug="firma-a")
        cls.org_b = Organization.objects.create(name="Firma B", slug="firma-b")

        cls.admin_a = User.objects.create_user(
            email="a@a.de", password="pw-secret-123", role=User.Role.ADMIN,
            organization=cls.org_a,
        )
        cls.admin_b = User.objects.create_user(
            email="b@b.de", password="pw-secret-123", role=User.Role.ADMIN,
            organization=cls.org_b,
        )
        cls.super = User.objects.create_superuser(email="root@root.de", password="pw-secret-123")

        cls.cust_a = Customer.objects.create(name="Kunde A", bundesland="HE", organization=cls.org_a)
        cls.cust_b = Customer.objects.create(name="Kunde B", bundesland="HE", organization=cls.org_b)

    def test_admin_lists_only_own_org_customers(self):
        self.client.force_authenticate(self.admin_a)
        res = self.client.get("/api/customers/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        names = {c["name"] for c in res.data["results"]} if "results" in res.data else {c["name"] for c in res.data}
        self.assertEqual(names, {"Kunde A"})

    def test_admin_cannot_read_other_org_customer(self):
        self.client.force_authenticate(self.admin_a)
        res = self.client.get(f"/api/customers/{self.cust_b.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_cannot_delete_other_org_customer(self):
        self.client.force_authenticate(self.admin_a)
        res = self.client.delete(f"/api/customers/{self.cust_b.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Customer.objects.filter(id=self.cust_b.id).exists())

    def test_created_customer_is_stamped_with_callers_org(self):
        self.client.force_authenticate(self.admin_a)
        res = self.client.post("/api/customers/", {"name": "Neu A", "bundesland": "HE"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        created = Customer.objects.get(name="Neu A")
        self.assertEqual(created.organization_id, self.org_a.id)

    def test_superuser_sees_all_orgs(self):
        self.client.force_authenticate(self.super)
        res = self.client.get("/api/customers/")
        names = {c["name"] for c in res.data["results"]} if "results" in res.data else {c["name"] for c in res.data}
        self.assertEqual(names, {"Kunde A", "Kunde B"})
