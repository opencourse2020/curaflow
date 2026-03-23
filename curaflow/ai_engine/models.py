from django.conf import settings
from django.db import models

from curaflow.profiles.models import OrganizationScopedModel, TimeStampedModel


class RecommendationRun(TimeStampedModel, OrganizationScopedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        NEEDS_REVIEW = "needs_review", "Needs Review"

    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="recommendation_runs"
    )
    program_case = models.ForeignKey(
        "programs.ProgramCase", on_delete=models.CASCADE, related_name="recommendation_runs"
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_recommendation_runs",
    )
    model_name = models.CharField(max_length=100, blank=True)
    workflow_version = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"RecommendationRun #{self.pk}"


class RecommendationInputSnapshot(TimeStampedModel):
    recommendation_run = models.OneToOneField(
        "ai_engine.RecommendationRun", on_delete=models.CASCADE, related_name="input_snapshot"
    )
    customer_profile_json = models.JSONField(default=dict, blank=True)
    goals_json = models.JSONField(default=list, blank=True)
    conditions_json = models.JSONField(default=list, blank=True)
    injuries_json = models.JSONField(default=list, blank=True)
    services_catalog_json = models.JSONField(default=list, blank=True)
    constraints_json = models.JSONField(default=dict, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Snapshot - Run #{self.recommendation_run_id}"


class RecommendationOption(TimeStampedModel):
    recommendation_run = models.ForeignKey(
        "ai_engine.RecommendationRun", on_delete=models.CASCADE, related_name="options"
    )
    rank = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    duration_weeks = models.PositiveIntegerField(default=8)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    safety_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    adherence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    effectiveness_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    recommendation_json = models.JSONField(default=dict, blank=True)
    rationale_text = models.TextField(blank=True)

    class Meta:
        ordering = ["rank"]

    def __str__(self):
        return f"Option {self.rank} - {self.title}"


class RecommendationOptionItem(TimeStampedModel):
    recommendation_option = models.ForeignKey(
        "ai_engine.RecommendationOption", on_delete=models.CASCADE, related_name="items"
    )
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendation_option_items",
    )
    service_name_snapshot = models.CharField(max_length=255)
    frequency_per_week = models.PositiveSmallIntegerField(default=1)
    duration_minutes = models.PositiveIntegerField(default=60)
    week_start = models.PositiveIntegerField(default=1)
    week_end = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)
    order_index = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order_index"]

    def __str__(self):
        return self.service_name_snapshot


class EvidenceSource(TimeStampedModel):
    class SourceType(models.TextChoices):
        WEB = "web", "Web"
        INTERNAL_DOC = "internal_doc", "Internal Document"
        MANUAL_GUIDELINE = "manual_guideline", "Manual Guideline"
        POLICY = "policy", "Policy"

    recommendation_run = models.ForeignKey(
        "ai_engine.RecommendationRun", on_delete=models.CASCADE, related_name="evidence_sources"
    )
    source_type = models.CharField(max_length=30, choices=SourceType.choices)
    title = models.CharField(max_length=255)
    url = models.URLField(blank=True)
    domain = models.CharField(max_length=255, blank=True)
    citation_text = models.TextField(blank=True)
    trust_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    retrieved_at = models.DateTimeField(null=True, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.title


class RecommendationDecision(TimeStampedModel):
    class Decision(models.TextChoices):
        APPROVED = "approved", "Approved"
        EDITED = "edited", "Edited"
        REJECTED = "rejected", "Rejected"
        NEEDS_MANUAL_DESIGN = "needs_manual_design", "Needs Manual Design"

    recommendation_run = models.OneToOneField(
        "ai_engine.RecommendationRun", on_delete=models.CASCADE, related_name="decision"
    )
    selected_option = models.ForeignKey(
        "ai_engine.RecommendationOption",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decisions",
    )
    decision = models.CharField(max_length=30, choices=Decision.choices)
    reviewed_by = models.ForeignKey(
        "profiles.Admin",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendation_decisions",
    )
    review_notes = models.TextField(blank=True)
    final_program = models.ForeignKey(
        "programs.Program",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendation_decisions",
    )

    def __str__(self):
        return f"Decision - Run #{self.recommendation_run_id}"


class AgentExecutionLog(TimeStampedModel):
    recommendation_run = models.ForeignKey(
        "ai_engine.RecommendationRun", on_delete=models.CASCADE, related_name="execution_logs"
    )
    node_name = models.CharField(max_length=100)
    step_order = models.PositiveIntegerField(default=0)
    input_payload = models.JSONField(default=dict, blank=True)
    output_payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=50)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["step_order", "created_at"]

    def __str__(self):
        return f"{self.node_name} - Run #{self.recommendation_run_id}"


class PromptLog(TimeStampedModel):
    recommendation_run = models.ForeignKey(
        "ai_engine.RecommendationRun", on_delete=models.CASCADE, related_name="prompt_logs"
    )
    prompt_type = models.CharField(max_length=100)
    prompt_text = models.TextField()
    model_name = models.CharField(max_length=100, blank=True)
    response_text = models.TextField(blank=True)
    token_usage_input = models.PositiveIntegerField(default=0)
    token_usage_output = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.prompt_type} - Run #{self.recommendation_run_id}"