import logging

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Prefetch
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from curaflow.profiles.mixins import OrganizationRequiredMixin

from .forms import ServiceForm, ServiceSearchForm
from .models import Service, ServiceCategory, ServiceStaffAssignment

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Module-level Prefetch objects — built once, reused on every request.
# staff_assignments prefetches both the Admin row and the User it points to
# so templates can display a staff member's name without extra queries.
# ---------------------------------------------------------------------------
_STAFF_ASSIGNMENT_PREFETCH = Prefetch(
    "staff_assignments",
    queryset=ServiceStaffAssignment.objects.select_related(
        "staff__user"
    ).order_by("-is_primary"),
    to_attr="prefetched_staff",
)


class ServiceListView(OrganizationRequiredMixin, ListView):
    """
    Paginated list of all services for the current organization.

    Provides context sufficient to render the services card/table:
      - category name
      - duration, price
      - primary assigned staff
      - contraindication count (via annotation)
      - active / archived status (is_active field from SoftDeleteModel)
    """

    model = Service
    template_name = "services.html"
    context_object_name = "services"
    paginate_by = 30

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("category", "location")
            .prefetch_related(_STAFF_ASSIGNMENT_PREFETCH)
            .annotate(contraindication_count=Count("contraindications", distinct=True))
        )

        form = ServiceSearchForm(self.request.GET, organization=self.organization)
        if form.is_valid():
            q = form.cleaned_data.get("q", "").strip()
            category = form.cleaned_data.get("category")
            is_active = form.cleaned_data.get("is_active", "")

            if q:
                from django.db.models import Q
                qs = qs.filter(
                    Q(name__icontains=q) | Q(code__icontains=q)
                )
            if category:
                qs = qs.filter(category=category)
            if is_active == "1":
                qs = qs.filter(is_active=True)
            elif is_active == "0":
                qs = qs.filter(is_active=False)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = ServiceSearchForm(
            self.request.GET, organization=self.organization
        )
        context["categories"] = ServiceCategory.objects.filter(
            organization=self.organization,
            is_active=True,
        ).order_by("name")
        context["total_active"] = (
            Service.objects.filter(organization=self.organization, is_active=True).count()
        )
        return context


class ServiceCreateView(OrganizationRequiredMixin, CreateView):
    """
    Create a new Service scoped to the current organization.

    The `organization` kwarg is passed to ServiceForm.__init__ so that
    the category and location dropdowns are restricted to this tenant.
    """

    model = Service
    form_class = ServiceForm
    template_name = "service_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pass organization into the form so it can scope FK querysets
        kwargs["organization"] = self.organization
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            service = form.save(commit=False)
            service.organization = self.organization
            service.save()

        logger.info(
            "Service %s (%s) created in org %s by user %s",
            service.pk,
            service.name,
            self.organization.pk,
            self.request.user.pk,
        )
        messages.success(self.request, f'"{service.name}" has been created.')
        self.object = service
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("services:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Add Service"
        return context


class ServiceUpdateView(OrganizationRequiredMixin, UpdateView):
    """
    Update an existing Service.

    get_queryset() is already org-scoped via OrganizationRequiredMixin,
    so a user in org A cannot update a service belonging to org B —
    they will receive a 404.
    """

    model = Service
    form_class = ServiceForm
    template_name = "service_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = self.organization
        return kwargs

    def form_valid(self, form):
        with transaction.atomic():
            service = form.save()

        messages.success(self.request, f'"{service.name}" has been updated.')
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("services:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit — {self.object.name}"
        context["is_update"] = True
        return context