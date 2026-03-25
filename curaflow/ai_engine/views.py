import logging

from django.contrib import messages
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, View

from curaflow.core.mixins import OrganizationRequiredMixin
from curaflow.core.services import ServiceException
from curaflow.customers.models import Customer
from curaflow.programs.models import ProgramCase

from .models import (
    EvidenceSource,
    RecommendationDecision,
    RecommendationOption,
    RecommendationRun,
)
from .services import (
    build_input_snapshot,
    initiate_run,
    record_decision,
    trigger_recommendation_run,
)

logger = logging.getLogger(__name__)


class RecommendationDetailView(OrganizationRequiredMixin, DetailView):
    """
    Render the full recommendation page for a completed or needs-review run.

    Provides context for:
      - customer snapshot (profile, goals, active conditions)
      - recommendation summary (run status, model, timing)
      - all options ordered by rank, each with their service items
      - evidence sources
      - current decision state (approved / rejected / none)
    """

    model = RecommendationRun
    template_name = "recommendation.html"
    context_object_name = "run"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "customer__profile",
                "program_case",
                "triggered_by",
            )
            .prefetch_related(
                # Options and their service items in one pass
                Prefetch(
                    "options",
                    queryset=RecommendationOption.objects.prefetch_related(
                        Prefetch(
                            "items",
                            queryset=(
                                __import__(
                                    "curaflow.ai_engine.models",
                                    fromlist=["RecommendationOptionItem"],
                                ).RecommendationOptionItem.objects
                                .select_related("service__category")
                                .order_by("order_index")
                            ),
                        )
                    ).order_by("rank"),
                    to_attr="ordered_options",
                ),
                # Evidence sources
                Prefetch(
                    "evidence_sources",
                    queryset=EvidenceSource.objects.order_by("-trust_score", "title"),
                    to_attr="ordered_evidence",
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        run = self.object
        customer = run.customer

        # Customer snapshot — goals and conditions already cached on customer
        # via prefetch_related in get_queryset above
        context["customer"] = customer
        context["customer_profile"] = getattr(customer, "profile", None)
        context["customer_goals"] = list(
            customer.goals.select_related("goal").order_by("priority")[:6]
        )
        context["customer_conditions"] = list(
            customer.medical_conditions.filter(status="active")
            .select_related("medical_condition")
        )

        # Options and evidence (served from to_attr prefetch — no extra query)
        context["options"] = getattr(run, "ordered_options", [])
        context["evidence_sources"] = getattr(run, "ordered_evidence", [])

        # Decision state
        context["decision"] = getattr(run, "decision", None)
        # Safely try the OneToOne relation
        if context["decision"] is None:
            try:
                context["decision"] = run.decision
            except RecommendationDecision.DoesNotExist:
                context["decision"] = None

        # Top option (rank=1) for the summary panel
        context["top_option"] = context["options"][0] if context["options"] else None

        # Decision choices for the action buttons / form
        context["decision_choices"] = RecommendationDecision.Decision.choices

        context["page_title"] = f"Recommendation — {customer}"
        return context


class RecommendationGenerateView(OrganizationRequiredMixin, View):
    """
    POST-only view that initiates a new RecommendationRun for a given
    ProgramCase + Customer.

    On success, redirects to the detail view of the newly created run.

    Expected POST parameters
    ------------------------
    customer_pk   : int
    program_case_pk : int
    """

    def post(self, request, *args, **kwargs):
        customer_pk = request.POST.get("customer_pk")
        program_case_pk = request.POST.get("program_case_pk")

        customer = get_object_or_404(
            Customer,
            pk=customer_pk,
            organization=self.organization,
        )
        program_case = get_object_or_404(
            ProgramCase,
            pk=program_case_pk,
            organization=self.organization,
        )

        try:
            run = initiate_run(
                organization=self.organization,
                customer=customer,
                program_case=program_case,
                triggered_by_user=request.user,
            )
            build_input_snapshot(run=run, customer=customer)
            trigger_recommendation_run(run=run)

        except ServiceException as exc:
            messages.error(request, str(exc))
            return redirect(
                reverse("programs:detail", kwargs={"pk": program_case_pk})
            )

        messages.success(
            request,
            "Recommendation run initiated. Review the options below.",
        )
        return redirect(reverse("ai_engine:detail", kwargs={"pk": run.pk}))


class RecommendationApproveView(OrganizationRequiredMixin, View):
    """
    POST-only view for recording a clinician's decision on a run.

    Accepts:
        decision          — one of RecommendationDecision.Decision values
        selected_option   — PK of the chosen RecommendationOption (optional)
        review_notes      — free text (optional)

    On approval, if a selected_option is provided the service layer will
    record it.  Program creation from the approved option is intentionally
    left as a separate step (handled by ProgramBuilderView with pre-filled
    data) to keep this view's responsibility narrow.
    """

    def post(self, request, *args, **kwargs):
        run = get_object_or_404(
            RecommendationRun,
            pk=self.kwargs["pk"],
            organization=self.organization,
        )

        decision_value = request.POST.get("decision", "")
        selected_option_pk = request.POST.get("selected_option_pk")
        review_notes = request.POST.get("review_notes", "").strip()

        selected_option = None
        if selected_option_pk:
            selected_option = get_object_or_404(
                RecommendationOption,
                pk=selected_option_pk,
                recommendation_run=run,
            )

        # Resolve the reviewer's Admin profile; gracefully store None if absent
        reviewed_by_admin = None
        try:
            reviewed_by_admin = request.user.admin
        except Exception:
            pass

        try:
            record_decision(
                run=run,
                decision_value=decision_value,
                selected_option=selected_option,
                reviewed_by_admin=reviewed_by_admin,
                review_notes=review_notes,
            )
        except ServiceException as exc:
            messages.error(request, str(exc))
            return redirect(reverse("ai_engine:detail", kwargs={"pk": run.pk}))

        messages.success(
            request,
            f"Decision recorded: {decision_value.replace('_', ' ').title()}.",
        )
        return redirect(reverse("ai_engine:detail", kwargs={"pk": run.pk}))
