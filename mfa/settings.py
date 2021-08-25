from django.conf import settings

# The actual domain (e.g. "example.com") that this is hosted on
# FIDO2 will fail if this is not set correctly
DOMAIN = settings.MFA_DOMAIN

# Site title that is shown in authenticator apps
SITE_TITLE = settings.MFA_SITE_TITLE

# Available authentication methods in order of relevance
METHODS = getattr(settings, 'MFA_METHODS', ['FIDO2', 'TOTP', 'recovery'])
