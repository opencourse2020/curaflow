from django import forms
from .models import Organization, OrganizationSettings, Location


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            "name",
            "business_type",
            "email",
            "phone",
            "website",
            "timezone",
            "currency",
            "country",
            "city",
            "address",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3, "class": "form-input"}),
            "business_type": forms.Select(attrs={"class": "form-select"}),
        }


class OrganizationSettingsForm(forms.ModelForm):
    class Meta:
        model = OrganizationSettings
        fields = [
            "allow_ai_recommendations",
            "require_human_approval_for_ai_programs",
            "allow_customer_portal",
            "enable_sms_notifications",
            "enable_email_notifications",
            "program_default_duration_weeks",
            "risk_threshold",
            "adherence_alert_threshold",
            "default_language",
        ]


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = [
            "name",
            "email",
            "phone",
            "country",
            "city",
            "address",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 2}),
        }

