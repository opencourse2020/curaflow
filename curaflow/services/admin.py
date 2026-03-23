from django.contrib import admin

# Register your models here.
from . import models

model_objects = (models.ServiceCategory,
                 models.Service,
                 models.ServiceEligibilityRule,
                 models.ServiceContraindication,
                 models.ServiceStaffAssignment,
                 models.ServiceResource,

                 )

for m in model_objects:
    admin.site.register(m)