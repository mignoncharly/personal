"""Audit-Log-API: nur Admin, mandantengetrennt, paginiert."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.common.models import AuditLog
from apps.organizations.models import Organization

User = get_user_model()


class AuditLogApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org_a = Organization.objects.create(name="Firma A", slug="firma-a")
        cls.org_b = Organization.objects.create(name="Firma B", slug="firma-b")
        cls.admin_a = User.objects.create_user(
            email="a@a.de", password="pw-secret-123", role=User.Role.ADMIN,
            organization=cls.org_a,
        )
        cls.employee_a = User.objects.create_user(
            email="e@a.de", password="pw-secret-123", role=User.Role.EMPLOYEE,
            organization=cls.org_a,
        )
        AuditLog.objects.create(
            actor=cls.admin_a, organization=cls.org_a, action=AuditLog.Action.CREATE,
            entity_type="Invoice", entity_id="1", summary="Rechnung A",
        )
        AuditLog.objects.create(
            organization=cls.org_b, action=AuditLog.Action.CREATE,
            entity_type="Invoice", entity_id="2", summary="Rechnung B",
        )

    def test_admin_sees_only_own_org_entries(self):
        self.client.force_authenticate(self.admin_a)
        res = self.client.get("/api/audit-log/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Paginierte Antwort.
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["summary"], "Rechnung A")
        self.assertEqual(res.data["results"][0]["actor_name"], "a@a.de")

    def test_employee_is_forbidden(self):
        self.client.force_authenticate(self.employee_a)
        res = self.client.get("/api/audit-log/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_by_action(self):
        self.client.force_authenticate(self.admin_a)
        res = self.client.get("/api/audit-log/", {"action": "approve"})
        self.assertEqual(res.data["count"], 0)
