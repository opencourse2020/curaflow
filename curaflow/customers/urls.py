from django.urls import path

from . import views

app_name = "customers"

urlpatterns = [
    # ── List ────────────────────────────────────────────────────────────────
    path("", views.CustomerListView.as_view(), name="list"),

    # ── Create ──────────────────────────────────────────────────────────────
    path("new/", views.CustomerCreateView.as_view(), name="create"),

    # ── Detail ──────────────────────────────────────────────────────────────
    path("<int:pk>/", views.CustomerDetailView.as_view(), name="detail"),

    # ── Update ──────────────────────────────────────────────────────────────
    path("<int:pk>/edit/", views.CustomerUpdateView.as_view(), name="update"),
]