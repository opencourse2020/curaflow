from django.contrib import admin

# Register your models here.
from . import models

model_objects = (models.User,
                 models.Admin,
                 models.Member,
                 models.Organization,
                 models.Location,
                 models.StaffAvailability,
                 models.OrganizationSettings,
                 models.OrganizationMembership,
                 models.AuditLog,

                 )

for m in model_objects:
    admin.site.register(m)
