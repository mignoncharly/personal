from rest_framework import viewsets

from apps.accounts.permissions import IsAdmin

from .models import AuditLog
from .pagination import StandardPagination
from .serializers import AuditLogSerializer
from .tenancy import scope_queryset


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Schreibgeschütztes Audit-Log (nur Admin), auf die eigene Organisation begrenzt."""

    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = scope_queryset(
            AuditLog.objects.select_related("actor"), self.request.user
        )
        params = self.request.query_params
        if action := params.get("action"):
            qs = qs.filter(action=action)
        if entity_type := params.get("entity_type"):
            qs = qs.filter(entity_type=entity_type)
        return qs
