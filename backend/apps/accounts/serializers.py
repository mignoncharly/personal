from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Anzeige/Bearbeitung von Benutzern (Admin) bzw. eigenem Profil."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "email", "first_name", "last_name", "full_name",
            "role", "phone", "is_active", "date_joined", "last_login",
        )
        read_only_fields = ("id", "date_joined", "last_login")

    def get_full_name(self, obj) -> str:
        return obj.get_full_name()


class MeSerializer(serializers.ModelSerializer):
    """Eigenes Profil – Rolle ist hier schreibgeschützt."""

    full_name = serializers.SerializerMethodField()
    is_admin = serializers.BooleanField(read_only=True)
    organization = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "email", "first_name", "last_name", "full_name",
            "role", "is_admin", "phone", "organization",
        )
        read_only_fields = ("id", "email", "role", "is_admin")

    def get_full_name(self, obj) -> str:
        return obj.get_full_name()

    def get_organization(self, obj):
        org = obj.organization
        if org is None:
            return None
        return {"id": org.id, "name": org.name, "slug": org.slug}


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Das aktuelle Passwort ist falsch.")
        return value

    def validate_new_password(self, value):
        validate_password(value, self.context["request"].user)
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Fordert einen Reset-Token an. Aus Sicherheitsgründen wird die Existenz
    der E-Mail nicht offengelegt; der Token wird nur bei vorhandenem Konto erzeugt."""

    email = serializers.EmailField()

    def get_user(self):
        return User.objects.filter(email__iexact=self.validated_data["email"], is_active=True).first()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            raise serializers.ValidationError({"uid": "Ungültiger Link."})

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "Token ungültig oder abgelaufen."})

        validate_password(attrs["new_password"], user)
        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class MouvinTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT-Login: ergänzt Rolle/Name im Token und in der Antwort."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["name"] = user.get_full_name()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        org = self.user.organization
        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "role": self.user.role,
            "full_name": self.user.get_full_name(),
            "is_admin": self.user.is_admin,
            "organization": (
                {"id": org.id, "name": org.name, "slug": org.slug} if org else None
            ),
        }
        return data
