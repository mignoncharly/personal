from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomerChoiceList,
    CustomerContractViewSet,
    CustomerViewSet,
    SurchargeRuleViewSet,
    TravelCostRuleViewSet,
    TravelDistanceViewSet,
)

router = DefaultRouter()
router.register("customers", CustomerViewSet)
router.register("contracts", CustomerContractViewSet)
router.register("surcharge-rules", SurchargeRuleViewSet)
router.register("travel-cost-rules", TravelCostRuleViewSet)
router.register("travel-distances", TravelDistanceViewSet)

urlpatterns = [
    path("customer-choices/", CustomerChoiceList.as_view(), name="customer-choices"),
    *router.urls,
]
