from django.contrib import admin

from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "city", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "legal_name", "slug", "city", "vat_id")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("invoice_sequence_counter", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "slug", "is_active")}),
        ("Firmenidentität (Rechnungskopf)", {
            "fields": ("legal_name", "street", "zip_code", "city", "phone", "email", "logo"),
        }),
        ("Steuer & Bank", {
            "fields": ("vat_id", "tax_number", "bank_name", "iban", "bic"),
        }),
        ("Rechnungsnummerierung", {
            "fields": ("invoice_number_prefix", "invoice_sequence_counter"),
        }),
        ("Zeitstempel", {"fields": ("created_at", "updated_at")}),
    )
