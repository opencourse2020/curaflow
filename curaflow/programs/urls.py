from django.urls import path

from . import views

app_name = "programs"

urlpatterns = [
    # ── Step 1: Program header ──────────────────────────────────────────────
    # Optional ?customer=<pk> pre-selects the customer in the form.
    path("new/", views.ProgramBuilderView.as_view(), name="create"),

    # ── Step 2: Add service items to a draft program ────────────────────────
    path("<int:pk>/items/", views.ProgramItemsView.as_view(), name="items"),

    # ── Detail ──────────────────────────────────────────────────────────────
    # Also handles POST for inline note submission.
    path("<int:pk>/", views.ProgramDetailView.as_view(), name="detail"),

    # ── Edit header ─────────────────────────────────────────────────────────
    path("<int:pk>/edit/", views.ProgramUpdateView.as_view(), name="update"),

    # ── Status transitions ───────────────────────────────────────────────────
    # POST only. Send status=<target> in the request body.
    path("<int:pk>/status/", views.ProgramStatusTransitionView.as_view(), name="status"),
]