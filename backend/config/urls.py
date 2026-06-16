"""URL configuration for the Schichtwerk backend."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    """Health-Check für Uptime-Monitoring/Load-Balancer; prüft die DB-Verbindung."""
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
    status_code = 200 if db_ok else 503
    return JsonResponse(
        {
            "status": "ok" if db_ok else "degraded",
            "service": "mouvin-backend",
            "database": "ok" if db_ok else "error",
        },
        status=status_code,
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.organizations.urls")),
    path("api/", include("apps.customers.urls")),
    path("api/", include("apps.employees.urls")),
    path("api/", include("apps.shifts.urls")),
    path("api/", include("apps.invoicing.urls")),
    path("api/", include("apps.common.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
