from django.urls import path, include
from . import views

app_name = "customers"


urlpatterns = [
    path("", views.CustomersView.as_view(), name="list"),
    path("profile/", views.CustomerProfileView.as_view(), name="customer_profile"),
    ]