from django.urls import path

from . import views

app_name = "scheduling"

urlpatterns = [
    # ── Tracking overview for a specific program ─────────────────────────
    path("programs/<int:pk>/", views.TrackingOverviewView.as_view(), name="tracking"),

    # ── Appointment status update ─────────────────────────────────────────
    path(
        "appointments/<int:pk>/update/",
        views.AppointmentUpdateView.as_view(),
        name="appointment_update",
    ),

    # ── Session execution record (GET form + POST save) ───────────────────
    path(
        "appointments/<int:pk>/execute/",
        views.SessionExecutionUpdateView.as_view(),
        name="session_execute",
    ),

    # ── Alert acknowledge/resolve/dismiss (POST only) ─────────────────────
    path(
        "alerts/<int:pk>/acknowledge/",
        views.AlertAcknowledgeView.as_view(),
        name="alert_acknowledge",
    ),
]
