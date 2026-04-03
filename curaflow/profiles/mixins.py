from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.urls import reverse_lazy


class JsonFormMixin:
    def form_valid(self, form):
        self.object = form.save()
        return JsonResponse(form.data)

    def form_invalid(self, form):
        data = {
            "success": False,
            "errors": {k: v[0] for k, v in form.errors.items()},
        }
        return JsonResponse(data, status=400)


class MemberRequiredMixin(PermissionRequiredMixin):
    permission_required = "profiles.access_member_pages"
    login_url = reverse_lazy("profiles:403")


class AdminRequiredMixin(PermissionRequiredMixin):
    permission_required = "profiles.access_admin_pages"
    login_url = reverse_lazy("profiles:403")


class AdminAllowedMixing(PermissionRequiredMixin):
    permission_required = ("", "", "", "", "")
    login_url = reverse_lazy("profiles:403")


class OrganizationRequiredMixin(LoginRequiredMixin):
    """
    Ensures the user is authenticated and belongs to an active Organization.
    Scopes simple view operations to the user's organization automatically.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        # getattr(request.user, 'organization', None)

        # org = request.user.profile.organization
        self.organization = getattr(request.user.profile, 'organization', None)

        if not self.organization:
            # Optionally redirect to an organization creation page
            raise PermissionDenied("You must belong to an organization to access this.")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Attempts to automatically scope querysets to the current organization.
        Assumes the model has an `organization` foreign key.
        Override this method if the scoping logic is more complex.
        """
        qs = super().get_queryset()
        if hasattr(qs.model, 'organization'):
            return qs.filter(organization=self.organization)
        return qs

    def get_context_data(self, **kwargs):
        """
        Inject the current organization into the template context.
        """
        context = super().get_context_data(**kwargs)
        print("organization:", self.organization)
        context['current_organization'] = self.organization
        return context
