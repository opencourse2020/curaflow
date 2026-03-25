from django.urls import path

from . import views

app_name = "services"

urlpatterns = [
    # ── List ────────────────────────────────────────────────────────────────
    path("", views.ServiceListView.as_view(), name="list"),

    # ── Create ──────────────────────────────────────────────────────────────
    path("new/", views.ServiceCreateView.as_view(), name="create"),

    # ── Update ──────────────────────────────────────────────────────────────
    path("<int:pk>/edit/", views.ServiceUpdateView.as_view(), name="update"),
]