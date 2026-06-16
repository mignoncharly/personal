from datetime import date as date_cls

from rest_framework import serializers

from apps.customers.models import Customer

from .models import Invoice, InvoiceLine


class InvoiceLineSerializer(serializers.ModelSerializer):
    line_type_display = serializers.CharField(source="get_line_type_display", read_only=True)

    class Meta:
        model = InvoiceLine
        fields = (
            "id", "position", "line_type", "line_type_display", "description",
            "quantity_hours", "factor", "amount",
        )


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    due_date = serializers.DateField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    shift_count = serializers.IntegerField(source="shifts.count", read_only=True)

    class Meta:
        model = Invoice
        fields = (
            "id", "number", "sequence", "customer", "customer_name",
            "invoice_date", "period_start", "period_end", "due_date",
            "status", "status_display", "sent_at", "paid_at", "last_reminded_at",
            "is_overdue", "is_small_business",
            "subtotal_net", "vat_rate", "vat_amount", "total_gross",
            "payment_term_days", "pdf_file", "shift_count", "lines",
            "created_at",
        )
        read_only_fields = fields


class InvoiceGenerateSerializer(serializers.Serializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    invoice_date = serializers.DateField(required=False)

    def validate(self, attrs):
        if attrs["period_start"] > attrs["period_end"]:
            raise serializers.ValidationError(
                {"period_end": "Das Enddatum darf nicht vor dem Startdatum liegen."}
            )
        attrs.setdefault("invoice_date", date_cls.today())
        return attrs
