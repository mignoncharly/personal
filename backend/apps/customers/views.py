from django.db.models import ProtectedError
from rest_framework import generics, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsAdmin
from apps.common.tenancy import (
    TenantScopedViewSet,
    assert_org_match,
    scope_queryset,
)

from .models import (
    Customer,
    CustomerContract,
    SurchargeRule,
    TravelCostRule,
    TravelDistance,
)
from .serializers import (
    CustomerChoiceSerializer,
    CustomerContractSerializer,
    CustomerSerializer,
    SurchargeRuleSerializer,
    TravelCostRuleSerializer,
    TravelDistanceSerializer,
)


class CustomerChoiceList(generics.ListAPIView):
    """Aktive Kunden für die Auswahl bei der Schichterfassung (alle Angemeldeten)."""

    queryset = Customer.objects.filter(is_active=True).order_by("name")
    serializer_class = CustomerChoiceSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return scope_queryset(super().get_queryset(), self.request.user)


class CustomerViewSet(TenantScopedViewSet, viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        bundesland = self.request.query_params.get("bundesland")
        active = self.request.query_params.get("is_active")
        if bundesland:
            qs = qs.filter(bundesland=bundesland)
        if active in ("true", "false"):
            qs = qs.filter(is_active=(active == "true"))
        return qs

    def perform_destroy(self, instance):
        # Kunden mit Schichten/Rechnungen sind per PROTECT-FK geschützt; klare 400
        # statt 500. Stattdessen sollte der Kunde deaktiviert werden.
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError(
                "Dieser Kunde kann nicht gelöscht werden, da noch Schichten oder "
                "Rechnungen darauf verweisen. Bitte stattdessen deaktivieren."
            )


class CustomerContractViewSet(TenantScopedViewSet, viewsets.ModelViewSet):
    queryset = CustomerContract.objects.select_related("customer").prefetch_related(
        "surcharge_rules", "travel_cost_rule"
    )
    serializer_class = CustomerContractSerializer
    permission_classes = [IsAdmin]
    tenant_field = "customer__organization"

    def get_queryset(self):
        qs = super().get_queryset()
        customer = self.request.query_params.get("customer")
        if customer:
            qs = qs.filter(customer_id=customer)
        return qs

    def perform_create(self, serializer):
        customer = serializer.validated_data["customer"]
        assert_org_match(self.request.user, customer.organization_id)
        serializer.save()


class SurchargeRuleViewSet(TenantScopedViewSet, viewsets.ModelViewSet):
    queryset = SurchargeRule.objects.select_related("contract__customer")
    serializer_class = SurchargeRuleSerializer
    permission_classes = [IsAdmin]
    tenant_field = "contract__customer__organization"

    def get_queryset(self):
        qs = super().get_queryset()
        contract = self.request.query_params.get("contract")
        if contract:
            qs = qs.filter(contract_id=contract)
        return qs

    def perform_create(self, serializer):
        contract = serializer.validated_data["contract"]
        assert_org_match(self.request.user, contract.customer.organization_id)
        serializer.save()


class TravelCostRuleViewSet(TenantScopedViewSet, viewsets.ModelViewSet):
    queryset = TravelCostRule.objects.select_related("contract__customer")
    serializer_class = TravelCostRuleSerializer
    permission_classes = [IsAdmin]
    tenant_field = "contract__customer__organization"

    def perform_create(self, serializer):
        contract = serializer.validated_data["contract"]
        assert_org_match(self.request.user, contract.customer.organization_id)
        serializer.save()


class TravelDistanceViewSet(TenantScopedViewSet, viewsets.ModelViewSet):
    queryset = TravelDistance.objects.select_related("employee", "customer")
    serializer_class = TravelDistanceSerializer
    permission_classes = [IsAdmin]
    tenant_field = "customer__organization"

    def get_queryset(self):
        qs = super().get_queryset()
        employee = self.request.query_params.get("employee")
        customer = self.request.query_params.get("customer")
        if employee:
            qs = qs.filter(employee_id=employee)
        if customer:
            qs = qs.filter(customer_id=customer)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        customer = serializer.validated_data["customer"]
        employee = serializer.validated_data["employee"]
        assert_org_match(user, customer.organization_id)
        assert_org_match(user, employee.organization_id)
        serializer.save()
