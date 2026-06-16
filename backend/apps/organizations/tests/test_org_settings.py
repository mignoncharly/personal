"""Selbstverwaltung der eigenen Organisation: ein Org-Admin liest und ändert die
Firmen-/Rechnungsidentität seiner eigenen Organisation – niemals einer fremden."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.organizations.models import Organization

User = get_user_model()

URL = "/api/organization/"


class CurrentOrganizationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org_a = Organization.objects.create(name="Firma A", slug="firma-a")
        cls.org_b = Organization.objects.create(name="Firma B", slug="firma-b")

        cls.admin_a = User.objects.create_user(
            email="a@a.de", password="pw-secret-123", role=User.Role.ADMIN,
            organization=cls.org_a,
        )
        cls.employee_a = User.objects.create_user(
            email="emp@a.de", password="pw-secret-123", role=User.Role.EMPLOYEE,
            organization=cls.org_a,
        )
        cls.platform_super = User.objects.create_superuser(
            email="root@root.de", password="pw-secret-123",
        )

    def test_admin_reads_own_organization(self):
        self.client.force_authenticate(self.admin_a)
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], self.org_a.id)
        self.assertEqual(res.data["name"], "Firma A")

    def test_admin_updates_own_organization(self):
        self.client.force_authenticate(self.admin_a)
        res = self.client.patch(URL, {
            "name": "Pflegedienst Sonnenschein GmbH",
            "legal_name": "Pflegedienst Sonnenschein GmbH",
            "street": "Hauptstraße 1",
            "zip_code": "65462",
            "city": "Ginsheim",
            "vat_id": "DE123456789",
            "iban": "DE02120300000000202051",
            "invoice_number_prefix": "PS",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.org_a.refresh_from_db()
        self.assertEqual(self.org_a.name, "Pflegedienst Sonnenschein GmbH")
        self.assertEqual(self.org_a.city, "Ginsheim")
        self.assertEqual(self.org_a.invoice_number_prefix, "PS")

    def test_read_only_fields_are_ignored(self):
        self.client.force_authenticate(self.admin_a)
        res = self.client.patch(URL, {
            "slug": "gehackt",
            "is_active": False,
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.org_a.refresh_from_db()
        self.assertEqual(self.org_a.slug, "firma-a")
        self.assertTrue(self.org_a.is_active)

    def test_admin_only_ever_touches_own_org(self):
        """Es gibt keinen Pfad zu einer fremden Organisation – Admin A sieht A."""
        self.client.force_authenticate(self.admin_a)
        res = self.client.get(URL)
        self.assertEqual(res.data["id"], self.org_a.id)
        self.assertNotEqual(res.data["id"], self.org_b.id)

    def test_employee_is_forbidden(self):
        self.client.force_authenticate(self.employee_a)
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_org_less_superuser_gets_404(self):
        self.client.force_authenticate(self.platform_super)
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_is_unauthorized(self):
        res = self.client.get(URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
