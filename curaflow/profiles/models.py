from django.contrib.auth.models import AbstractUser
from django.db import models

from curaflow.core.models import TimeStampedModel


class User(AbstractUser, TimeStampedModel):
    username = None
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class StaffProfile(TimeStampedModel):
    user = models.OneToOneField(
        "profiles.User", on_delete=models.CASCADE, related_name="staff_profile"
    )
    organization = models.ForeignKey(
        "core.Organization", on_delete=models.CASCADE, related_name="staff_profiles"
    )
    location = models.ForeignKey(
        "core.Location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_profiles",
    )
    title = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    license_number = models.CharField(max_length=100, blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    avatar = models.ImageField(upload_to="staff_avatars/", null=True, blank=True)

    can_approve_programs = models.BooleanField(default=False)
    can_edit_services = models.BooleanField(default=False)
    can_manage_customers = models.BooleanField(default=False)
    can_view_analytics = models.BooleanField(default=False)
    is_available_for_assignment = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email}"


class StaffAvailability(TimeStampedModel):
    class Weekday(models.IntegerChoices):
        MONDAY = 1, "Monday"
        TUESDAY = 2, "Tuesday"
        WEDNESDAY = 3, "Wednesday"
        THURSDAY = 4, "Thursday"
        FRIDAY = 5, "Friday"
        SATURDAY = 6, "Saturday"
        SUNDAY = 7, "Sunday"

    staff = models.ForeignKey(
        "profiles.StaffProfile", on_delete=models.CASCADE, related_name="availabilities"
    )
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.ForeignKey(
        "core.Location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_availabilities",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["staff", "weekday", "start_time"]

    def __str__(self):
        return f"{self.staff} - {self.get_weekday_display()}"