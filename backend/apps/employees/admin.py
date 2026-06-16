from django.contrib import admin

from .models import EmployeeProfile


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ("__str__", "qualification", "city", "is_active")
    list_filter = ("qualification", "is_active")
    search_fields = ("user__email", "user__first_name", "user__last_name", "city")
    autocomplete_fields = ("user",)
