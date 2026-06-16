"""
Django settings for Schichtwerk (Schicht- & Rechnungssystem).

Configuration is read from environment variables (.env) via django-environ.
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000", "http://127.0.0.1:3000"]),
)
environ.Env.read_env(BASE_DIR / ".env")

# --- Core ---------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me-in-env")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# --- Applications -------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.organizations",
    "apps.accounts",
    "apps.customers",
    "apps.employees",
    "apps.shifts",
    "apps.invoicing",
    "apps.common",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Database -----------------------------------------------------------
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}

# --- Auth ---------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- DRF & JWT ----------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    # ScopedRateThrottle greift nur bei Views mit gesetztem `throttle_scope`
    # (z. B. Login, Passwort-Reset) – alle anderen Endpunkte bleiben ungedrosselt.
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "login": env("THROTTLE_LOGIN", default="10/min"),
        "password_reset": env("THROTTLE_PASSWORD_RESET", default="5/hour"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=60)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=7)),
}

# --- CORS & CSRF --------------------------------------------------------
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# --- Sicherheit (greift in Produktion, DEBUG=False) ---------------------
if not DEBUG:
    # Nginx terminiert TLS und setzt X-Forwarded-Proto.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
    SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)

# --- Internationalization ----------------------------------------------
LANGUAGE_CODE = "de-de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True

# --- Static, Media & Rechnungs-PDFs -------------------------------------
# Alle Speicherorte sind per env überschreibbar; in Produktion liegen sie
# unter dem app-eigenen Ordner storage/ (getrennt von anderen Apps).
STORAGE_DIR = Path(env("STORAGE_DIR", default=str(BASE_DIR)))

STATIC_URL = "static/"
STATIC_ROOT = Path(env("STATIC_ROOT", default=str(STORAGE_DIR / "staticfiles")))
MEDIA_URL = "media/"
MEDIA_ROOT = Path(env("MEDIA_ROOT", default=str(STORAGE_DIR / "media")))

# Rechnungs-PDFs in eigenem Verzeichnis (nicht mit media vermischt)
INVOICE_ROOT = Path(env("INVOICE_ROOT", default=str(STORAGE_DIR / "invoices")))
INVOICE_URL = env("INVOICE_URL", default="/invoices/")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Logging ------------------------------------------------------------
LOG_DIR = env("LOG_DIR", default="")
if LOG_DIR:
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {"format": "{asctime} {levelname} {name} {message}", "style": "{"},
        },
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(Path(LOG_DIR) / "backend.log"),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "verbose",
            },
            "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        },
        "root": {"handlers": ["file", "console"], "level": "INFO"},
        "loggers": {
            "django": {"handlers": ["file", "console"], "level": "INFO", "propagate": False},
        },
    }

# --- E-Mail (SMTP) ------------------------------------------------------
if env.bool("EMAIL_USE_CONSOLE", default=True):
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = env("EMAIL_HOST", default="")
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="infos@mouvinpersonal.de")

# Basis-URL des Frontends für Links in E-Mails (Einladung, Passwort-Reset).
# Wird genutzt, wenn die Anfrage keinen Origin-Header trägt (z. B. serverseitig
# ausgelöste Mails). Fällt sonst auf die erste erlaubte CORS-Origin zurück.
FRONTEND_BASE_URL = env(
    "FRONTEND_BASE_URL",
    default=(CORS_ALLOWED_ORIGINS[0] if CORS_ALLOWED_ORIGINS else ""),
)

# --- Firmenstammdaten (für Rechnungen, Phase 9) ------------------------
COMPANY = {
    "name": "Mouvin Personal Dienstleistungs GmbH",
    "street": "Rheinstrasse 15",
    "zip_city": "65185 Wiesbaden",
    "phone": "01791449049",
    "email": "infos@mouvinpersonal.de",
    "vat_id": "DE123456789",
    "iban": "DE19 0000 0100 0000 0000 00",
    "bic": "000000XXX",
    "vat_rate": "19",
}

# --- Fehler-Monitoring (Sentry) ----------------------------------------
# Nur aktiv, wenn SENTRY_DSN gesetzt ist – lokal/CI bleibt es aus.
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment=env("SENTRY_ENVIRONMENT", default="production"),
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),
        send_default_pii=False,
    )
