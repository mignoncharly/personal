from django.contrib import admin

from .models import (
    Customer,
    CustomerContract,
    SurchargeRule,
    TravelCostRule,
    TravelDistance,
)


class SurchargeRuleInline(admin.TabularInline):
    model = SurchargeRule
    extra = 0


class TravelCostRuleInline(admin.StackedInline):
    model = TravelCostRule
    extra = 0


@admin.register(CustomerContract)
class CustomerContractAdmin(admin.ModelAdmin):
    list_display = (
        "customer", "valid_from", "is_active", "base_hourly_rate",
        "invoice_rhythm", "vat_rate",
    )
    list_filter = ("is_active", "invoice_rhythm")
    search_fields = ("customer__name",)
    inlines = [SurchargeRuleInline, TravelCostRuleInline]


class CustomerContractInline(admin.StackedInline):
    model = CustomerContract
    extra = 0
    show_change_link = True


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "customer_number", "city", "bundesland", "is_active")
    list_filter = ("bundesland", "is_active")
    search_fields = ("name", "customer_number", "city")
    inlines = [CustomerContractInline]


@admin.register(TravelDistance)
class TravelDistanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "customer", "one_way_km")
    search_fields = ("employee__email", "customer__name")
