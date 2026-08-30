from django.conf import settings
from django.db import models


class MFAKey(models.Model):
    id = models.BigAutoField(primary_key=True, serialize=False, verbose_name='ID')
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

    # rate limiting
    #
    # NOTE: this would better fit in the User model, but that is harder
    # to modify. Instead, we save the same value on all keys of a user.
    next_use_at = models.DateTimeField(blank=True, null=True)
