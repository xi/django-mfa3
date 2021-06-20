import pyotp
from django.conf import settings

name = 'TOTP'


def register_begin(user):
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    url = totp.provisioning_uri(
        user.username,
        issuer_name=settings.MFA_SITE_TITLE,
    )
    return {'url': url, 'secret': secret}, secret


def register_complete(state, request_data):
    totp = pyotp.TOTP(state)
    if not totp.verify(request_data):
        raise ValueError
    return state


def authenticate_begin(user):
    return None, None


def authenticate_complete(state, user, request_data):
    keys = user.mfakey_set.filter(method=name)
    for key in keys:
        totp = pyotp.TOTP(key.secret)
        if totp.verify(request_data):
            return
    raise ValueError