from django.contrib import admin

from .models import Shift, ShiftCalculation


class ShiftCalculationInline(admin.StackedInline):
    model = ShiftCalculation
    extra = 0
    can_delete = False


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = (
        "date", "employee", "customer", "shift_type", "start_time", "end_time",
        "break_minutes", "status",
    )
    list_filter = ("status", "shift_type", "customer")
    search_fields = ("employee__email", "customer__name")
    date_hierarchy = "date"
    autocomplete_fields = ("employee", "customer")
    inlines = [ShiftCalculationInline]


@admin.register(ShiftCalculation)
class ShiftCalculationAdmin(admin.ModelAdmin):
    list_display = ("shift", "paid_hours", "night_hours", "saturday_hours", "sunday_hours", "holiday_hours")
