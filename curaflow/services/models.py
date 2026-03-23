from django.db import models

from curaflow.profiles.models import OrganizationScopedModel, SoftDeleteModel, TimeStampedModel, Location, Admin


class ServiceCategory(TimeStampedModel, SoftDeleteModel, OrganizationScopedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ("organization", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Service(TimeStampedModel, SoftDeleteModel, OrganizationScopedModel):
    class IntensityLevel(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    class DeliveryMode(models.TextChoices):
        IN_PERSON = "in_person", "In Person"
        VIRTUAL = "virtual", "Virtual"
        HYBRID = "hybrid", "Hybrid"

    category = models.ForeignKey(
        "services.ServiceCategory",
        on_delete=models.SET_NULL,
        null=True,
        related_name="services",
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=255, blank=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    default_frequency_per_week = models.PositiveSmallIntegerField(default=1)
    intensity_level = models.CharField(
        max_length=10, choices=IntensityLevel.choices, default=IntensityLevel.LOW
    )
    delivery_mode = models.CharField(
        max_length=20, choices=DeliveryMode.choices, default=DeliveryMode.IN_PERSON
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="services",
    )
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default="USD")
    requires_staff_assignment = models.BooleanField(default=True)
    requires_medical_clearance = models.BooleanField(default=False)

    class Meta:
        unique_together = ("organization", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name


class ServiceEligibilityRule(TimeStampedModel):
    class RuleType(models.TextChoices):
        AGE_MIN = "age_min", "Minimum Age"
        AGE_MAX = "age_max", "Maximum Age"
        BMI_RANGE = "bmi_range", "BMI Range"
        GENDER_LIMIT = "gender_limit", "Gender Limit"
        CONDITION_REQUIRED = "condition_required", "Condition Required"
        CONDITION_EXCLUDED = "condition_excluded", "Condition Excluded"
        INJURY_EXCLUDED = "injury_excluded", "Injury Excluded"
        RISK_LIMIT = "risk_limit", "Risk Limit"

    service = models.ForeignKey(
        "services.Service", on_delete=models.CASCADE, related_name="eligibility_rules"
    )
    rule_name = models.CharField(max_length=255)
    rule_type = models.CharField(max_length=50, choices=RuleType.choices)
    operator = models.CharField(max_length=20, blank=True)
    value = models.CharField(max_length=255)
    is_hard_rule = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.service} - {self.rule_name}"


class ServiceContraindication(TimeStampedModel):
    service = models.ForeignKey(
        "services.Service", on_delete=models.CASCADE, related_name="contraindications"
    )
    medical_condition = models.ForeignKey(
        "customers.MedicalCondition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="service_contraindications",
    )
    injury = models.ForeignKey(
        "customers.Injury",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="service_contraindications",
    )
    contraindication_text = models.TextField()
    severity = models.CharField(max_length=50, blank=True)
    requires_manual_review = models.BooleanField(default=False)

    def __str__(self):
        return f"Contraindication - {self.service}"


class ServiceStaffAssignment(TimeStampedModel):
    service = models.ForeignKey(
        "services.Service", on_delete=models.CASCADE, related_name="staff_assignments"
    )
    staff = models.ForeignKey(
        Admin,
        on_delete=models.CASCADE,
        related_name="service_assignments",
    )
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ("service", "staff")

    def __str__(self):
        return f"{self.service} - {self.staff}"


class ServiceResource(TimeStampedModel):
    class ResourceType(models.TextChoices):
        ROOM = "room", "Room"
        MACHINE = "machine", "Machine"
        EQUIPMENT = "equipment", "Equipment"

    service = models.ForeignKey(
        "services.Service", on_delete=models.CASCADE, related_name="resources"
    )
    name = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices)
    quantity_required = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.service})"