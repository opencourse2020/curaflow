from django.shortcuts import render
from django.views.generic import (
    CreateView, UpdateView, DeleteView, DetailView, ListView, TemplateView, View)

# Create your views here.


class ServicesView(TemplateView):
    template_name = "services.html"