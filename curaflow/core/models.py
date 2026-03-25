from django.db import models
from django.utils.text import slugify

from curaflow.profiles.models import *


class Organization(TimeStampedModel, SoftDeleteModel):
    class BusinessType(models.TextChoices):
        GYM = "gym", "Gym"
        PHYSIO = "physio", "Physiotherapy Clinic"
        SPA = "spa", "Spa"
        WELLNESS_CENTER = "wellness_center", "Wellness Center"
        NUTRITION = "nutrition", "Nutrition Practice"
        REHAB = "rehab", "Rehabilitation Center"
        OTHER = "other", "Other"

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    business_type = models.CharField(max_length=32, choices=BusinessType.choices, default=BusinessType.OTHER)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to=logo_directory_path, null=True, blank=True)
    primary_color = models.CharField(max_length=20, blank=True)
    timezone = models.CharField(max_length=64, default="Africa/Casablanca")
    currency = models.CharField(max_length=10, default="MAD")
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return str(self.name)


class Location(TimeStampedModel, SoftDeleteModel, OrganizationScopedModel):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        unique_together = ("organization", "name")
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} - {self.organization.name}"


class StaffAvailability(TimeStampedModel):
    class Weekday(models.IntegerChoices):
        MONDAY = 1, "Monday"
        TUESDAY = 2, "Tuesday"
        WEDNESDAY = 3, "Wednesday"
        THURSDAY = 4, "Thursday"
        FRIDAY = 5, "Friday"
        SATURDAY = 6, "Saturday"
        SUNDAY = 7, "Sunday"

    admin = models.ForeignKey(
        Admin, on_delete=models.CASCADE, related_name="availabilities", null=True
    )
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_availabilities",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["admin", "weekday", "start_time"]

    def __str__(self):
        return f"{self.admin} - {self.get_weekday_display()}"


class OrganizationSettings(TimeStampedModel):
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name="settings",
    )
    allow_ai_recommendations = models.BooleanField(default=True)
    require_human_approval_for_ai_programs = models.BooleanField(default=True)
    allow_customer_portal = models.BooleanField(default=True)
    enable_sms_notifications = models.BooleanField(default=False)
    enable_email_notifications = models.BooleanField(default=True)
    program_default_duration_weeks = models.PositiveIntegerField(default=8)
    risk_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=70.00)
    adherence_alert_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=70.00)
    default_language = models.CharField(max_length=20, default="en")

    def __str__(self) -> str:
        return f"Settings - {self.organization.name}"


class OrganizationMembership(TimeStampedModel):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MANAGER = "manager", "Manager"
        PRACTITIONER = "practitioner", "Practitioner"
        COACH = "coach", "Coach"
        NUTRITIONIST = "nutritionist", "Nutritionist"
        RECEPTIONIST = "receptionist", "Receptionist"
        ANALYST = "analyst", "Analyst"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="memberships"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.MANAGER)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "organization")

    def __str__(self):
        return f"{self.user.email} @ {self.organization.name}"


class AuditLog(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor_type = models.CharField(max_length=50, blank=True)
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.action} - {self.model_name} ({self.object_id})"