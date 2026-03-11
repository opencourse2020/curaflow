from django.shortcuts import render
from django.views.generic import (
    CreateView, UpdateView, DeleteView, DetailView, ListView, TemplateView, View)

# Create your views here.


class DashboardView(TemplateView):
    template_name = "dashboard.html"


class RecommendationView(TemplateView):
    template_name = "recommendation.html"


class AnalyticsView(TemplateView):
    template_name = "analytics.html"


class TrackingView(TemplateView):
    template_name = "tracking.html"


class SettingsView(TemplateView):
    template_name = "settings.html"