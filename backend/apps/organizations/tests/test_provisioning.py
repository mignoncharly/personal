"""Das Management-Kommando legt Organisation + ersten Admin korrekt an."""

from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.organizations.models import Organization

User = get_user_model()


class CreateOrganizationCommandTests(TestCase):
    def test_creates_org_and_admin_without_password(self):
        call_command(
            "create_organization", "Pflege Sonne",
            admin_email="Chef@Sonne.de", admin_first_name="Maria",
            stdout=StringIO(),
        )
        org = Organization.objects.get(slug="pflege-sonne")
        admin = User.objects.get(email="chef@sonne.de")
        self.assertEqual(admin.organization_id, org.id)
        self.assertEqual(admin.role, User.Role.ADMIN)
        self.assertEqual(admin.first_name, "Maria")
        # Kein Passwort -> Erstanmeldung via Reset
        self.assertFalse(admin.has_usable_password())

    def test_creates_admin_with_password(self):
        call_command(
            "create_organization", "Pflege Mond",
            admin_email="chef@mond.de", password="sicher-Passwort-99",
            stdout=StringIO(),
        )
        admin = User.objects.get(email="chef@mond.de")
        self.assertTrue(admin.has_usable_password())
        self.assertTrue(admin.check_password("sicher-Passwort-99"))

    def test_rejects_duplicate_email(self):
        call_command("create_organization", "Firma X", admin_email="dup@x.de", stdout=StringIO())
        with self.assertRaises(CommandError):
            call_command("create_organization", "Firma Y", admin_email="dup@x.de", stdout=StringIO())
