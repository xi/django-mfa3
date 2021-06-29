from django.contrib import admin

from .models import MFAKey


@admin.register(MFAKey)
class MFAKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'method']
