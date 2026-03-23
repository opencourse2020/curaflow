from django.contrib import admin

# Register your models here.
from . import models


model_objects = (models.RecommendationRun,
                 models.RecommendationOption,
                 models.RecommendationDecision,
                 models.RecommendationOptionItem,
                 models.RecommendationInputSnapshot,
                 models.AgentExecutionLog,
                 models.EvidenceSource,
                 models.PromptLog
                 )


for m in model_objects:
    admin.site.register(m)