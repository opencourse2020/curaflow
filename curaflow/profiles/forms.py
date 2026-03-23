from django import forms
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.contrib.auth import get_user_model
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.models import Permission, Group
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from datetime import datetime
from allauth.account.forms import SignupForm, LoginForm, ResetPasswordForm
from . import models

User = get_user_model()

class MyResetPasswordForm(ResetPasswordForm):
    # email_address = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control form-control-lg bg-inverse bg-opacity-5'}))
    pass


class SignInForm(LoginForm):
    pass
#     captcha = ReCaptchaField()


class ProfileCreateForm(SignupForm):
    # USER_TYPES = [("parent", _("Parent")), ("student", _("Student")), ("professor", _("Professor")), ("institutadmin", _("Institute Admin")), ("serviceprovider", _("Service Provider"))]
    USER_TYPES = [("admin", _("Admin")), ("customer", _("Customer"))]
    # USER_TYPES = [("staff", _("Staff"))]
    # user_type = forms.ChoiceField(choices=USER_TYPES, widget=forms.Select(attrs={'class': 'form-select form-select-lg bg-inverse bg-opacity-5'}))
    user_type = forms.ChoiceField(choices=USER_TYPES)
    # captcha = ReCaptchaField()
    class Meta(auth_forms.UserCreationForm.Meta):
        model = User

    def save(self, request):
        with transaction.atomic():
            user = super().save(request)
            #***********************************************************************************************************
            #****************************************  Can be added in case we need more types of users ****************
            # ***********************************************************************************************************

            user_type = self.cleaned_data["user_type"]
            user_type_class_map = {
                "admin": models.Admin,
                "customer": models.Member           # Customer refers to Member
            }
            user_class = user_type_class_map[user_type]
            # ***********************************************************************************************************
            # ***********************************************************************************************************
            # ***********************************************************************************************************
            # user_type = "parent"
            # user_class = models.Parent
            profile = user_class()
            setattr(user, user_type, profile)
            user.is_staff = False
            if user_type == "admin":
                permissions = Permission.objects.filter(codename__startswith="manage")
                for perm in permissions:
                    user.user_permissions.add(perm)
                user.is_staff = True
            # elif user_type == "member":
            #     permissions = Permission.objects.filter(codename="view_newsletter_logiflex")
            #     user.user_permissions.add(permissions)

            permission = get_object_or_404(
                Permission, codename=f"access_{user_type}_pages"
            )
            user.user_permissions.add(permission)

            group_name = f"{user_type}s".capitalize()
            group, created = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
            # user.date_expire = expire

            user.save()
            profile.save()
            return user


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
        ]


class LanguageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["language"]
        labels = {
            "language": _("Prefered Language")
        }


class StaffForm(forms.ModelForm):
    class Meta:
        model = models.Admin
        fields = [
            "title",
            "location",
            "specialization",
            "bio",
            "license_number",
            "years_experience",
            "avatar",

        ]
        labels = {
            "title": _("Title"),
            "location": _("Location"),
            "specialization": _("Specialization"),
            "bio": _("Bio"),
            "license_number": _("License Number"),
            "years_experience": _("Years of Experience"),
            "avatar": _("Avatar")
        }


class StaffRulesForm(forms.ModelForm):
    class Meta:
        model = models.Admin
        fields = [
            "can_approve_programs",
            "can_edit_services",
            "can_manage_customers",
            "can_view_analytics",
            "is_available_for_assignment"
        ]
        labels = {
            "can_approve_programs": _("Can Approve Programs"),
            "can_edit_services": _("Can Edit Services"),
            "can_manage_customers": _("Can Manage Customers"),
            "can_view_analytics": _("Can View Analytics"),
            "is_available_for_assignment": _("Is Available For Assignment"),
        }


class MemberForm(forms.ModelForm):
    class Meta:
        model = models.Member
        fields = [
            "gender",
            "date_of_birth",
            "phone",
            "whatsapp",
        ]
        labels = {
            "gender": _("Gender"),
            "date_of_birth": _("Date of Birth"),
            "phone": _("Telephone"),
            "whatsapp": _("Whatsapp Number"),
            }

# class RegularForm(forms.ModelForm):
#     class Meta:
#         model = models.User
#         fields = [
#             "phone",
#             "email",
#             "",
#             "whatsapp",
#             "address",
#             # "picture",
#             "gender",
#             # "yearofbirth",
#
#         ]
#         labels = {
#             "tel": _("Telephone"),
#             "whatsapp": _("Whatsapp Number"),
#             "address": _("Address"),
#             "city": _("City"),
#             "country": _("Country"),
#             # "picture": _("Picture"),
#             "gender": _("Gender"),
#             # "yearofbirth": _("Year of Birth")
#         }


AdminFormSet = inlineformset_factory(
    User, models.Admin, form=SignupForm, exclude=[], extra=1, can_delete=False,
)

MemberFormSet = inlineformset_factory(
    User, models.Member, form=MemberForm, exclude=[], extra=1, can_delete=False,
)


