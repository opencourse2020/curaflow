from django.urls import include, path

from . import views

app_name = "metrics"

urlpatterns = [
    # ── Analytics dashboard shell ─────────────────────────────────────────
    path("", views.AnalyticsDashboardView.as_view(), name="dashboard"),

    # ── DRF chart data endpoints ──────────────────────────────────────────
    # Namespaced separately so they can be prefixed under /metrics/api/
    path("api/", include("curaflow.metrics.api.urls", namespace="metrics_api")),
]
