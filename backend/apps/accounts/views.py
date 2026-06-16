from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .emails import send_password_reset_email
from .serializers import (
    ChangePasswordSerializer,
    MeSerializer,
    MouvinTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
)


class MouvinTokenObtainPairView(TokenObtainPairView):
    """Login per E-Mail/Passwort; liefert Access/Refresh + Benutzerinfos."""

    serializer_class = MouvinTokenObtainPairSerializer
    throttle_scope = "login"


class MeView(generics.RetrieveUpdateAPIView):
    """Eigenes Profil lesen/aktualisieren (Name, Telefon)."""

    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Passwort geändert."}, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.get_user()
        if user is not None:
            send_password_reset_email(user, request)
        # Immer gleiche Antwort – keine Offenlegung, ob die E-Mail existiert.
        return Response(
            {"detail": "Falls ein Konto existiert, wurde eine E-Mail versendet."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Passwort wurde zurückgesetzt."}, status=status.HTTP_200_OK)
