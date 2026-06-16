"""Rechnungsversand per E-Mail (PDF im Anhang, BCC an die Organisation)."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase

from apps.customers.models import Customer
from apps.invoicing.models import Invoice
from apps.organizations.models import Organization

User = get_user_model()


class InvoiceSendTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = Organization.objects.create(
            name="Pflege Nord", slug="pflege-nord", email="buchhaltung@nord.de",
        )
        cls.admin = User.objects.create_user(
            email="admin@nord.de", password="pw-secret-123",
            role=User.Role.ADMIN, organization=cls.org,
        )
        cls.customer = Customer.objects.create(
            name="In Haus Mainblick", bundesland="HE", organization=cls.org,
            email="kunde@mainblick.de",
        )

    def _make_invoice(self, **overrides):
        defaults = dict(
            organization=self.org, customer=self.customer,
            number="RECH-1-20260616", sequence=1, invoice_date=date(2026, 6, 16),
            period_start=date(2026, 6, 1), period_end=date(2026, 6, 15),
            status=Invoice.Status.FINALIZED, total_gross=Decimal("119.00"),
        )
        defaults.update(overrides)
        return Invoice.objects.create(**defaults)

    def setUp(self):
        self.client.force_authenticate(self.admin)

    def test_send_finalized_invoice_emails_customer_with_pdf_and_bcc(self):
        invoice = self._make_invoice()
        res = self.client.post(f"/api/invoices/{invoice.id}/send/")
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.Status.SENT)
        self.assertIsNotNone(invoice.sent_at)

        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ["kunde@mainblick.de"])
        self.assertEqual(msg.bcc, ["buchhaltung@nord.de"])
        self.assertIn("RECH-1-20260616", msg.subject)
        self.assertEqual(len(msg.attachments), 1)
        filename, _content, mimetype = msg.attachments[0]
        self.assertEqual(filename, "RECH-1-20260616.pdf")
        self.assertEqual(mimetype, "application/pdf")

    def test_cannot_send_draft(self):
        invoice = self._make_invoice(status=Invoice.Status.DRAFT)
        res = self.client.post(f"/api/invoices/{invoice.id}/send/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(mail.outbox), 0)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.Status.DRAFT)

    def test_send_without_customer_email_returns_clear_error(self):
        self.customer.email = ""
        self.customer.save(update_fields=["email"])
        invoice = self._make_invoice()
        res = self.client.post(f"/api/invoices/{invoice.id}/send/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("E-Mail-Adresse", str(res.data))
        self.assertEqual(len(mail.outbox), 0)

    def test_resend_allowed_for_already_sent(self):
        invoice = self._make_invoice(status=Invoice.Status.SENT)
        res = self.client.post(f"/api/invoices/{invoice.id}/send/")
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(len(mail.outbox), 1)

    def test_mark_paid_and_unpaid(self):
        from django.utils import timezone

        invoice = self._make_invoice(status=Invoice.Status.SENT, sent_at=timezone.now())
        res = self.client.post(f"/api/invoices/{invoice.id}/mark_paid/")
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.Status.PAID)
        self.assertIsNotNone(invoice.paid_at)

        res = self.client.post(f"/api/invoices/{invoice.id}/mark_unpaid/")
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        invoice.refresh_from_db()
        # War zuvor versendet -> kehrt zu SENT zurück.
        self.assertEqual(invoice.status, Invoice.Status.SENT)
        self.assertIsNone(invoice.paid_at)

    def test_cannot_mark_draft_paid(self):
        invoice = self._make_invoice(status=Invoice.Status.DRAFT)
        res = self.client.post(f"/api/invoices/{invoice.id}/mark_paid/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_overdue_flag_and_summary(self):
        from datetime import date, timedelta

        # Überfällig: festgeschrieben, Fälligkeit in der Vergangenheit.
        overdue = self._make_invoice(
            number="RECH-2-20260101", sequence=2,
            invoice_date=date.today() - timedelta(days=60), payment_term_days=14,
        )
        self.assertTrue(overdue.is_overdue)

        res = self.client.get("/api/invoices/summary/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["open_count"], 1)
        self.assertEqual(res.data["overdue_count"], 1)

    def test_finalized_invoice_cannot_be_deleted(self):
        invoice = self._make_invoice(status=Invoice.Status.FINALIZED)
        res = self.client.delete(f"/api/invoices/{invoice.id}/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Invoice.objects.filter(id=invoice.id).exists())

    def test_remind_overdue_invoice(self):
        from datetime import date, timedelta

        overdue = self._make_invoice(
            number="RECH-9-20260101", sequence=9,
            invoice_date=date.today() - timedelta(days=60), payment_term_days=14,
        )
        res = self.client.post(f"/api/invoices/{overdue.id}/remind/")
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        overdue.refresh_from_db()
        self.assertIsNotNone(overdue.last_reminded_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Zahlungserinnerung", mail.outbox[0].subject)

    def test_cannot_remind_non_overdue(self):
        invoice = self._make_invoice(status=Invoice.Status.FINALIZED)
        res = self.client.post(f"/api/invoices/{invoice.id}/remind/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(mail.outbox), 0)

    def test_cancel_invoice(self):
        invoice = self._make_invoice(status=Invoice.Status.SENT)
        res = self.client.post(f"/api/invoices/{invoice.id}/cancel/")
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.Status.CANCELLED)
        # Nummer bleibt erhalten (kein Löschen).
        self.assertTrue(Invoice.objects.filter(id=invoice.id).exists())

    def test_cannot_cancel_draft_or_twice(self):
        draft = self._make_invoice(status=Invoice.Status.DRAFT)
        self.assertEqual(
            self.client.post(f"/api/invoices/{draft.id}/cancel/").status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        cancelled = self._make_invoice(
            number="RECH-3-20260101", sequence=3, status=Invoice.Status.CANCELLED,
        )
        self.assertEqual(
            self.client.post(f"/api/invoices/{cancelled.id}/cancel/").status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_csv_export(self):
        self._make_invoice()
        res = self.client.get("/api/invoices/export/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment", res["Content-Disposition"])
        body = res.content.decode("utf-8-sig")
        self.assertIn("Nummer;Kunde", body)
        self.assertIn("RECH-1-20260616", body)
        self.assertIn("In Haus Mainblick", body)


class KleinunternehmerInvoiceTests(APITestCase):
    """§ 19 UStG: Bei Kleinunternehmern wird keine USt ausgewiesen."""

    @classmethod
    def setUpTestData(cls):
        from datetime import time

        from apps.customers.models import CustomerContract
        from apps.shifts.models import Shift

        cls.admin = User.objects.create_user(
            email="a@klein.de", password="pw-secret-123", role=User.Role.ADMIN,
        )

        def build(org_small):
            org = Organization.objects.create(
                name=f"Org {org_small}", slug=f"org-{org_small}",
                is_small_business=org_small,
            )
            customer = Customer.objects.create(
                name="Kunde", bundesland="HE", organization=org,
            )
            CustomerContract.objects.create(
                customer=customer, valid_from=date(2025, 1, 1),
                base_hourly_rate=Decimal("40"), vat_rate=Decimal("19"),
            )
            Shift.objects.create(
                organization=org, employee=cls.admin, customer=customer,
                shift_type=Shift.ShiftType.EARLY, date=date(2025, 1, 15),  # Mittwoch
                start_time=time(8, 0), end_time=time(16, 0), break_minutes=0,
                status=Shift.Status.APPROVED,
            )
            return customer

        cls.small_customer = build(True)
        cls.normal_customer = build(False)

    def _generate(self, customer):
        from apps.invoicing.services import generate_invoice

        return generate_invoice(
            customer=customer, period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31), invoice_date=date(2025, 2, 1),
            user=self.admin,
        )

    def test_small_business_invoice_has_no_vat(self):
        inv = self._generate(self.small_customer)
        self.assertTrue(inv.is_small_business)
        self.assertEqual(inv.vat_rate, Decimal("0"))
        self.assertEqual(inv.vat_amount, Decimal("0.00"))
        self.assertEqual(inv.total_gross, inv.subtotal_net)
        self.assertEqual(inv.subtotal_net, Decimal("320.00"))  # 8 h × 40 €

    def test_small_business_pdf_shows_paragraph_19_note(self):
        from apps.invoicing.pdf import build_context

        ctx = build_context(self._generate(self.small_customer))
        self.assertTrue(ctx["is_small_business"])
        self.assertIn("§ 19 UStG", ctx["small_business_note"])

    def test_normal_org_still_charges_vat(self):
        inv = self._generate(self.normal_customer)
        self.assertFalse(inv.is_small_business)
        self.assertEqual(inv.vat_rate, Decimal("19"))
        self.assertEqual(inv.vat_amount, Decimal("60.80"))  # 19 % von 320
        self.assertEqual(inv.total_gross, Decimal("380.80"))


class ReportTests(APITestCase):
    """Auswertungen: Umsatz im Zeitraum, je Kunde, mandantengebunden."""

    @classmethod
    def setUpTestData(cls):
        cls.org = Organization.objects.create(name="Org R", slug="org-r")
        cls.admin = User.objects.create_user(
            email="r@org.de", password="pw-secret-123",
            role=User.Role.ADMIN, organization=cls.org,
        )
        cls.customer = Customer.objects.create(
            name="Kunde R", bundesland="HE", organization=cls.org,
        )
        common = dict(
            organization=cls.org, customer=cls.customer,
            status=Invoice.Status.FINALIZED, subtotal_net=Decimal("100.00"),
            vat_amount=Decimal("19.00"), total_gross=Decimal("119.00"),
            period_start=date(2026, 1, 1), period_end=date(2026, 1, 31),
        )
        Invoice.objects.create(
            number="R-1-20260115", sequence=1, invoice_date=date(2026, 1, 15), **common,
        )
        Invoice.objects.create(
            number="R-2-20260215", sequence=2, invoice_date=date(2026, 2, 15), **common,
        )
        # Entwurf zählt nicht zum Umsatz.
        Invoice.objects.create(
            number="R-3-20260120", sequence=3, invoice_date=date(2026, 1, 20),
            status=Invoice.Status.DRAFT, **{k: v for k, v in common.items() if k != "status"},
        )

    def setUp(self):
        self.client.force_authenticate(self.admin)

    def test_report_totals_and_breakdowns(self):
        res = self.client.get("/api/reports/", {"from": "2026-01-01", "to": "2026-02-28"})
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        # Zwei festgeschriebene Rechnungen, Entwurf ausgeschlossen.
        self.assertEqual(res.data["totals"]["count"], 2)
        self.assertEqual(Decimal(res.data["totals"]["gross"]), Decimal("238.00"))
        self.assertEqual(len(res.data["by_month"]), 2)
        self.assertEqual(res.data["by_customer"][0]["customer"], "Kunde R")

    def test_report_respects_date_range(self):
        res = self.client.get("/api/reports/", {"from": "2026-02-01", "to": "2026-02-28"})
        self.assertEqual(res.data["totals"]["count"], 1)
        self.assertEqual(Decimal(res.data["totals"]["gross"]), Decimal("119.00"))

    def test_report_csv_export(self):
        res = self.client.get("/api/reports/", {"download": "csv"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("Kunde;Anzahl", res.content.decode("utf-8-sig"))
