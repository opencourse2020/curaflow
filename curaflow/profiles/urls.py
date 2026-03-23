from django.urls import path, include
from . import views

app_name = "profiles"


urlpatterns = [
    path("", views.ProfileDetailView.as_view(), name="profile"),
    path("userinfo/<int:pk>/", views.UserUpdateView.as_view(), name="userinfo"),
    path("edit/", views.ProfileView.as_view(), name="editprofile"),
    path("dispatch-login/", views.DispatchLoginView.as_view(), name="dispatch_login"),
    path("member/", views.MemberUpdateView.as_view(), name="member"),
    path("admin/", views.AdminUpdateView.as_view(), name="admin"),
    path("403/", views.ForbiddenView.as_view(), name="403"),


    ]