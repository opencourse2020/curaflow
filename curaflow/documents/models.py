from django.conf import settings
from django.db import models

from curaflow.core.models import OrganizationScopedModel, TimeStampedModel


class Document(TimeStampedModel, OrganizationScopedModel):
    class DocumentType(models.TextChoices):
        CONSENT = "consent", "Consent"
        MEDICAL_REPORT = "medical_report", "Medical Report"
        ASSESSMENT = "assessment", "Assessment"
        IMAGE = "image", "Image"
        INVOICE = "invoice", "Invoice"
        ATTACHMENT = "attachment", "Attachment"

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_documents",
    )
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/")
    mime_type = models.CharField(max_length=100, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)
    description = models.TextField(blank=True)
    is_sensitive = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class IntakeFormTemplate(TimeStampedModel, OrganizationScopedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    schema_json = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("organization", "name")

    def __str__(self):
        return self.name


class IntakeFormSubmission(TimeStampedModel):
    template = models.ForeignKey(
        "documents.IntakeFormTemplate",
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="intake_submissions"
    )
    submitted_by_customer = models.BooleanField(default=True)
    answers_json = models.JSONField(default=dict)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        "profiles.StaffProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_intake_submissions",
    )
    review_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.template} - {self.customer}"