from django.conf import settings

# The actual domain (e.g. "example.com") that this is hosted on
# FIDO2 will fail if this is not set correctly
DOMAIN = settings.MFA_DOMAIN

# Site title that is shown in authenticator apps
SITE_TITLE = settings.MFA_SITE_TITLE

# Available authentication methods in order of relevance
METHODS = getattr(settings, 'MFA_METHODS', ['FIDO2', 'TOTP', 'recovery'])

# `valid_window` parameter passed to PyOTP's verify method
# See https://pyauth.github.io/pyotp/#pyotp.totp.TOTP.verify
TOTP_VALID_WINDOW = getattr(settings, 'MFA_TOTP_VALID_WINDOW', 0)

# `user_verification` parameter passed to python-fido2
# See https://www.w3.org/TR/webauthn/#enum-userVerificationRequirement
FIDO2_USER_VERIFICATION = getattr(settings, 'MFA_FIDO2_USER_VERIFICATION', None)

# An account might end up having a large number of keys
# if it is shared by multiple users or if lost keys are not
# deleted. Both are potential security issues, so this is
# restricted to a reasonable (but small) number by default.
#
# This setting only applies when adding new keys.
# To allow an arbitrary number of keys, set this to `None`.
MAX_KEYS_PER_ACCOUNT = getattr(settings, 'MFA_MAX_KEYS_PER_ACCOUNT', 3)
