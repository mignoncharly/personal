"""Auth-Endpunkte: Throttling von Login und Passwort-Reset.

Geprüft wird die real konfigurierte Drosselung (DEFAULT_THROTTLE_RATES in
config.settings: login 10/min, password_reset 5/hour). Wir senden mehr Anfragen
als erlaubt und erwarten ein 429.
"""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()  # Drossel-Historie pro Test zurücksetzen
        User.objects.create_user(email="u@example.com", password="pw-secret-123")

    def tearDown(self):
        cache.clear()

    def test_login_is_throttled_after_repeated_attempts(self):
        codes = [
            self.client.post(
                "/api/auth/token/", {"email": "u@example.com", "password": "wrong"}
            ).status_code
            for _ in range(15)
        ]
        # Anfangs normale Fehlversuche, danach Drosselung.
        self.assertEqual(codes[0], status.HTTP_401_UNAUTHORIZED)
        self.assertIn(status.HTTP_429_TOO_MANY_REQUESTS, codes)

    def test_password_reset_is_throttled_after_repeated_requests(self):
        codes = [
            self.client.post(
                "/api/auth/password/reset/", {"email": "u@example.com"}
            ).status_code
            for _ in range(8)
        ]
        self.assertEqual(codes[0], status.HTTP_200_OK)
        self.assertIn(status.HTTP_429_TOO_MANY_REQUESTS, codes)


class AuthFlowTests(APITestCase):
    """Login, /auth/me/, Passwortwechsel und Passwort-Reset-Flow."""

    @classmethod
    def setUpTestData(cls):
        from apps.organizations.models import Organization

        cls.org = Organization.objects.create(name="Firma A", slug="firma-a")
        cls.user = User.objects.create_user(
            email="user@firma.de", password="pw-secret-123",
            first_name="Erika", last_name="Muster", organization=cls.org,
        )

    def setUp(self):
        cache.clear()

    def test_login_returns_tokens_and_org(self):
        res = self.client.post(
            "/api/auth/token/", {"email": "user@firma.de", "password": "pw-secret-123"}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertIn("access", res.data)
        self.assertEqual(res.data["user"]["organization"]["slug"], "firma-a")

    def test_me_returns_profile(self):
        self.client.force_authenticate(self.user)
        res = self.client.get("/api/auth/me/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], "user@firma.de")
        self.assertEqual(res.data["organization"]["name"], "Firma A")

    def test_change_password(self):
        self.client.force_authenticate(self.user)
        res = self.client.post(
            "/api/auth/password/change/",
            {"old_password": "pw-secret-123", "new_password": "neu-secret-456"},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("neu-secret-456"))

    def test_change_password_wrong_old(self):
        self.client.force_authenticate(self.user)
        res = self.client.post(
            "/api/auth/password/change/",
            {"old_password": "falsch", "new_password": "neu-secret-456"},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_flow(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        self.client.post("/api/auth/password/reset/", {"email": "user@firma.de"})
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        res = self.client.post(
            "/api/auth/password/reset/confirm/",
            {"uid": uid, "token": token, "new_password": "reset-secret-789"},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("reset-secret-789"))
