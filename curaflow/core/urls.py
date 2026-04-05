from django.urls import path, include
from . import views

app_name = "core"


urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("recommendation/", views.RecommendationView.as_view(), name="recommendation"),
    path("analytics/", views.AnalyticsView.as_view(), name="analytics"),
    path("tracking/", views.TrackingView.as_view(), name="tracking"),
# Main settings entry point
    path("settings/", views.SettingsView.as_view(), name="settings"),
    # Organization Profile & Config
    path("settings/organization/", views.OrganizationUpdateView.as_view(), name="settings_organization"),
    path("settings/preferences/", views.OrganizationSettingsUpdateView.as_view(), name="settings_preferences"),

    # Locations Management
    path("settings/locations/", views.LocationListView.as_view(), name="settings_locations"),
    path("settings/locations/new/", views.LocationCreateView.as_view(), name="settings_location_create"),
    ]