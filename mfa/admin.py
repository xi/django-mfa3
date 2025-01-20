from django.contrib import admin
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse

from .decorators import login_not_required
from .models import MFAKey


@login_not_required
def custom_login(self, request, extra_context=None):
    next_url = (
        request.GET.get(REDIRECT_FIELD_NAME)
        or request.POST.get(REDIRECT_FIELD_NAME)
        or reverse('admin:index')
    )
    return redirect_to_login(next_url)


def patch_admin():
    setattr(admin.AdminSite, 'login', custom_login)


@admin.register(MFAKey)
class MFAKeyAdmin(admin.ModelAdmin):
    list_display = ['user', 'method', 'name']
    search_fields = ['user__username', 'name']
    list_filter = ['method']
