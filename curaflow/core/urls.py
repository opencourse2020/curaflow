from django.urls import path, include
from . import views

app_name = "core"


urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("recommendation/", views.RecommendationView.as_view(), name="recommendation"),
    path("analytics/", views.AnalyticsView.as_view(), name="analytics"),
    path("tracking/", views.TrackingView.as_view(), name="tracking"),
    path("settings/", views.SettingsView.as_view(), name="settings"),
    ]