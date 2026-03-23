from django.contrib import admin

# Register your models here.
from . import models

model_objects = (models.Appointment,
                 models.AppointmentRescheduleHistory,
                 models.SessionExecution,
                 models.AdherenceSnapshot,
                 models.ExecutionAlert,
                 models.CustomerFeedback,

                 )

for m in model_objects:
    admin.site.register(m)