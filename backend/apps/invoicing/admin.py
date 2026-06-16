from django.contrib import admin

from .models import Invoice, InvoiceLine


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "number", "customer", "invoice_date", "period_start", "period_end",
        "subtotal_net", "vat_amount", "total_gross", "status",
    )
    list_filter = ("status", "customer")
    search_fields = ("number", "customer__name")
    date_hierarchy = "invoice_date"
    inlines = [InvoiceLineInline]
