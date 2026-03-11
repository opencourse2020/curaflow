from django.shortcuts import render
from django.views.generic import (
    CreateView, UpdateView, DeleteView, DetailView, ListView, TemplateView, View)

# Create your views here.


class CustomersView(TemplateView):
    template_name = "customers.html"


class CustomerProfileView(TemplateView):
    template_name = "customer_profile.html"