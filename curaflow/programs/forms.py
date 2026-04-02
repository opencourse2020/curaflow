from django import forms
from django.forms import inlineformset_factory

from curaflow.customers.models import Customer
from curaflow.profiles.models import Admin
from curaflow.services.models import Service

from .models import Program, ProgramItem, ProgramNote


class ProgramForm(forms.ModelForm):
    """
    Step 1 of the program builder: header information.

    `customer` queryset is scoped at the view level via __init__.
    `organization` is NEVER accepted from the form — it is injected
    in the service layer after validation.
    """

    class Meta:
        model = Program
        fields = [
            "customer",
            "name",
            "objective_summary",
            "duration_weeks",
            "start_date",
            "end_date",
            "adherence_target",
            "review_frequency_days",
        ]
        widgets = {
            "objective_summary": forms.Textarea(attrs={"rows": 3}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization is not None:
            self.fields["customer"].queryset = Customer.objects.filter(
                organization=organization,
                status=Customer.Status.ACTIVE,
                is_active=True,
            ).order_by("first_name", "last_name")
        self.fields["name"].required = True
        self.fields["customer"].required = True

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end <= start:
            raise forms.ValidationError(
                {"end_date": "End date must be after the start date."}
            )
        return cleaned


class ProgramItemForm(forms.ModelForm):
    """
    A single program item (one service line within a program).
    `service` and `assigned_staff` querysets are scoped in the view
    via get_form via ProgramItemFormSet.form's __init__.
    """

    class Meta:
        model = ProgramItem
        fields = [
            "service",
            "assigned_staff",
            "week_number",
            "frequency_per_week",
            "planned_sessions_count",
            "session_duration_minutes",
            "order_index",
            "intensity_override",
            "custom_notes",
        ]
        widgets = {
            "custom_notes": forms.Textarea(attrs={"rows": 2}),
            "intensity_override": forms.Select(
                choices=[("", "—"), ("low", "Low"), ("medium", "Medium"), ("high", "High")]
            ),
        }


def build_program_item_formset(organization, **kwargs):
    """
    Factory that produces an inline ProgramItem formset with org-scoped
    `service` and `assigned_staff` dropdowns.

    Accepts the same **kwargs as inlineformset_factory so the caller
    can pass data=, instance=, queryset= etc.
    """

    OrgProgramItemForm = _make_scoped_item_form(organization)
    FormSet = inlineformset_factory(
        Program,
        ProgramItem,
        form=OrgProgramItemForm,
        extra=1,
        can_delete=True,
        min_num=1,
        validate_min=True,
    )
    return FormSet(**kwargs)


def _make_scoped_item_form(organization):
    """
    Dynamically creates a ProgramItemForm subclass with FK querysets
    restricted to the given organization.  This avoids leaking another
    tenant's services or staff into the dropdown.
    """

    active_services = Service.objects.filter(
        organization=organization,
        is_active=True,
    ).select_related("category").order_by("name")

    available_staff = Admin.objects.filter(
        organization=organization,
        is_available_for_assignment=True,
    ).select_related("user").order_by("user__first_name")

    class ScopedProgramItemForm(ProgramItemForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields["service"].queryset = active_services
            self.fields["assigned_staff"].queryset = available_staff
            self.fields["assigned_staff"].required = False

    return ScopedProgramItemForm


class ProgramNoteForm(forms.ModelForm):
    """Used on the detail/update page to add clinical or operational notes."""

    class Meta:
        model = ProgramNote
        fields = ["note_type", "content", "is_internal"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 3}),
        }


class ProgramUpdateForm(forms.ModelForm):
    """
    Lightweight edit form for header fields only.
    Status transitions are handled explicitly in the view — not via raw form.
    """

    class Meta:
        model = Program
        fields = [
            "name",
            "objective_summary",
            "duration_weeks",
            "start_date",
            "end_date",
            "adherence_target",
            "review_frequency_days",
            "status",
        ]
        widgets = {
            "objective_summary": forms.Textarea(attrs={"rows": 3}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end <= start:
            raise forms.ValidationError(
                {"end_date": "End date must be after the start date."}
            )
        return cleaned
