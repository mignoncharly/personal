from rest_framework import serializers

from .models import Organization


class OrganizationSerializer(serializers.ModelSerializer):
    """Selbstverwaltung der eigenen Organisation durch deren Admin.

    Firmenidentität und Rechnungsangaben (Briefkopf) sind editierbar. ``slug``,
    Aktiv-Status und der Rechnungszähler bleiben schreibgeschützt – diese verwaltet
    ausschließlich der Plattform-Superuser (Django-Admin bzw. CLI-Provisionierung).
    Das Logo wird hier nur gelesen (Upload erfolgt im Django-Admin).
    """

    logo = serializers.ImageField(read_only=True)

    class Meta:
        model = Organization
        fields = (
            "id", "name", "slug", "is_active",
            "legal_name", "street", "zip_code", "city", "phone", "email",
            "vat_id", "tax_number", "is_small_business",
            "bank_name", "iban", "bic",
            "logo", "invoice_number_prefix",
        )
        read_only_fields = ("id", "slug", "is_active", "logo")
