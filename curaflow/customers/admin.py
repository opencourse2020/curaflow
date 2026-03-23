from django.contrib import admin

# Register your models here.
from . import models


model_objects = (models.Customer,
                 models.CustomerProfile,
                 models.MedicalCondition,
                 models.CustomerMedicalCondition,
                 models.Injury,
                 models.CustomerInjury,
                 models.Allergy,
                 models.CustomerAllergy,
                 models.Medication,
                 models.CustomerMedication,
                 models.Goal,
                 models.CustomerGoal,
                 models.CustomerAssessment,
                 models.Notification,

                 )


for m in model_objects:
    admin.site.register(m)
