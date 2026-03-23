from django.contrib import admin

# Register your models here.
from . import models


model_objects = (models.SubscriptionPlan,
                 models.OrganizationSubscription,
                 models.Invoice,
                 models.PaymentTransaction,
                 models.UsageRecord
                 )


for m in model_objects:
    admin.site.register(m)