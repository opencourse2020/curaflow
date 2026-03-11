from django.conf import settings
from django.db import models

from curaflow.core.models import OrganizationScopedModel, TimeStampedModel


class Appointment(TimeStampedModel, OrganizationScopedModel):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        MISSED = "missed", "Missed"
        CANCELLED = "cancelled", "Cancelled"
        RESCHEDULED = "rescheduled", "Rescheduled"

    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="appointments"
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
    )
    program_item = models.ForeignKey(
        "programs.ProgramItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
    )
    service = models.ForeignKey(
        "services.Service", on_delete=models.CASCADE, related_name="appointments"
    )
    staff = models.ForeignKey(
        "profiles.StaffProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
    )
    location = models.ForeignKey(
        "core.Location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
    )
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["scheduled_start"]

    def __str__(self):
        return f"{self.customer} - {self.service} - {self.scheduled_start}"


class AppointmentRescheduleHistory(TimeStampedModel):
    appointment = models.ForeignKey(
        "scheduling.Appointment", on_delete=models.CASCADE, related_name="reschedule_history"
    )
    old_start = models.DateTimeField()
    old_end = models.DateTimeField()
    new_start = models.DateTimeField()
    new_end = models.DateTimeField()
    reason = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointment_reschedules",
    )

    def __str__(self):
        return f"Reschedule - Appointment #{self.appointment_id}"


class SessionExecution(TimeStampedModel):
    class Status(models.TextChoices):
        COMPLETED = "completed", "Completed"
        PARTIAL = "partial", "Partial"
        MISSED = "missed", "Missed"
        CANCELLED = "cancelled", "Cancelled"

    appointment = models.OneToOneField(
        "scheduling.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="execution",
    )
    program = models.ForeignKey(
        "programs.Program", on_delete=models.CASCADE, related_name="session_executions"
    )
    program_item = models.ForeignKey(
        "programs.ProgramItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="session_executions",
    )
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="session_executions"
    )
    service = models.ForeignKey(
        "services.Service", on_delete=models.CASCADE, related_name="session_executions"
    )
    staff = models.ForeignKey(
        "profiles.StaffProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="session_executions",
    )
    execution_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices)
    duration_minutes = models.PositiveIntegerField(default=0)
    customer_attended = models.BooleanField(default=False)
    pain_before = models.PositiveSmallIntegerField(null=True, blank=True)
    pain_after = models.PositiveSmallIntegerField(null=True, blank=True)
    energy_before = models.PositiveSmallIntegerField(null=True, blank=True)
    energy_after = models.PositiveSmallIntegerField(null=True, blank=True)
    session_feedback = models.TextField(blank=True)
    staff_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.customer} - {self.execution_date}"


class AdherenceSnapshot(TimeStampedModel):
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="adherence_snapshots"
    )
    program = models.ForeignKey(
        "programs.Program", on_delete=models.CASCADE, related_name="adherence_snapshots"
    )
    snapshot_date = models.DateField()
    planned_sessions = models.PositiveIntegerField(default=0)
    completed_sessions = models.PositiveIntegerField(default=0)
    missed_sessions = models.PositiveIntegerField(default=0)
    cancelled_sessions = models.PositiveIntegerField(default=0)
    adherence_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    engagement_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dropout_risk_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("customer", "program", "snapshot_date")
        ordering = ["-snapshot_date"]

    def __str__(self):
        return f"Adherence - {self.customer} - {self.snapshot_date}"


class ExecutionAlert(TimeStampedModel, OrganizationScopedModel):
    class AlertType(models.TextChoices):
        MISSED_SESSION = "missed_session", "Missed Session"
        LOW_ADHERENCE = "low_adherence", "Low Adherence"
        SYMPTOM_WORSENING = "symptom_worsening", "Symptom Worsening"
        REVIEW_DUE = "review_due", "Review Due"
        NO_PROGRESS = "no_progress", "No Progress"
        RISK_FLAG = "risk_flag", "Risk Flag"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="execution_alerts"
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts",
    )
    appointment = models.ForeignKey(
        "scheduling.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts",
    )
    alert_type = models.CharField(max_length=30, choices=AlertType.choices)
    severity = models.CharField(max_length=50, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    assigned_to = models.ForeignKey(
        "profiles.StaffProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_alerts",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title