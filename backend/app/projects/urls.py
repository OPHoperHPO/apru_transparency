from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet, ComplaintViewSet, DashboardStatsAPIView
)
router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="projects")
router.register(r"complaints", ComplaintViewSet, basename="complaints")
urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/stats/", DashboardStatsAPIView.as_view(), name="dashboard-stats"),
]
