"""Erstellt die Standard-Organisation und ordnet alle bestehenden Daten ihr zu.

Läuft vor den Migrationen, die organization auf NOT NULL setzen (siehe run_before),
damit bestehende Zeilen sicher befüllt sind. Der plattformweite Superuser bleibt
bewusst ohne Organisation.
"""

from django.db import migrations

DEFAULT_NAME = "Your Company Name"
DEFAULT_SLUG = "your-company-name"


def create_default_org(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    User = apps.get_model("accounts", "User")
    Customer = apps.get_model("customers", "Customer")
    Shift = apps.get_model("shifts", "Shift")
    Invoice = apps.get_model("invoicing", "Invoice")
    AuditLog = apps.get_model("common", "AuditLog")

    org, _ = Organization.objects.get_or_create(
        slug=DEFAULT_SLUG,
        defaults={"name": DEFAULT_NAME, "invoice_number_prefix": "RECH"},
    )

    # Alle bestehenden Mandantendaten der Standard-Organisation zuordnen.
    Customer.objects.filter(organization__isnull=True).update(organization=org)
    Shift.objects.filter(organization__isnull=True).update(organization=org)
    Invoice.objects.filter(organization__isnull=True).update(organization=org)
    AuditLog.objects.filter(organization__isnull=True).update(organization=org)

    # Bestehende Nicht-Superuser gehören in die Standard-Organisation;
    # echte Plattform-Superuser bleiben ohne Organisation.
    User.objects.filter(organization__isnull=True, is_superuser=False).update(organization=org)


def remove_default_org(apps, schema_editor):
    # Rückwärts: Zuordnungen lösen, dann die Standard-Organisation entfernen.
    Organization = apps.get_model("organizations", "Organization")
    User = apps.get_model("accounts", "User")
    Customer = apps.get_model("customers", "Customer")
    Shift = apps.get_model("shifts", "Shift")
    Invoice = apps.get_model("invoicing", "Invoice")
    AuditLog = apps.get_model("common", "AuditLog")

    try:
        org = Organization.objects.get(slug=DEFAULT_SLUG)
    except Organization.DoesNotExist:
        return

    User.objects.filter(organization=org).update(organization=None)
    Customer.objects.filter(organization=org).update(organization=None)
    Shift.objects.filter(organization=org).update(organization=None)
    Invoice.objects.filter(organization=org).update(organization=None)
    AuditLog.objects.filter(organization=org).update(organization=None)
    org.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0001_initial"),
        ("accounts", "0002_user_organization"),
        ("customers", "0003_customer_organization"),
        ("shifts", "0002_shift_organization"),
        ("invoicing", "0003_invoice_organization"),
        ("common", "0002_auditlog_organization"),
    ]

    # Muss vor dem Umstellen auf NOT NULL laufen.
    run_before = [
        ("customers", "0004_alter_customer_organization"),
        ("shifts", "0003_alter_shift_organization"),
        ("invoicing", "0004_alter_invoice_organization"),
    ]

    operations = [
        migrations.RunPython(create_default_org, remove_default_org),
    ]
