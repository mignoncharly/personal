from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "entity_type", "entity_id", "actor", "summary")
    list_filter = ("action", "entity_type")
    search_fields = ("entity_id", "summary")
    readonly_fields = ("created_at", "actor", "action", "entity_type", "entity_id", "summary", "changes")

    def has_add_permission(self, request):
        return False
