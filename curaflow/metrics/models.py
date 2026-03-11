from django.conf import settings
from django.db import models

from curaflow.core.models import OrganizationScopedModel, TimeStampedModel


class MetricType(TimeStampedModel):
    class DataType(models.TextChoices):
        INTEGER = "integer", "Integer"
        DECIMAL = "decimal", "Decimal"
        TEXT = "text", "Text"
        BOOLEAN = "boolean", "Boolean"

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="metric_types",
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    unit = models.CharField(max_length=20, blank=True)
    data_type = models.CharField(max_length=20, choices=DataType.choices, default=DataType.DECIMAL)
    category = models.CharField(max_length=100, blank=True)
    higher_is_better = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("organization", "code")
        ordering = ["name"]

    def __str__(self):
        return self.name


class CustomerMetricRecord(TimeStampedModel):
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="metric_records"
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="metric_records",
    )
    metric_type = models.ForeignKey(
        "metrics.MetricType", on_delete=models.CASCADE, related_name="records"
    )
    value_number = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    value_text = models.CharField(max_length=255, blank=True)
    recorded_at = models.DateTimeField()
    source = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_metric_records",
    )

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"{self.customer} - {self.metric_type} - {self.recorded_at}"