from django.urls import path

from .views import CurrentOrganizationView

app_name = "organizations"

urlpatterns = [
    path("organization/", CurrentOrganizationView.as_view(), name="current-organization"),
]
