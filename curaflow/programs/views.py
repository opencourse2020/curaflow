import logging

from django.contrib import messages
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, UpdateView, View

from curaflow.profiles.mixins import OrganizationRequiredMixin
from curaflow.services.models import Service

from .forms import (
    ProgramForm,
    ProgramNoteForm,
    ProgramUpdateForm,
    build_program_item_formset,
)
from .models import Program, ProgramItem, ProgramNote
from .services import add_program_items, calculate_program_price, create_program

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Program Builder — two-step staged approach
#
# Step 1  GET  /programs/new/?customer=<pk>   → ProgramBuilderView (form)
# Step 2  POST /programs/new/?customer=<pk>   → creates Program, redirects to
#              /programs/<pk>/items/           → ProgramItemsView (formset)
#
# Why staged and not a single giant view?
# - A single POST with both ProgramForm + ProgramItemFormSet means if the
#   item formset fails, the customer selection and program header are also
#   re-rendered with full error state. The staged approach mirrors how
#   a practitioner actually works (decide on the program header, then
#   add services one by one).
# - It also means the ProgramItems page can be revisited independently
#   (adding/removing services on an existing draft program).
# ---------------------------------------------------------------------------


class ProgramBuilderView(OrganizationRequiredMixin, FormView):
    """
    Step 1: fill in the program header (name, customer, dates, objective).
    Submitting this form creates the Program + ProgramCase and redirects
    the user to the items step.
    """

    template_name = "program_builder.html"
    form_class = ProgramForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = self.organization
        # Pre-select customer if passed as a query parameter
        if self.request.method == "GET":
            customer_pk = self.request.GET.get("customer")
            if customer_pk:
                kwargs.setdefault("initial", {})["customer"] = customer_pk
        return kwargs

    def form_valid(self, form):
        cd = form.cleaned_data
        program = create_program(
            organization=self.organization,
            customer=cd["customer"],
            name=cd["name"],
            created_by_user=self.request.user,
            objective_summary=cd.get("objective_summary", ""),
            duration_weeks=cd.get("duration_weeks", 8),
            start_date=cd.get("start_date"),
            end_date=cd.get("end_date"),
            adherence_target=cd.get("adherence_target", 80),
            review_frequency_days=cd.get("review_frequency_days", 7),
        )
        messages.success(
            self.request,
            f'Program "{program.name}" created. Now add services below.',
        )
        return redirect(reverse("programs:items", kwargs={"pk": program.pk}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Expose the active service catalog so the template can render
        # a reference panel alongside the builder form.
        context["available_services"] = (
            Service.objects.filter(organization=self.organization, is_active=True)
            .select_related("category")
            .order_by("category__name", "name")
        )
        context["page_title"] = "New Program"
        return context


class ProgramItemsView(OrganizationRequiredMixin, View):
    """
    Step 2: add / edit the service items for a draft Program.

    GET  → renders the ProgramItem inline formset.
    POST → validates and saves; redirects to ProgramDetailView.
    """

    template_name = "program_builder.html"

    def _get_program(self):
        return get_object_or_404(
            Program,
            pk=self.kwargs["pk"],
            organization=self.organization,
            status=Program.Status.DRAFT,
        )

    def get(self, request, *args, **kwargs):
        from django.shortcuts import render

        program = self._get_program()
        formset = build_program_item_formset(
            organization=self.organization,
            instance=program,
        )
        return render(request, self.template_name, self._build_context(program, formset))

    def post(self, request, *args, **kwargs):
        from django.shortcuts import render

        program = self._get_program()
        formset = build_program_item_formset(
            organization=self.organization,
            instance=program,
            data=request.POST,
        )
        if formset.is_valid():
            add_program_items(program=program, formset=formset)
            calculate_program_price(program)
            messages.success(request, f'"{program.name}" is ready for review.')
            return redirect(reverse("programs:detail", kwargs={"pk": program.pk}))

        # Re-render with errors
        return render(request, self.template_name, self._build_context(program, formset))

    def _build_context(self, program, formset):
        return {
            "program": program,
            "customer": program.customer,
            "formset": formset,
            "available_services": (
                Service.objects.filter(
                    organization=self.organization, is_active=True
                )
                .select_related("category")
                .order_by("category__name", "name")
            ),
            "page_title": f"Add Services — {program.name}",
            "is_items_step": True,
        }


class ProgramDetailView(OrganizationRequiredMixin, DetailView):
    """
    Full program detail: header, all items, notes, pricing summary.
    Also handles POST for adding a ProgramNote inline.
    """

    model = Program
    template_name = "program_builder.html"
    context_object_name = "program"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "customer",
                "program_case",
                "template_used",
                "approved_by__user",
            )
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=ProgramItem.objects.select_related(
                        "service__category",
                        "assigned_staff__user",
                    ).order_by("week_number", "order_index"),
                    to_attr="ordered_items",
                ),
                Prefetch(
                    "notes",
                    queryset=ProgramNote.objects.select_related("author__user")
                    .order_by("-created_at"),
                    to_attr="all_notes",
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["note_form"] = ProgramNoteForm()
        context["page_title"] = self.object.name
        return context

    def post(self, request, *args, **kwargs):
        """Handle inline note submission on the detail page."""
        self.object = self.get_object()
        note_form = ProgramNoteForm(request.POST)
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.program = self.object
            # Resolve Admin profile for author FK; store None if not found
            try:
                note.author = request.user.admin
            except Exception:
                note.author = None
            note.save()
            messages.success(request, "Note added.")
            return redirect(
                reverse("programs:detail", kwargs={"pk": self.object.pk})
            )
        # Re-render detail with invalid note form
        context = self.get_context_data(note_form=note_form)
        return self.render_to_response(context)


class ProgramUpdateView(OrganizationRequiredMixin, UpdateView):
    """
    Edit Program header fields on an existing program.
    Status transitions (DRAFT → APPROVED, ACTIVE → PAUSED, etc.) are
    handled by dedicated action views rather than being exposed here,
    which prevents accidental status regressions via a form field.
    """

    model = Program
    form_class = ProgramUpdateForm
    template_name = "program_builder.html"

    def get_queryset(self):
        return super().get_queryset().select_related("customer")

    def form_valid(self, form):
        program = form.save()
        messages.success(self.request, f'"{program.name}" has been updated.')
        return redirect(reverse("programs:detail", kwargs={"pk": program.pk}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit — {self.object.name}"
        context["is_update"] = True
        return context


# ---------------------------------------------------------------------------
# Status transition views — thin, explicit, no form required
# ---------------------------------------------------------------------------


class ProgramStatusTransitionView(OrganizationRequiredMixin, View):
    """
    POST-only view for advancing a program's status.
    Taking status transitions out of the update form makes them explicit,
    auditable, and impossible to trigger accidentally.

    Supported transitions (enforced here):
        draft       → approved
        approved    → active
        active      → paused
        paused      → active
        active      → completed
        any         → cancelled  (if not already completed)
    """

    ALLOWED_TRANSITIONS = {
        Program.Status.DRAFT:     [Program.Status.APPROVED],
        Program.Status.APPROVED:  [Program.Status.ACTIVE, Program.Status.CANCELLED],
        Program.Status.ACTIVE:    [Program.Status.PAUSED, Program.Status.COMPLETED, Program.Status.CANCELLED],
        Program.Status.PAUSED:    [Program.Status.ACTIVE, Program.Status.CANCELLED],
    }

    def post(self, request, *args, **kwargs):
        program = get_object_or_404(
            Program,
            pk=self.kwargs["pk"],
            organization=self.organization,
        )
        target_status = request.POST.get("status")
        allowed = self.ALLOWED_TRANSITIONS.get(program.status, [])

        if target_status not in allowed:
            messages.error(
                request,
                f"Cannot move a {program.get_status_display()} program to {target_status}.",
            )
            return redirect(reverse("programs:detail", kwargs={"pk": program.pk}))

        program.status = target_status
        program.save(update_fields=["status", "updated_at"])

        logger.info(
            "Program %s transitioned to %s by user %s",
            program.pk,
            target_status,
            request.user.pk,
        )
        messages.success(
            request,
            f'"{program.name}" is now {program.get_status_display()}.',
        )
        return redirect(reverse("programs:detail", kwargs={"pk": program.pk}))