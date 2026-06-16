from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Shift, ShiftCalculation

User = get_user_model()


class ShiftCalculationSerializer(serializers.ModelSerializer):
    net_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ShiftCalculation
        fields = (
            "total_hours", "break_hours", "paid_hours",
            "night_hours", "saturday_hours", "sunday_hours", "holiday_hours",
            "is_holiday", "holiday_name",
            "base_amount", "night_amount", "saturday_amount", "sunday_amount",
            "holiday_amount", "special_amount", "travel_amount", "net_total",
            "calculated_at",
        )


class ShiftSerializer(serializers.ModelSerializer):
    # Wird im ViewSet gesetzt; Mitarbeiter erfassen für sich selbst, Admin optional für andere.
    employee = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False, allow_null=True
    )
    employee_name = serializers.CharField(source="employee.get_full_name", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    shift_type_display = serializers.CharField(source="get_shift_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    calculation = ShiftCalculationSerializer(read_only=True)

    class Meta:
        model = Shift
        fields = (
            "id", "employee", "employee_name", "customer", "customer_name",
            "shift_type", "shift_type_display", "date",
            "start_time", "end_time", "break_minutes", "note",
            "status", "status_display",
            "created_by", "submitted_at", "reviewed_by", "reviewed_at",
            "correction_reason", "calculation", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "employee_name", "customer_name", "shift_type_display",
            "status_display", "status", "created_by", "submitted_at",
            "reviewed_by", "reviewed_at", "correction_reason", "calculation",
            "created_at", "updated_at",
        )

    def validate_break_minutes(self, value):
        if value < 0:
            raise serializers.ValidationError("Die Pause darf nicht negativ sein.")
        return value

    def validate(self, attrs):
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start is not None and end is not None and start == end:
            raise serializers.ValidationError(
                {"end_time": "Start- und Endzeit dürfen nicht identisch sein."}
            )
        return attrs
