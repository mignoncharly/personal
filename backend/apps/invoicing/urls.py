from django.urls import path
from rest_framework.routers import DefaultRouter

from .reports import ReportView
from .views import InvoiceViewSet

router = DefaultRouter()
router.register("invoices", InvoiceViewSet)

urlpatterns = [
    path("reports/", ReportView.as_view(), name="reports"),
    *router.urls,
]
