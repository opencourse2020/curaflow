from django import forms

from .models import Customer, CustomerProfile


class CustomerForm(forms.ModelForm):
    """
    Used for both CustomerCreateView and CustomerUpdateView.

    The `organization` field is intentionally excluded — it is injected in
    the view's form_valid() to enforce multi-tenant scoping and prevent
    mass-assignment of arbitrary organizations.
    """

    class Meta:
        model = Customer
        fields = [
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "email",
            "phone",
            "emergency_contact_name",
            "emergency_contact_phone",
            "preferred_language",
            "address",
            "city",
            "country",
            "source",
            "status",
            "consent_given",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 3}),
            "gender": forms.Select(),
            "status": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mark required fields explicitly for front-end labelling
        for field_name in ("first_name", "last_name"):
            self.fields[field_name].required = True


class CustomerProfileForm(forms.ModelForm):
    """
    Separate form for the CustomerProfile one-to-one record.
    Rendered alongside CustomerForm when editing a customer's details.
    """

    class Meta:
        model = CustomerProfile
        fields = [
            "height_cm",
            "weight_kg",
            "activity_level",
            "sleep_quality_score",
            "stress_level",
            "dietary_preference",
            "smoking_status",
            "alcohol_use",
            "occupation",
            "lifestyle_notes",
            "goals_summary",
            "risk_level",
        ]
        widgets = {
            "lifestyle_notes": forms.Textarea(attrs={"rows": 3}),
            "goals_summary": forms.Textarea(attrs={"rows": 3}),
            "activity_level": forms.Select(),
            "risk_level": forms.Select(),
        }


class CustomerSearchForm(forms.Form):
    """
    Stateless search/filter form used in CustomerListView.
    No CSRF required — all GET parameters.
    """

    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={"placeholder": "Name, email or phone…"}),
    )
    status = forms.ChoiceField(
        required=False,
        label="Status",
        choices=[("", "All statuses")] + Customer.Status.choices,
    )
