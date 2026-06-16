"""Mitarbeiter-Anlage: Einladungs-E-Mail und Organisationszuordnung."""

from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase

from apps.organizations.models import Organization

User = get_user_model()


class EmployeeInviteTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = Organization.objects.create(name="Pflege Nord", slug="pflege-nord")
        cls.admin = User.objects.create_user(
            email="admin@nord.de", password="pw-secret-123",
            role=User.Role.ADMIN, organization=cls.org,
        )

    def setUp(self):
        self.client.force_authenticate(self.admin)

    def test_create_without_password_sends_invite(self):
        res = self.client.post("/api/employees/", {
            "email": "neu@nord.de", "first_name": "Neue", "last_name": "Kraft",
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)

        user = User.objects.get(email="neu@nord.de")
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.organization_id, self.org.id)

        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ["neu@nord.de"])
        self.assertIn("Pflege Nord", msg.subject)
        self.assertIn("/passwort-reset?uid=", msg.body)
        self.assertIn("neu@nord.de", msg.body)

    def test_create_with_password_does_not_send_invite(self):
        res = self.client.post("/api/employees/", {
            "email": "mitpw@nord.de", "first_name": "Mit", "last_name": "Passwort",
            "password": "pw-secret-456",
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)

        user = User.objects.get(email="mitpw@nord.de")
        self.assertTrue(user.has_usable_password())
        self.assertEqual(len(mail.outbox), 0)

    def test_email_failure_is_logged_and_does_not_block_creation(self):
        with mock.patch(
            "apps.accounts.emails.send_mail", side_effect=RuntimeError("smtp down")
        ):
            with self.assertLogs("apps.accounts.emails", level="WARNING") as logs:
                res = self.client.post("/api/employees/", {"email": "fehler@nord.de"})

        # Anlage gelingt trotz fehlgeschlagenem Mailversand.
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertTrue(User.objects.filter(email="fehler@nord.de").exists())
        self.assertTrue(any("fehler@nord.de" in line for line in logs.output))

    def test_invite_link_uses_request_origin(self):
        res = self.client.post(
            "/api/employees/", {"email": "origin@nord.de"},
            HTTP_ORIGIN="https://personal.example.com",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertIn(
            "https://personal.example.com/passwort-reset?uid=",
            mail.outbox[0].body,
        )
