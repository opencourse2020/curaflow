from django.shortcuts import render
from django.views.generic import (
    CreateView, UpdateView, DeleteView, DetailView, ListView, TemplateView, View)
# Create your views here.


class profileView(TemplateView):
    template_name = "login.html"