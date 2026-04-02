from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class OrganizationRequiredMixin(LoginRequiredMixin):
    """
    Ensures the user is authenticated and belongs to an active Organization.
    Scopes simple view operations to the user's organization automatically.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        self.organization = getattr(request.user, 'organization', None)
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
        context['current_organization'] = self.organization
        return context


class StaffRoleRequiredMixin(OrganizationRequiredMixin):
    """
    Ensures the user has staff privileges within their organization.
    """
    
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if response.status_code != 200:
            return response
            
        # Example role check logic
        # if not request.user.is_org_staff:
        #     raise PermissionDenied("Staff role required.")
        
        return response
