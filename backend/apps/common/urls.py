from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AuditLogViewSet, SystemStatusView

router = DefaultRouter()
router.register("audit-log", AuditLogViewSet, basename="audit-log")

urlpatterns = [
    path("system/status/", SystemStatusView.as_view(), name="system-status"),
    *router.urls,
]
