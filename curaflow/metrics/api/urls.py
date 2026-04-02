from django.urls import path

from . import views

# Namespaced as "metrics_api" (registered in metrics/urls.py)
app_name = "metrics_api"

urlpatterns = [
    # Weekly adherence rate time-series
    path("adherence-trend/",       views.AdherenceTrendView.as_view(),           name="adherence_trend"),

    # Completion rate grouped by service category
    path("completion-by-category/", views.CompletionRateByCategoryView.as_view(), name="completion_by_category"),

    # Top-N services by session count
    path("service-utilisation/",   views.ServiceUtilisationView.as_view(),        name="service_utilisation"),

    # Weekly dropout risk trend
    path("dropout-risk/",          views.DropoutRiskTrendView.as_view(),          name="dropout_risk"),

    # Weekly average for any CustomerMetricRecord metric type
    # Requires: ?metric=<code>
    path("outcome-trend/",         views.OutcomeTrendView.as_view(),              name="outcome_trend"),
]
