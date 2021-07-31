from django.conf import settings
from django.db import models


class MFAKey(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    method = models.CharField(max_length=8, choices=[
        ('FIDO2', 'FIDO2'),
        ('TOTP', 'TOTP'),
        ('recovery', 'recovery'),
    ])
    name = models.CharField(max_length=32)
    secret = models.TextField()
    # replay protection
    last_code = models.CharField(max_length=32, blank=True)
