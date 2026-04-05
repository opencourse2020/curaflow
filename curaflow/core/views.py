from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from .models import Organization, OrganizationSettings, Location
from .forms import OrganizationForm, OrganizationSettingsForm, LocationForm

# Assuming core mixins like OrganizationScopedMixin restrict querysets/access
# to the current user's organization via request.organization
from curaflow.profiles.mixins import OrganizationRequiredMixin
# Create your views here.


class HomeView(TemplateView):
    template_name = "landing.html"


class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        raw_data = "72,Wk1|76,Wk2|81,Wk3|79,Wk4|74,Wk5|82,Wk6|85,Wk7|78,Wk8"
        # Create a list of tuples: [('72', 'Wk1'), ('76', 'Wk2'), ...]
        weeks = [item.split(',') for item in raw_data.split('|')]

        kwargs["weeks"] = weeks

        return super(DashboardView, self).get_context_data(**kwargs)


class RecommendationView(TemplateView):
    template_name = "recommendation.html"


class AnalyticsView(TemplateView):
    template_name = "analytics.html"


class TrackingView(TemplateView):
    template_name = "tracking.html"


# class SettingsView(TemplateView):
#     template_name = "settings.html"



class SettingsView(LoginRequiredMixin, OrganizationRequiredMixin, TemplateView):
    """Entry point for the Settings Section, likely showing links/sub-pages."""
    template_name = "core/settings/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.request.organization
        return context


class OrganizationUpdateView(LoginRequiredMixin, OrganizationRequiredMixin, UpdateView):
    """View to update main business profile details."""
    model = Organization
    form_class = OrganizationForm
    template_name = "core/settings/organization_form.html"
    success_url = reverse_lazy("core:settings")

    def get_object(self, queryset=None):
        """Ensure the user can only edit their own organization."""
        return self.request.organization

    def form_valid(self, form):
        messages.success(self.request, "Organization profile updated successfully.")
        return super().form_valid(form)


class OrganizationSettingsUpdateView(LoginRequiredMixin, OrganizationRequiredMixin, UpdateView):
    """View to update functional settings and features for the organization."""
    model = OrganizationSettings
    form_class = OrganizationSettingsForm
    template_name = "core/settings/settings_form.html"
    success_url = reverse_lazy("core:settings")

    def get_object(self, queryset=None):
        """Fetch settings or create default ones if they don't exist yet."""
        settings, created = OrganizationSettings.objects.get_or_create(
            organization=self.request.organization
        )
        return settings

    def form_valid(self, form):
        messages.success(self.request, "Organization preferences updated successfully.")
        return super().form_valid(form)


class LocationListView(LoginRequiredMixin, OrganizationRequiredMixin, ListView):
    """List physical locations associated with the organization."""
    model = Location
    template_name = "core/settings/location_list.html"
    context_object_name = "locations"

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


class LocationCreateView(LoginRequiredMixin, OrganizationRequiredMixin, CreateView):
    """Add a new location to the organization."""
    model = Location
    form_class = LocationForm
    template_name = "core/settings/location_form.html"
    success_url = reverse_lazy("core:settings_locations")

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        messages.success(self.request, "Location added successfully.")
        return super().form_valid(form)

