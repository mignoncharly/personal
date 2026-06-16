from rest_framework import serializers

from .models import (
    Customer,
    CustomerContract,
    SurchargeRule,
    TravelCostRule,
    TravelDistance,
)


class SurchargeRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurchargeRule
        fields = ("id", "contract", "label", "percent", "is_active")


class TravelCostRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelCostRule
        fields = (
            "id", "contract", "enabled", "rate_per_km", "round_trip",
            "min_amount", "max_amount", "show_on_invoice",
        )


class CustomerContractSerializer(serializers.ModelSerializer):
    """Vertrag inkl. eingebetteter Spezialzuschläge und Fahrkostenregel (lesend)."""

    surcharge_rules = SurchargeRuleSerializer(many=True, read_only=True)
    travel_cost_rule = TravelCostRuleSerializer(read_only=True)

    class Meta:
        model = CustomerContract
        fields = (
            "id", "customer", "valid_from", "is_active",
            "base_hourly_rate",
            "night_surcharge_pct", "saturday_surcharge_pct",
            "sunday_surcharge_pct", "holiday_surcharge_pct",
            "cumulative_surcharges", "night_start", "night_end",
            "invoice_rhythm", "payment_term_days", "vat_rate",
            "surcharge_rules", "travel_cost_rule",
        )


class CustomerSerializer(serializers.ModelSerializer):
    """Kunde inkl. aktivem Vertrag (lesend)."""

    active_contract = CustomerContractSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = (
            "id", "name", "customer_number", "contact_person",
            "street", "zip_code", "city", "bundesland",
            "phone", "fax", "email", "is_active",
            "active_contract", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class CustomerChoiceSerializer(serializers.ModelSerializer):
    """Schlanke Kundenliste zur Auswahl bei der Schichterfassung."""

    class Meta:
        model = Customer
        fields = ("id", "name", "city", "bundesland")


class TravelDistanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.get_full_name", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = TravelDistance
        fields = ("id", "employee", "employee_name", "customer", "customer_name", "one_way_km")
