from django.conf import settings
from django.db import models

from curaflow.core.models import OrganizationScopedModel, SoftDeleteModel, TimeStampedModel


class Customer(TimeStampedModel, SoftDeleteModel, OrganizationScopedModel):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"
        PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        PROSPECT = "prospect", "Prospect"
        ARCHIVED = "archived", "Archived"

    external_customer_id = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=30, choices=Gender.choices, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)

    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=50, blank=True)

    preferred_language = models.CharField(max_length=20, default="en")
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    source = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    consent_given = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["first_name", "last_name"]
        unique_together = ("organization", "external_customer_id")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class CustomerProfile(TimeStampedModel):
    class ActivityLevel(models.TextChoices):
        SEDENTARY = "sedentary", "Sedentary"
        LIGHT = "light", "Light"
        MODERATE = "moderate", "Moderate"
        ACTIVE = "active", "Active"

    class RiskLevel(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    customer = models.OneToOneField(
        "customers.Customer", on_delete=models.CASCADE, related_name="profile"
    )
    height_cm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    bmi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    activity_level = models.CharField(
        max_length=20, choices=ActivityLevel.choices, blank=True
    )
    sleep_quality_score = models.PositiveSmallIntegerField(null=True, blank=True)
    stress_level = models.PositiveSmallIntegerField(null=True, blank=True)
    dietary_preference = models.CharField(max_length=100, blank=True)
    smoking_status = models.CharField(max_length=50, blank=True)
    alcohol_use = models.CharField(max_length=50, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    lifestyle_notes = models.TextField(blank=True)
    goals_summary = models.TextField(blank=True)
    risk_level = models.CharField(
        max_length=20, choices=RiskLevel.choices, default=RiskLevel.LOW
    )

    def __str__(self):
        return f"Profile - {self.customer}"


class MedicalCondition(TimeStampedModel):
    class Category(models.TextChoices):
        MUSCULOSKELETAL = "musculoskeletal", "Musculoskeletal"
        CARDIOVASCULAR = "cardiovascular", "Cardiovascular"
        METABOLIC = "metabolic", "Metabolic"
        NEUROLOGICAL = "neurological", "Neurological"
        RESPIRATORY = "respiratory", "Respiratory"
        OTHER = "other", "Other"

    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, blank=True)
    category = models.CharField(max_length=50, choices=Category.choices, default=Category.OTHER)
    description = models.TextField(blank=True)
    is_high_risk = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class CustomerMedicalCondition(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        HISTORICAL = "historical", "Historical"
        CONTROLLED = "controlled", "Controlled"

    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="medical_conditions"
    )
    medical_condition = models.ForeignKey(
        "customers.MedicalCondition", on_delete=models.CASCADE, related_name="customer_links"
    )
    severity = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    diagnosed_at = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    requires_program_restriction = models.BooleanField(default=False)

    class Meta:
        unique_together = ("customer", "medical_condition")

    def __str__(self):
        return f"{self.customer} - {self.medical_condition}"


class Injury(TimeStampedModel):
    name = models.CharField(max_length=255)
    body_area = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ("name", "body_area")

    def __str__(self):
        return self.name


class CustomerInjury(TimeStampedModel):
    class Side(models.TextChoices):
        LEFT = "left", "Left"
        RIGHT = "right", "Right"
        BILATERAL = "bilateral", "Bilateral"
        NONE = "none", "None"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RECOVERING = "recovering", "Recovering"
        RESOLVED = "resolved", "Resolved"

    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="injuries"
    )
    injury = models.ForeignKey(
        "customers.Injury", on_delete=models.CASCADE, related_name="customer_links"
    )
    side = models.CharField(max_length=20, choices=Side.choices, default=Side.NONE)
    severity = models.CharField(max_length=50, blank=True)
    onset_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    pain_level = models.PositiveSmallIntegerField(null=True, blank=True)
    mobility_impact = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.customer} - {self.injury}"


class Allergy(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class CustomerAllergy(TimeStampedModel):
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="allergies"
    )
    allergy = models.ForeignKey(
        "customers.Allergy", on_delete=models.CASCADE, related_name="customer_links"
    )
    severity = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("customer", "allergy")

    def __str__(self):
        return f"{self.customer} - {self.allergy}"


class Medication(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class CustomerMedication(TimeStampedModel):
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="medications"
    )
    medication = models.ForeignKey(
        "customers.Medication", on_delete=models.CASCADE, related_name="customer_links"
    )
    dosage = models.CharField(max_length=100, blank=True)
    frequency = models.CharField(max_length=100, blank=True)
    purpose = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.customer} - {self.medication}"


class Goal(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class CustomerGoal(TimeStampedModel):
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="goals"
    )
    goal = models.ForeignKey(
        "customers.Goal", on_delete=models.CASCADE, related_name="customer_links"
    )
    priority = models.PositiveSmallIntegerField(default=1)
    target_value = models.CharField(max_length=100, blank=True)
    target_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("customer", "goal")

    def __str__(self):
        return f"{self.customer} - {self.goal}"


class CustomerAssessment(TimeStampedModel):
    class AssessmentType(models.TextChoices):
        INTAKE = "intake", "Intake"
        REASSESSMENT = "reassessment", "Reassessment"
        MONTHLY_REVIEW = "monthly_review", "Monthly Review"
        DISCHARGE = "discharge", "Discharge"

    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="assessments"
    )
    assessed_by = models.ForeignKey(
        "profiles.StaffProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_assessments",
    )
    assessment_type = models.CharField(
        max_length=30, choices=AssessmentType.choices, default=AssessmentType.INTAKE
    )
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    body_fat_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pain_level = models.PositiveSmallIntegerField(null=True, blank=True)
    mobility_score = models.PositiveSmallIntegerField(null=True, blank=True)
    fitness_score = models.PositiveSmallIntegerField(null=True, blank=True)
    stress_score = models.PositiveSmallIntegerField(null=True, blank=True)
    sleep_score = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    raw_questionnaire_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.get_assessment_type_display()} - {self.customer}"


class CustomerFeedback(TimeStampedModel):
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="feedbacks"
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedbacks",
    )
    session_execution = models.ForeignKey(
        "scheduling.SessionExecution",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedbacks",
    )
    satisfaction_score = models.PositiveSmallIntegerField(null=True, blank=True)
    ease_of_following_score = models.PositiveSmallIntegerField(null=True, blank=True)
    perceived_benefit_score = models.PositiveSmallIntegerField(null=True, blank=True)
    pain_change_score = models.SmallIntegerField(null=True, blank=True)
    comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback - {self.customer}"