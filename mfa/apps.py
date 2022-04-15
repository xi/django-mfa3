from django.apps import AppConfig


class TwoFactorConfig(AppConfig):
    name = 'mfa'
    verbose_name = 'Multi Factor Authentication'

    def ready(self):
        from .admin import patch_admin
        patch_admin()
