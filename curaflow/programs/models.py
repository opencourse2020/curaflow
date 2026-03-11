from django.db import models

from curaflow.core.models import OrganizationScopedModel, SoftDeleteModel, TimeStampedModel


class ProgramTemplate(TimeStampedModel, SoftDeleteModel, OrganizationScopedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_goal_category = models.CharField(max_length=100, blank=True)
    target_customer_type = models.CharField(max_length=100, blank=True)
    default_duration_weeks = models.PositiveIntegerField(default=8)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(
        "profiles.StaffProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_program_templates",
    )

    class Meta:
        unique_together = ("organization", "name")

    def __str__(self):
        return self.name


class ProgramTemplateItem(TimeStampedModel):
    program_template = models.ForeignKey(
        "programs.ProgramTemplate", on_delete=models.CASCADE, related_name="items"
    )
    service = models.ForeignKey(
        "services.Service", on_delete=models.CASCADE, related_name="template_items"
    )
    week_number = models.PositiveIntegerField(default=1)
    day_of_week = models.PositiveSmallIntegerField(null=True, blank=True)
    frequency_per_week = models.PositiveSmallIntegerField(default=1)
    session_duration_minutes = models.PositiveIntegerField(default=60)
    order_index = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    is_optional = models.BooleanField(default=False)

    class Meta:
        ordering = ["week_number", "order_index"]

    def __str__(self):
        return f"{self.program_template} - {self.service}"


class ProgramCase(TimeStampedModel, OrganizationScopedModel):
    class CaseStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        UNDER_REVIEW = "under_review", "Under Review"
        APPROVED = "approved", "Approved"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        AI_ASSISTED = "ai_assisted", "AI Assisted"
        CLONED = "cloned", "Cloned"
        IMPORTED = "imported", "Imported"

    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="program_cases"
    )
    created_by = models.ForeignKey(
        "profiles.StaffProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="program_cases",
    )
    case_status = models.CharField(
        max_length=20, choices=CaseStatus.choices, default=CaseStatus.DRAFT
    )
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    intake_assessment = models.ForeignKey(
        "customers.CustomerAssessment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="program_cases",
    )
    target_start_date = models.DateField(null=True, blank=True)
    target_end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Case #{self.pk} - {self.customer}"


class Program(TimeStampedModel, SoftDeleteModel, OrganizationScopedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="programs"
    )
    program_case = models.ForeignKey(
        "programs.ProgramCase",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="programs",
    )
    template_used = models.ForeignKey(
        "programs.ProgramTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_programs",
    )
    name = models.CharField(max_length=255)
    objective_summary = models.TextField(blank=True)
    duration_weeks = models.PositiveIntegerField(default=8)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    adherence_target = models.DecimalField(max_digits=5, decimal_places=2, default=80.00)
    review_frequency_days = models.PositiveIntegerField(default=7)
    approved_by = models.ForeignKey(
        "profiles.StaffProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_programs",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ProgramItem(TimeStampedModel):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        REMOVED = "removed", "Removed"
        COMPLETED = "completed", "Completed"

    program = models.ForeignKey(
        "programs.Program", on_delete=models.CASCADE, related_name="items"
    )
    service = models.ForeignKey(
        "services.Service", on_delete=models.CASCADE, related_name="program_items"
    )
    assigned_staff = models.ForeignKey(
        "profiles.StaffProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="program_items",
    )
    week_number = models.PositiveIntegerField(default=1)
    frequency_per_week = models.PositiveSmallIntegerField(default=1)
    planned_sessions_count = models.PositiveIntegerField(default=1)
    session_duration_minutes = models.PositiveIntegerField(default=60)
    order_index = models.PositiveIntegerField(default=0)
    intensity_override = models.CharField(max_length=20, blank=True)
    custom_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)

    class Meta:
        ordering = ["week_number", "order_index"]

    def __str__(self):
        return f"{self.program} - {self.service}"


class ProgramRestriction(TimeStampedModel):
    class RestrictionType(models.TextChoices):
        MEDICAL = "medical", "Medical"
        INJURY = "injury", "Injury"
        AGE = "age", "Age"
        FATIGUE = "fatigue", "Fatigue"
        BUDGET = "budget", "Budget"
        STAFFING = "staffing", "Staffing"

    program = models.ForeignKey(
        "programs.Program", on_delete=models.CASCADE, related_name="restrictions"
    )
    restriction_type = models.CharField(max_length=20, choices=RestrictionType.choices)
    severity = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    recommended_action = models.TextField(blank=True)

    def __str__(self):
        return f"{self.program} - {self.restriction_type}"


class ProgramNote(TimeStampedModel):
    class NoteType(models.TextChoices):
        CLINICAL = "clinical", "Clinical"
        COACHING = "coaching", "Coaching"
        OPERATIONAL = "operational", "Operational"
        AI_COMMENT = "ai_comment", "AI Comment"

    program = models.ForeignKey(
        "programs.Program", on_delete=models.CASCADE, related_name="notes"
    )
    author = models.ForeignKey(
        "profiles.StaffProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="program_notes",
    )
    note_type = models.CharField(max_length=20, choices=NoteType.choices, default=NoteType.OPERATIONAL)
    content = models.TextField()
    is_internal = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.note_type} - {self.program}"


class ProgressReview(TimeStampedModel):
    class Recommendation(models.TextChoices):
        CONTINUE = "continue", "Continue"
        INTENSIFY = "intensify", "Intensify"
        REDUCE = "reduce", "Reduce"
        REDESIGN = "redesign", "Redesign"
        PAUSE = "pause", "Pause"
        DISCHARGE = "discharge", "Discharge"

    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="progress_reviews"
    )
    program = models.ForeignKey(
        "programs.Program", on_delete=models.CASCADE, related_name="progress_reviews"
    )
    reviewer = models.ForeignKey(
        "profiles.StaffProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="progress_reviews",
    )
    review_date = models.DateField()
    adherence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    progress_summary = models.TextField(blank=True)
    issue_summary = models.TextField(blank=True)
    recommendation = models.CharField(
        max_length=20, choices=Recommendation.choices, default=Recommendation.CONTINUE
    )
    next_review_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Review - {self.customer} - {self.review_date}"


class ProgramAdjustment(TimeStampedModel):
    class AdjustmentType(models.TextChoices):
        FREQUENCY_CHANGE = "frequency_change", "Frequency Change"
        SERVICE_ADDITION = "service_addition", "Service Addition"
        SERVICE_REMOVAL = "service_removal", "Service Removal"
        DURATION_CHANGE = "duration_change", "Duration Change"
        STAFF_CHANGE = "staff_change", "Staff Change"
        FULL_REDESIGN = "full_redesign", "Full Redesign"

    program = models.ForeignKey(
        "programs.Program", on_delete=models.CASCADE, related_name="adjustments"
    )
    progress_review = models.ForeignKey(
        "programs.ProgressReview",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="adjustments",
    )
    adjusted_by = models.ForeignKey(
        "profiles.StaffProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="program_adjustments",
    )
    adjustment_type = models.CharField(max_length=30, choices=AdjustmentType.choices)
    description = models.TextField()
    old_value_json = models.JSONField(default=dict, blank=True)
    new_value_json = models.JSONField(default=dict, blank=True)
    effective_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.program} - {self.adjustment_type}"
