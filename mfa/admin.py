from django.contrib import admin
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse

from .models import MFAKey

original_login = admin.AdminSite.login


def custom_login(self, request, extra_context=None):
    next_url = (
        request.GET.get(REDIRECT_FIELD_NAME)
        or request.POST.get(REDIRECT_FIELD_NAME)
        or reverse('admin:index')
    )
    return redirect_to_login(next_url)


def patch_admin():
    setattr(admin.AdminSite, 'login', custom_login)


def unpatch_admin():
    setattr(admin.AdminSite, 'login', original_login)


@admin.register(MFAKey)
class MFAKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'method']
