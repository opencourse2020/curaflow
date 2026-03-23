from django.contrib import admin

# Register your models here.
from . import models

model_objects = (models.Document,
                 models.IntakeFormTemplate,
                 models.IntakeFormSubmission,


                 )

for m in model_objects:
    admin.site.register(m)
