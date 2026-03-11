from django.urls import path, include
from . import views

app_name = "programs"


urlpatterns = [
    path("", views.ProgramsView.as_view(), name="program_builder"),
    ]