from django.contrib import admin

# Register your models here.
from . import models

model_objects = (models.ProgramTemplate,
                 models.ProgramTemplateItem,
                 models.ProgramCase,
                 models.Program,
                 models.ProgramItem,
                 models.ProgramRestriction,
                 models.ProgramNote,
                 models.ProgressReview,
                 models.ProgramAdjustment,

                 )

for m in model_objects:
    admin.site.register(m)