from django.shortcuts import render
from django.views.generic import (
    CreateView, UpdateView, DeleteView, DetailView, ListView, TemplateView, View)

# Create your views here.


class DashboardView(TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        raw_data = "72,Wk1|76,Wk2|81,Wk3|79,Wk4|74,Wk5|82,Wk6|85,Wk7|78,Wk8"
        # Create a list of tuples: [('72', 'Wk1'), ('76', 'Wk2'), ...]
        weeks = [item.split(',') for item in raw_data.split('|')]

        kwargs["weeks"] = weeks

        return super(DashboardView, self).get_context_data(**kwargs)


class RecommendationView(TemplateView):
    template_name = "recommendation.html"


class AnalyticsView(TemplateView):
    template_name = "analytics.html"


class TrackingView(TemplateView):
    template_name = "tracking.html"


class SettingsView(TemplateView):
    template_name = "settings.html"