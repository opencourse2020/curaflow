from django.shortcuts import render
from django.views.generic import (
    CreateView, UpdateView, DeleteView, DetailView, ListView, TemplateView, View)

# Create your views here.


class ProgramsView(TemplateView):
    template_name = "program_builder.html"