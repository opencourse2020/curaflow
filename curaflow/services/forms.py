from django import forms

from curaflow.profiles.models import Admin

from .models import Service, ServiceCategory


class ServiceForm(forms.ModelForm):
    """
    Create and update form for Service.

    `organization` is excluded and injected in the view to prevent
    mass-assignment — the same pattern used in CustomerForm.

    The `category` and `location` querysets are unscoped here and MUST be
    restricted in the view by calling `form.fields[...].queryset = ...`
    after form instantiation (see ServiceCreateView / ServiceUpdateView).
    """

    class Meta:
        model = Service
        fields = [
            "name",
            "code",
            "category",
            "short_description",
            "description",
            "duration_minutes",
            "default_frequency_per_week",
            "intensity_level",
            "delivery_mode",
            "location",
            "base_price",
            "currency",
            "requires_staff_assignment",
            "requires_medical_clearance",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "short_description": forms.TextInput(),
            "intensity_level": forms.Select(),
            "delivery_mode": forms.Select(),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Scope FK dropdowns to the current organization so a staff member
        # cannot select resources from another tenant.
        if organization is not None:
            self.fields["category"].queryset = ServiceCategory.objects.filter(
                organization=organization,
                is_active=True,
            )
            # Location is also org-scoped — import inline to avoid a circular
            # import at module level between services and profiles apps.
            from curaflow.profiles.models import Location

            self.fields["location"].queryset = Location.objects.filter(
                organization=organization,
                is_active=True,
            )
        self.fields["name"].required = True

    def clean_duration_minutes(self):
        value = self.cleaned_data.get("duration_minutes")
        if value is not None and value < 5:
            raise forms.ValidationError("Duration must be at least 5 minutes.")
        return value

    def clean_base_price(self):
        value = self.cleaned_data.get("base_price")
        if value is not None and value < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return value


class ServiceCategoryForm(forms.ModelForm):
    """
    Lightweight form for creating a ServiceCategory inline.
    `organization` injected in the view.
    """

    class Meta:
        model = ServiceCategory
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
        }


class ServiceSearchForm(forms.Form):
    """
    Stateless search / filter form for ServiceListView (GET only).
    """

    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={"placeholder": "Service name or code…"}),
    )
    category = forms.ModelChoiceField(
        required=False,
        label="Category",
        queryset=ServiceCategory.objects.none(),  # scoped at view level
        empty_label="All categories",
    )
    is_active = forms.ChoiceField(
        required=False,
        label="Status",
        choices=[
            ("", "All"),
            ("1", "Active"),
            ("0", "Archived"),
        ],
    )

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization is not None:
            self.fields["category"].queryset = ServiceCategory.objects.filter(
                organization=organization,
                is_active=True,
            )
