from django.db import models

from curaflow.profiles.models import TimeStampedModel


class SubscriptionPlan(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    yearly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default="USD")
    max_staff = models.PositiveIntegerField(default=5)
    max_customers = models.PositiveIntegerField(default=100)
    max_ai_recommendations_per_month = models.PositiveIntegerField(default=100)
    max_locations = models.PositiveIntegerField(default=1)
    features_json = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class OrganizationSubscription(TimeStampedModel):
    class BillingCycle(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"

    class Status(models.TextChoices):
        TRIALING = "trialing", "Trialing"
        ACTIVE = "active", "Active"
        PAST_DUE = "past_due", "Past Due"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    organization = models.ForeignKey(
        "profiles.Organization", on_delete=models.CASCADE, related_name="subscriptions"
    )
    subscription_plan = models.ForeignKey(
        "billing.SubscriptionPlan", on_delete=models.PROTECT, related_name="subscriptions"
    )
    billing_cycle = models.CharField(
        max_length=20, choices=BillingCycle.choices, default=BillingCycle.MONTHLY
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIALING)
    started_at = models.DateTimeField(null=True, blank=True)
    renewal_date = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    external_subscription_id = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.organization} - {self.subscription_plan}"


class Invoice(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ISSUED = "issued", "Issued"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    organization = models.ForeignKey(
        "profiles.Organization", on_delete=models.CASCADE, related_name="invoices"
    )
    subscription = models.ForeignKey(
        "billing.OrganizationSubscription",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )
    invoice_number = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    due_date = models.DateField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    external_invoice_id = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.invoice_number


class PaymentTransaction(TimeStampedModel):
    organization = models.ForeignKey(
        "profiles.Organization", on_delete=models.CASCADE, related_name="payment_transactions"
    )
    invoice = models.ForeignKey(
        "billing.Invoice", on_delete=models.CASCADE, related_name="transactions"
    )
    provider = models.CharField(max_length=50, blank=True)
    transaction_reference = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    status = models.CharField(max_length=50)
    paid_at = models.DateTimeField(null=True, blank=True)
    raw_response_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.transaction_reference or f"Txn #{self.pk}"


class UsageRecord(TimeStampedModel):
    organization = models.ForeignKey(
        "profiles.Organization", on_delete=models.CASCADE, related_name="usage_records"
    )
    usage_type = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    usage_date = models.DateField()
    metadata_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-usage_date"]

    def __str__(self):
        return f"{self.organization} - {self.usage_type} - {self.usage_date}"