from rest_framework import viewsets

from apps.accounts.emails import send_invite_email
from apps.accounts.permissions import IsAdmin
from apps.common.tenancy import TenantScopedViewSet, get_current_org

from .models import EmployeeProfile
from .serializers import EmployeeSerializer


class EmployeeViewSet(TenantScopedViewSet, viewsets.ModelViewSet):
    queryset = EmployeeProfile.objects.select_related("user")
    serializer_class = EmployeeSerializer
    permission_classes = [IsAdmin]
    tenant_field = "user__organization"

    def get_queryset(self):
        qs = super().get_queryset()
        active = self.request.query_params.get("is_active")
        qualification = self.request.query_params.get("qualification")
        if active in ("true", "false"):
            qs = qs.filter(is_active=(active == "true"))
        if qualification:
            qs = qs.filter(qualification=qualification)
        return qs

    def perform_create(self, serializer):
        # Neue Mitarbeiter gehören in die Organisation des anlegenden Admins.
        org = get_current_org(self.request.user)
        profile = serializer.save()
        if org and profile.user.organization_id != org.id:
            profile.user.organization = org
            profile.user.save(update_fields=["organization"])

        # Ohne gesetztes Passwort: Einladung verschicken, damit der Mitarbeiter
        # sein erstes Passwort selbst festlegt. Wurde beim Anlegen ein Passwort
        # gesetzt, teilt der Admin es selbst mit – dann keine Einladung.
        if not profile.user.has_usable_password():
            send_invite_email(profile.user, self.request)
