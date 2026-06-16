from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import EmployeeProfile

User = get_user_model()


class EmployeeSerializer(serializers.ModelSerializer):
    """Mitarbeiter = User (Login) + EmployeeProfile in einer Ressource.

    Beim Anlegen wird ein User mit Rolle 'employee' erstellt. Wird kein Passwort
    übergeben, erhält der User ein unbrauchbares Passwort und meldet sich per
    Passwort-Reset erstmalig an.
    """

    # User-Felder (flach abgebildet, lesen+schreiben über die Relation)
    email = serializers.EmailField(source="user.email")
    first_name = serializers.CharField(source="user.first_name", allow_blank=True, required=False)
    last_name = serializers.CharField(source="user.last_name", allow_blank=True, required=False)
    phone = serializers.CharField(source="user.phone", allow_blank=True, required=False)
    password = serializers.CharField(write_only=True, required=False)
    full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = (
            "id", "user_id", "email", "first_name", "last_name", "phone", "password",
            "full_name", "qualification", "street", "zip_code", "city", "is_active",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "user_id", "full_name", "created_at", "updated_at")

    def validate_email(self, value):
        qs = User.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise serializers.ValidationError("Diese E-Mail-Adresse wird bereits verwendet.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        user_data = validated_data.pop("user", {})
        password = validated_data.pop("password", None)
        user = User(role=User.Role.EMPLOYEE, **user_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return EmployeeProfile.objects.create(user=user, **validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        password = validated_data.pop("password", None)
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        if password:
            user.set_password(password)
        user.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
