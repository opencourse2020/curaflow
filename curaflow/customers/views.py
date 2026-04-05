import logging

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from curaflow.profiles.mixins import OrganizationRequiredMixin
from curaflow.metrics.models import CustomerMetricRecord
from curaflow.programs.models import Program

from .forms import CustomerForm, CustomerProfileForm, CustomerSearchForm
from .models import Customer, CustomerProfile

logger = logging.getLogger(__name__)


class CustomerListView(OrganizationRequiredMixin, ListView):
    """
    Paginated list of customers scoped to the current organization.
    Supports search by name/email/phone and filtering by status.
    """

    model = Customer
    template_name = "customers.html"
    context_object_name = "customers"
    paginate_by = 25

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("profile")
            .order_by("first_name", "last_name")
        )
        for cusg in qs.customergoal_set.all:
            print(cusg)
        form = CustomerSearchForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data.get("q", "").strip()
            status = form.cleaned_data.get("status", "")

            if q:
                qs = qs.filter(
                    first_name__icontains=q
                ) | qs.filter(
                    last_name__icontains=q
                ) | qs.filter(
                    email__icontains=q
                ) | qs.filter(
                    phone__icontains=q
                )
                # Re-scope to org after OR union (union can escape org scope)
                qs = qs.filter(organization=self.organization)

            if status:
                qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = CustomerSearchForm(self.request.GET)
        context["status_choices"] = Customer.Status.choices
        context["total_count"] = Customer.objects.filter(
            organization=self.organization
        ).count()
        return context


class CustomerDetailView(OrganizationRequiredMixin, DetailView):
    """
    Full customer profile view including health data, active programs,
    recent assessments, goals, medical conditions, and metric records.

    Heavy use of prefetch_related to avoid N+1 queries across all the
    related objects rendered in the customer profile template.
    """

    model = Customer
    template_name = "customer_profile.html"
    context_object_name = "customer"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("profile")
            .prefetch_related(
                "goals__goal",
                "medical_conditions__medical_condition",
                "injuries__injury",
                "allergies__allergy",
                "medications__medication",
                "assessments__assessed_by",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.object

        # Active and recent programs — scoped via the customer FK which is
        # already org-scoped, so a secondary org filter is not needed here.
        context["active_programs"] = (
            Program.objects.filter(
                customer=customer,
                status__in=[Program.Status.ACTIVE, Program.Status.APPROVED],
            )
            .select_related("template_used", "approved_by")
            .order_by("-created_at")[:5]
        )

        context["recent_programs"] = (
            Program.objects.filter(customer=customer)
            .exclude(status=Program.Status.ACTIVE)
            .select_related("template_used")
            .order_by("-created_at")[:3]
        )

        # Recent assessments (most recent 5)
        context["recent_assessments"] = (
            customer.assessments.select_related("assessed_by")
            .order_by("-created_at")[:5]
        )

        # Recent metric records (most recent 10 across all metric types)
        context["recent_metrics"] = (
            CustomerMetricRecord.objects.filter(customer=customer)
            .select_related("metric_type", "program")
            .order_by("-recorded_at")[:10]
        )

        # Goals ordered by priority
        context["goals"] = customer.goals.select_related("goal").order_by("priority")

        # Active medical conditions only
        context["active_conditions"] = customer.medical_conditions.filter(
            status="active"
        ).select_related("medical_condition")

        # Profile (may be None if not yet created)
        context["profile"] = getattr(customer, "profile", None)

        return context


class CustomerCreateView(OrganizationRequiredMixin, CreateView):
    """
    Creates a new Customer record and its associated CustomerProfile
    within a single atomic transaction.
    """

    model = Customer
    form_class = CustomerForm
    template_name = "customer_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Supply a profile form so the template can render both forms at once
        if self.request.POST:
            context["profile_form"] = CustomerProfileForm(self.request.POST)
        else:
            context["profile_form"] = CustomerProfileForm()
        return context

    def form_valid(self, form):
        profile_form = CustomerProfileForm(self.request.POST)
        if not profile_form.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            # Inject organization before saving — never trust form input
            customer = form.save(commit=False)
            customer.organization = self.organization
            customer.save()

            # Create the linked profile record
            profile = profile_form.save(commit=False)
            profile.customer = customer
            profile.save()

        logger.info(
            "Customer created: %s (org=%s, by=%s)",
            customer.pk,
            self.organization.pk,
            self.request.user.pk,
        )
        messages.success(
            self.request,
            f"{customer} has been added successfully.",
        )
        return redirect(self.get_success_url(customer))

    def get_success_url(self, customer=None):
        if customer:
            from django.urls import reverse
            return reverse("customers:detail", kwargs={"pk": customer.pk})
        return reverse_lazy("customers:list")


class CustomerUpdateView(OrganizationRequiredMixin, UpdateView):
    """
    Updates an existing Customer and their CustomerProfile together.
    Retrieves only customers belonging to the current organization via
    the scoped queryset from OrganizationRequiredMixin.
    """

    model = Customer
    form_class = CustomerForm
    template_name = "customer_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = getattr(self.object, "profile", None)
        if self.request.POST:
            context["profile_form"] = CustomerProfileForm(
                self.request.POST, instance=profile
            )
        else:
            context["profile_form"] = CustomerProfileForm(instance=profile)
        context["is_update"] = True
        return context

    def form_valid(self, form):
        profile_instance = getattr(self.object, "profile", None)
        profile_form = CustomerProfileForm(
            self.request.POST, instance=profile_instance
        )
        if not profile_form.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            customer = form.save()

            profile = profile_form.save(commit=False)
            if not profile_instance:
                # Profile didn't exist yet — create it now
                profile.customer = customer
            profile.save()

        messages.success(self.request, f"{customer} has been updated.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("customers:detail", kwargs={"pk": self.object.pk})