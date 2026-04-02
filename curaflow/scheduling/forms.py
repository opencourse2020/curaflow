from django import forms

from .models import Appointment, ExecutionAlert, SessionExecution


class AppointmentStatusForm(forms.ModelForm):
    """
    Minimal form for updating an Appointment's status and notes.

    Full rescheduling (date/time change) is intentionally out of scope
    for this iteration; only status transitions and note edits are
    surfaced here to keep the view footprint small.
    """

    class Meta:
        model = Appointment
        fields = ["status", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
            "status": forms.Select(),
        }

    def clean_status(self):
        """
        Prevent illegal forward jumps (e.g. marking a cancelled session
        completed).  Soft-guard only — hard enforcement can be added in
        the service layer once business rules are finalised.
        """
        new_status = self.cleaned_data["status"]
        current = self.instance.status if self.instance.pk else None

        illegal = {
            Appointment.Status.CANCELLED: [
                Appointment.Status.COMPLETED,
                Appointment.Status.CONFIRMED,
            ],
        }
        if current and new_status in illegal.get(current, []):
            raise forms.ValidationError(
                f"Cannot move a {current} appointment to {new_status}."
            )
        return new_status


class SessionExecutionForm(forms.ModelForm):
    """
    Records the outcome of an executed session (staff-side entry).
    Linked to a specific Appointment via the OneToOne relation in the view.
    """

    class Meta:
        model = SessionExecution
        fields = [
            "status",
            "duration_minutes",
            "customer_attended",
            "pain_before",
            "pain_after",
            "energy_before",
            "energy_after",
            "session_feedback",
            "staff_notes",
        ]
        widgets = {
            "session_feedback": forms.Textarea(attrs={"rows": 3}),
            "staff_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        attended = cleaned.get("customer_attended")
        status = cleaned.get("status")
        # If the customer didn't attend, only missed/cancelled are valid
        if not attended and status == SessionExecution.Status.COMPLETED:
            raise forms.ValidationError(
                "A session cannot be COMPLETED if the customer did not attend."
            )
        return cleaned


class AlertAcknowledgeForm(forms.ModelForm):
    """
    Minimal form for acknowledging or resolving an ExecutionAlert.
    """

    class Meta:
        model = ExecutionAlert
        fields = ["status"]
        widgets = {"status": forms.Select()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show actionable transitions in the dropdown
        self.fields["status"].choices = [
            (ExecutionAlert.Status.ACKNOWLEDGED, "Acknowledge"),
            (ExecutionAlert.Status.RESOLVED, "Resolve"),
            (ExecutionAlert.Status.DISMISSED, "Dismiss"),
        ]
