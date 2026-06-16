"""Rechnungsnummern laufen pro Organisation unabhängig und nutzen deren Präfix."""

from django.db import transaction
from django.test import TestCase

from apps.invoicing.services import next_sequence
from apps.organizations.models import Organization


class PerOrgInvoiceNumberingTests(TestCase):
    def setUp(self):
        self.org_a = Organization.objects.create(name="Firma A", slug="firma-a", invoice_number_prefix="A")
        self.org_b = Organization.objects.create(name="Firma B", slug="firma-b", invoice_number_prefix="B")

    def test_sequences_are_independent_per_org(self):
        with transaction.atomic():
            self.assertEqual(next_sequence(self.org_a), 1)
            self.assertEqual(next_sequence(self.org_a), 2)
            # Org B beginnt unabhängig bei 1.
            self.assertEqual(next_sequence(self.org_b), 1)
            self.assertEqual(next_sequence(self.org_a), 3)

        self.org_a.refresh_from_db()
        self.org_b.refresh_from_db()
        self.assertEqual(self.org_a.invoice_sequence_counter, 3)
        self.assertEqual(self.org_b.invoice_sequence_counter, 1)
