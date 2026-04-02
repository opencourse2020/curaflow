from django.urls import path

from . import views

app_name = "ai_engine"

urlpatterns = [
    # ── Detail: view a recommendation run and its options ───────────────────
    path("<int:pk>/", views.RecommendationDetailView.as_view(), name="detail"),

    # ── Generate: POST to initiate a new run for a customer / case ─────────
    # Requires: customer_pk, program_case_pk in POST body.
    path("generate/", views.RecommendationGenerateView.as_view(), name="generate"),

    # ── Approve/Reject/Review: POST to record a decision on a run ──────────
    # Requires: decision, optional selected_option_pk, review_notes in POST.
    path("<int:pk>/decision/", views.RecommendationApproveView.as_view(), name="decision"),
]
